from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal
from ..models.order import Order, OrderStatus
from ..models.customer import Customer
from ..models.idempotency import IdempotencyRecord
from ..config import settings

def process_loyalty(db: Session) -> dict:
    orders = db.execute(select(Order).where(Order.status == OrderStatus.PAID)).scalars().all()
    added = 0
    for o in orders:
        key = f"LOYALTY_{o.id}"
        if db.get(IdempotencyRecord, key):
            continue
        points = int((Decimal(str(o.total)) // Decimal("10")))
        points = min(points, settings.LOYALTY_MAX_POINTS)
        cust = db.get(Customer, o.customer_id)
        if not cust:
            continue
        cust.loyalty_points += points
        db.add(IdempotencyRecord(key=key, request_hash="", response_body="{}", status_code=200, operation_type="LOYALTY"))
        added += points
    db.commit()
    return {"awardedPoints": added}
