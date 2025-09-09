from decimal import Decimal
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, validates

from app.database import Base


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class OrderEntity(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    total = Column(Numeric(10, 2), nullable=False)
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)

    @validates('subtotal', 'discount_amount', 'total')
    def validate_amounts(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value

    def calculate_totals(self):
        self.subtotal = sum(item.subtotal for item in self.items)
        self.total = self.subtotal - self.discount_amount

    def can_be_cancelled(self) -> bool:
        return self.status in [OrderStatus.PENDING, OrderStatus.PAID]

    def __repr__(self):
        return f"<OrderEntity(id={self.id}, status='{self.status}', total={self.total})>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    order = relationship("OrderEntity", back_populates="items")
    product = relationship("Product")

    @validates('unit_price', 'subtotal')
    def validate_amounts(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value

    @validates('quantity')
    def validate_quantity(self, key, value):
        if value is not None and value <= 0:
            raise ValueError("Quantity must be positive")
        return value

    def calculate_subtotal(self):
        self.subtotal = self.unit_price * self.quantity

    def __repr__(self):
        return f"<OrderItem(id={self.id}, sku='{self.sku}', quantity={self.quantity})>"
