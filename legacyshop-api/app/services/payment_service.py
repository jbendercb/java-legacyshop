"""
Payment service with retry logic and external service integration.
Implements retry logic matching the Java @Retryable annotation.
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.models import Order, Payment, PaymentStatus
from app.config.business_config import config
from app.services.exceptions import PaymentException, ResourceNotFoundException


class PaymentService:
    """Service for payment processing with retry logic"""
    
    @retry(
        stop=stop_after_attempt(config.payment_max_attempts),
        wait=wait_fixed(config.payment_backoff_seconds),
        retry=retry_if_exception_type(PaymentException),
        reraise=True
    )
    async def authorize_payment(self, order_id: int, db: Session) -> Payment:
        """
        Authorize payment with retry logic on 5xx errors.
        Maps 4xx errors to domain exceptions.
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ResourceNotFoundException(f"Order not found with id: {order_id}")
        
        existing_payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        if existing_payment:
            if existing_payment.status == PaymentStatus.AUTHORIZED:
                return existing_payment
            elif existing_payment.status == PaymentStatus.PENDING:
                payment = existing_payment
            else:
                payment = Payment(
                    order_id=order.id,
                    amount=order.total,
                    status=PaymentStatus.PENDING
                )
                db.add(payment)
                db.commit()
                db.refresh(payment)
        else:
            payment = Payment(
                order_id=order.id,
                amount=order.total,
                status=PaymentStatus.PENDING
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
        
        try:
            authorization_id = await self._call_external_payment_service(order.total)
            
            payment.authorize(authorization_id)
            db.commit()
            
            order.mark_as_paid()
            db.commit()
            
            return payment
            
        except httpx.HTTPStatusError as e:
            payment.increment_retry_attempts()
            
            if 400 <= e.response.status_code < 500:
                error_message = f"Payment authorization failed: {e.response.text}"
                payment.fail(error_message)
                db.commit()
                raise PaymentException(error_message, retryable=False)
            
            elif 500 <= e.response.status_code < 600:
                error_message = "Payment service temporarily unavailable"
                payment.fail(error_message)
                db.commit()
                raise PaymentException(error_message, retryable=True)
            
            else:
                error_message = f"Unexpected payment error: {e.response.status_code}"
                payment.fail(error_message)
                db.commit()
                raise PaymentException(error_message, retryable=False)
                
        except Exception as e:
            payment.increment_retry_attempts()
            error_message = f"Payment authorization failed: {str(e)}"
            payment.fail(error_message)
            db.commit()
            raise PaymentException(error_message, retryable=True)
    
    async def _call_external_payment_service(self, amount: float) -> str:
        """
        Call external payment authorization service.
        This demonstrates the integration point that could fail with 4xx/5xx.
        """
        async with httpx.AsyncClient(timeout=config.payment_timeout_seconds) as client:
            request_data = {
                "amount": str(amount),
                "currency": "USD",
                "paymentMethod": "CARD"
            }
            
            response = await client.post(
                config.payment_auth_url,
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            if "authorizationId" in data:
                return data["authorizationId"]
            else:
                raise PaymentException("Invalid response from payment service", retryable=False)
    
    def void_payment(self, payment_id: int, db: Session):
        """
        Void payment (compensation action for order cancellation).
        """
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ResourceNotFoundException(f"Payment not found with id: {payment_id}")
        
        if payment.status != PaymentStatus.AUTHORIZED:
            raise ValueError("Can only void authorized payments")
        
        try:
            payment.void()
            db.commit()
        except Exception as e:
            raise PaymentException(f"Failed to void payment: {str(e)}", retryable=False)


payment_service = PaymentService()
