from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from ..models.order import Order
from ..models.order_item import OrderItem

def list_orders(db: Session, start: str | None, end: str | None, page: int, page_size: int):
    q = db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product))
    if start:
        q = q.filter(func.date(Order.created_at) >= start)
    if end:
        q = q.filter(func.date(Order.created_at) <= end)
    total = q.count()
    items = q.order_by(Order.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    def serialize(o: Order):
        return {
            "id": o.id,
            "status": o.status.value,
            "subtotal": str(o.subtotal),
            "discount": str(o.discount),
            "total": str(o.total),
            "items": [
                {
                    "productId": it.product_id,
                    "productSku": it.product.sku if it.product else None,
                    "quantity": it.quantity,
                    "unitPrice": str(it.unit_price),
                    "subtotal": str(it.subtotal),
                } for it in o.items
            ],
        }
    return {"total": total, "page": page, "pageSize": page_size, "orders": [serialize(o) for o in items]}
