from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from ..models.order import Order
from ..models.order_item import OrderItem
from ..models.customer import Customer

def get(db: Session, order_id: int) -> Order | None:
    return db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(Order.id == order_id).first()

def get_by_customer_email(db: Session, email: str) -> list[Order]:
    return (
        db.query(Order)
        .join(Customer, Customer.id == Order.customer_id)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Customer.email == email)
        .order_by(Order.id.desc())
        .all()
    )

def create(db: Session, order: Order) -> Order:
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
