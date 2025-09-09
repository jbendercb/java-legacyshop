from sqlalchemy.orm import Session
from ..models.product import Product
from ..utils.problem_details import ResourceNotFoundError

def replenish_product(db: Session, product_id: int, quantity: int):
    prod = db.get(Product, product_id)
    if not prod:
        raise ResourceNotFoundError("Product not found")
    prod.stock_quantity += quantity
    db.commit()
    return {"productId": prod.id, "newStock": prod.stock_quantity}

from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.product import Product
from ..models.audit_log import AuditLog
from ..config import settings

def replenish_low_stock(db: Session) -> dict:
    threshold = settings.INVENTORY_LOW_STOCK_THRESHOLD
    amount = settings.INVENTORY_RESTOCK_QUANTITY
    products = db.execute(select(Product).where(Product.stock_quantity < threshold)).scalars().all()
    count = 0
    for p in products:
        p.stock_quantity += amount
        count += 1
        db.add(AuditLog(operation_type="INVENTORY_REPLENISHMENT", entity_id=str(p.id), entity_type="Product", details=f"+{amount}"))
    db.commit()
    return {"replenished": count}
