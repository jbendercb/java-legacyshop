import httpx
from sqlalchemy.orm import Session
from decimal import Decimal
from ..config import settings
from ..models.payment import Payment, PaymentStatus
from ..models.order import Order, OrderStatus
from ..utils.money import quantize_2
from ..utils.problem_details import PaymentError

def authorize_payment(db: Session, order_id: int) -> dict:
    order = db.get(Order, order_id)
    if not order:
        from ..utils.problem_details import ResourceNotFoundError
        raise ResourceNotFoundError(f"Order {order_id} not found")
    amount = quantize_2(order.total)
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if not payment:
        payment = Payment(order_id=order.id, amount=amount, status=PaymentStatus.CREATED, retry_attempts=0)
        db.add(payment)
        db.commit()
        db.refresh(payment)
    url = settings.PAYMENTS_AUTH_URL
    payload = {"orderId": order.id, "amount": str(amount)}
    retry = False
    for attempt in range(2):
        try:
            with httpx.Client(timeout=settings.PAYMENTS_TIMEOUT_SECONDS) as client:
                resp = client.post(url, json=payload)
            if 200 <= resp.status_code < 300:
                data = resp.json()
                payment.status = PaymentStatus.AUTHORIZED
                payment.external_authorization_id = data.get("authId", "mock")
                order.status = OrderStatus.PAID
                db.commit()
                return {"status": "AUTHORIZED", "authId": payment.external_authorization_id}
            if 400 <= resp.status_code < 500:
                payment.status = PaymentStatus.FAILED
                db.commit()
                raise PaymentError("Payment authorization failed", retryable=False)
            if 500 <= resp.status_code < 600:
                payment.retry_attempts += 1
                db.commit()
                if retry:
                    raise PaymentError("Payment service unavailable", retryable=True)
                retry = True
                continue
            payment.status = PaymentStatus.FAILED
            db.commit()
            raise PaymentError("Unexpected payment response", retryable=True)
        except httpx.HTTPError:
            payment.retry_attempts += 1
            db.commit()
            if retry:
                raise PaymentError("Payment service unavailable", retryable=True)
            retry = True
            continue
    raise PaymentError("Payment service unavailable", retryable=True)
