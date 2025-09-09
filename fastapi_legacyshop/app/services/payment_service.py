from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, RetryError
from sqlalchemy.orm import Session

from app.models.order import OrderEntity, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.audit import AuditLog, OperationType
from app.config import settings
from app.exceptions import PaymentError, PaymentGatewayError


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    async def authorize_payment(self, order_id: int, amount, card_number: str, expiry_month: int, expiry_year: int, cvv: str):
        payment = Payment(
            order_id=order_id,
            amount=amount,
            status=PaymentStatus.PENDING
        )
        self.db.add(payment)
        self.db.flush()

        try:
            result = await self._authorize_with_retry(payment, card_number, expiry_month, expiry_year, cvv)
            
            payment.external_payment_id = result.get("transaction_id")
            payment.status = PaymentStatus.AUTHORIZED
            
            self.db.commit()
            
            self._create_audit_log(OperationType.PAYMENT_AUTHORIZED, "Payment", payment.id,
                                 f"Payment authorized for order {order_id}, external ID: {payment.external_payment_id}")
            
            return payment

        except PaymentGatewayError as e:
            payment.status = PaymentStatus.FAILED
            payment.last_error_message = str(e)
            self.db.commit()
            
            self._create_audit_log(OperationType.PAYMENT_FAILED, "Payment", payment.id,
                                 f"Payment failed for order {order_id}: {str(e)}")
            raise
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.last_error_message = str(e)
            self.db.commit()
            
            self._create_audit_log(OperationType.PAYMENT_FAILED, "Payment", payment.id,
                                 f"Payment failed for order {order_id}: {str(e)}")
            
            if hasattr(e, 'last_attempt') and hasattr(e.last_attempt, 'exception'):
                original_exception = e.last_attempt.exception()
                if isinstance(original_exception, PaymentGatewayError):
                    raise original_exception
            raise

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(PaymentGatewayError)
    )
    async def _authorize_with_retry(self, payment: Payment, card_number: str, expiry_month: int, expiry_year: int, cvv: str) -> dict:
        payment.increment_retry_count()
        
        async with httpx.AsyncClient(timeout=settings.payments.timeout_seconds) as client:
            try:
                response = await client.post(
                    settings.payments.auth_url,
                    json={
                        "amount": float(payment.amount),
                        "order_id": payment.order_id,
                        "card_number": card_number,
                        "expiry_month": expiry_month,
                        "expiry_year": expiry_year,
                        "cvv": cvv
                    }
                )
                
                if response.status_code >= 500:
                    try:
                        error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"message": response.text}
                        error_message = error_data.get("message", f"Payment gateway error: {response.status_code}")
                    except:
                        error_message = f"Payment gateway error: {response.status_code}"
                    raise PaymentGatewayError(error_message)
                elif response.status_code >= 400:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"message": response.text}
                    error_message = error_data.get("message", response.text)
                    raise PaymentError(f"Payment validation error: {error_message}")
                
                return response.json()
                
            except httpx.TimeoutException:
                raise PaymentGatewayError("Payment gateway timeout")
            except httpx.RequestError as e:
                raise PaymentGatewayError(f"Payment gateway connection error: {str(e)}")

    async def void_payment(self, payment: Payment):
        if not payment.external_payment_id:
            return

        try:
            async with httpx.AsyncClient(timeout=settings.payments.timeout_seconds) as client:
                response = await client.post(
                    f"{settings.payments.auth_url.replace('/authorize', '/void')}",
                    json={"payment_id": payment.external_payment_id}
                )
                
                if response.status_code == 200:
                    payment.status = PaymentStatus.VOIDED
                    self.db.commit()
                    
                    self._create_audit_log(OperationType.PAYMENT_VOIDED, "Payment", payment.id,
                                         f"Payment voided: {payment.external_payment_id}")

        except Exception as e:
            self._create_audit_log(OperationType.PAYMENT_FAILED, "Payment", payment.id,
                                 f"Failed to void payment {payment.external_payment_id}: {str(e)}")

    def _create_audit_log(self, operation_type: OperationType, entity_type: str, entity_id: int, details: str):
        audit_log = AuditLog(
            operation_type=operation_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
        self.db.add(audit_log)
