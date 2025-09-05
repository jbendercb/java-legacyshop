from sqlalchemy.orm import Session, joinedload
from ..models.order import Order
from ..models.order_item import OrderItem

def get(db: Session, order_id: int) -> Order | None:
    return db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()

def create(db: Session, order: Order) -> Order:
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
