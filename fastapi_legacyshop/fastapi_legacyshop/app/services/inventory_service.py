from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.product import Product
from app.models.audit import AuditLog, OperationType
from app.config import settings
from app.exceptions import ProductNotFoundError


class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    async def replenish_inventory(self):
        try:
            page_size = 50
            page = 0
            
            while True:
                offset = page * page_size
                low_stock_products = (
                    self.db.query(Product)
                    .filter(
                        and_(
                            Product.active == True,
                            Product.stock_quantity <= settings.inventory.low_stock_threshold
                        )
                    )
                    .offset(offset)
                    .limit(page_size)
                    .all()
                )
                
                if not low_stock_products:
                    break
                
                for product in low_stock_products:
                    try:
                        old_quantity = product.stock_quantity
                        product.increment_stock(settings.inventory.default_restock_quantity)
                        
                        self._create_audit_log(
                            OperationType.INVENTORY_REPLENISHMENT,
                            "Product",
                            product.id,
                            f"Replenished from {old_quantity} to {product.stock_quantity}"
                        )
                        
                    except Exception as e:
                        self._create_audit_log(
                            OperationType.INVENTORY_REPLENISHMENT,
                            "Product", 
                            product.id,
                            f"Failed to replenish: {str(e)}"
                        )
                
                self.db.commit()
                page += 1
                
        except Exception as e:
            self.db.rollback()
            raise

    async def replenish_product(self, product_id: int, quantity: int):
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")

        try:
            old_quantity = product.stock_quantity
            product.increment_stock(quantity)
            self.db.commit()
            
            self._create_audit_log(
                OperationType.INVENTORY_REPLENISHMENT,
                "Product",
                product.id,
                f"Manual replenishment from {old_quantity} to {product.stock_quantity}"
            )
            
        except Exception as e:
            self.db.rollback()
            self._create_audit_log(
                OperationType.INVENTORY_REPLENISHMENT,
                "Product",
                product.id,
                f"Failed manual replenishment: {str(e)}"
            )
            raise

    async def get_low_stock_products(self) -> List[Product]:
        return (
            self.db.query(Product)
            .filter(
                and_(
                    Product.active == True,
                    Product.stock_quantity <= settings.inventory.low_stock_threshold
                )
            )
            .all()
        )

    def _create_audit_log(self, operation_type: OperationType, entity_type: str, entity_id: int, details: str):
        audit_log = AuditLog(
            operation_type=operation_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
        self.db.add(audit_log)
