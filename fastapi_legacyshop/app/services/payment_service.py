import httpx
from sqlalchemy.orm import Session
from ..config import settings
from ..models.payment import Payment, PaymentStatus
from ..models.order import Order, OrderStatus
from ..utils.money import quantize_2
from ..utils.problem_details import PaymentError

def _simulate_authorize(amount_str: str):
    from ..routers.dev_inject import pop_next_failure
    nxt = pop_next_failure()
    if nxt:
        return {"status_code": nxt, "body": {"error": "Payment service temporarily unavailable"}}
    try:
        amount = float(str(amount_str))
    except Exception:
        amount = 0.0
    if amount < 0.01:
        return {"status_code": 400, "body": {"error": "Amount must be at least 0.01"}}
    if amount > 1000:
        return {"status_code": 402, "body": {"error": "Insufficient funds"}}
    from uuid import uuid4
    return {"status_code": 200, "body": {"authorizationId": "AUTH_" + uuid4().hex, "status": "AUTHORIZED", "amount": f"{amount:.2f}"}}

def _simulate_void(auth_id: str):
    from ..routers.dev_inject import pop_next_failure
    nxt = pop_next_failure()
    if nxt:
        return {"status_code": nxt, "body": {"error": "Void service temporarily unavailable"}}
    if not auth_id:
        return {"status_code": 400, "body": {"error": "Authorization ID is required"}}
    return {"status_code": 200, "body": {"authorizationId": auth_id, "status": "VOIDED"}}

def _http_post(url: str, json_payload: dict):
    with httpx.Client(timeout=settings.PAYMENTS_TIMEOUT_SECONDS) as client:
        return client.post(url, json=json_payload)

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
    for _ in range(2):
        if settings.APP_ENV == "test":
            result = _simulate_authorize(payload["amount"])
            status_code = result["status_code"]
            data = result["body"]
        else:
            try:
                resp = _http_post(url, payload)
                status_code = resp.status_code
                data = resp.json() if 200 <= resp.status_code < 600 else {}
            except httpx.HTTPError:
                payment.retry_attempts += 1
                db.commit()
                if retry:
                    raise PaymentError("Payment service unavailable", retryable=True)
                retry = True
                continue
        if 200 <= status_code < 300:
            payment.status = PaymentStatus.AUTHORIZED
            payment.external_authorization_id = data.get("authorizationId") or data.get("authId") or "mock"
            order.status = OrderStatus.PAID
            db.commit()
            return {"status": "AUTHORIZED", "authorizationId": payment.external_authorization_id}
        if 400 <= status_code < 500:
            payment.status = PaymentStatus.FAILED
            db.commit()
            raise PaymentError("Payment authorization failed", retryable=False)
        if 500 <= status_code < 600:
            payment.retry_attempts += 1
            db.commit()
            if retry:
                raise PaymentError("Payment service unavailable", retryable=True)
            retry = True
            continue
        payment.status = PaymentStatus.FAILED
        db.commit()
        raise PaymentError("Unexpected payment response", retryable=True)
    raise PaymentError("Payment service unavailable", retryable=True)

def void_authorization(authorization_id: str) -> None:
    if settings.APP_ENV == "test":
        _simulate_void(authorization_id)
        return
    try:
        _http_post(settings.PAYMENTS_AUTH_URL.replace("/authorize", "/void"), {"authorizationId": authorization_id})
    except httpx.HTTPError:
        return
