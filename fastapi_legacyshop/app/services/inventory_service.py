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
