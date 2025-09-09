from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, event
from sqlalchemy.orm import validates

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates('price')
    def validate_price(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Price must be non-negative")
        return value

    @validates('stock_quantity')
    def validate_stock_quantity(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Stock quantity must be non-negative")
        return value

    def decrement_stock(self, quantity: int) -> bool:
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            return True
        return False

    def increment_stock(self, quantity: int):
        self.stock_quantity += quantity

    def is_available(self) -> bool:
        return self.active and self.stock_quantity > 0

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"


@event.listens_for(Product, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
