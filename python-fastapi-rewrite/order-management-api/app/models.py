"""
Database models for Order Management API.
Replicates the Java/Spring Boot entity structure for compatibility.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    Index,
    UniqueConstraint
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models"""
    pass


class OrderStatus(str, PyEnum):
    """Order status enum matching Java implementation"""
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, PyEnum):
    """Payment status enum matching Java implementation"""
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    FAILED = "FAILED"
    VOIDED = "VOIDED"


class Product(Base):
    """Product entity"""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def decrement_stock(self, quantity: int):
        """Decrement stock atomically"""
        if self.stock_quantity < quantity:
            raise ValueError(f"Insufficient stock for product {self.sku}")
        self.stock_quantity -= quantity

    def increment_stock(self, quantity: int):
        """Increment stock (compensation action)"""
        self.stock_quantity += quantity


class Customer(Base):
    """Customer entity"""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    loyalty_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    orders: Mapped[List["OrderEntity"]] = relationship("OrderEntity", back_populates="customer")


class OrderEntity(Base):
    """Order entity"""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    customer: Mapped[Customer] = relationship("Customer", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="order", uselist=False)

    def calculate_totals(self):
        """Calculate order totals from items"""
        self.subtotal = sum((item.subtotal for item in self.items), Decimal("0.00"))

    def apply_discount(self, discount_amount: Decimal):
        """Apply discount and recalculate total"""
        self.discount_amount = discount_amount
        self.total = self.subtotal - self.discount_amount

    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PAID]

    def cancel(self):
        """Cancel order"""
        self.status = OrderStatus.CANCELLED

    def mark_as_paid(self):
        """Mark order as paid"""
        self.status = OrderStatus.PAID


class OrderItem(Base):
    """Order item entity"""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    order: Mapped[OrderEntity] = relationship("OrderEntity", back_populates="items")
    product: Mapped[Product] = relationship("Product")


class Payment(Base):
    """Payment entity"""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    external_authorization_id: Mapped[Optional[str]] = mapped_column(String(255))
    retry_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    order: Mapped[OrderEntity] = relationship("OrderEntity", back_populates="payment")

    def authorize(self, authorization_id: str):
        """Mark payment as authorized"""
        self.status = PaymentStatus.AUTHORIZED
        self.external_authorization_id = authorization_id
        self.error_message = None

    def fail(self, error_message: str):
        """Mark payment as failed"""
        self.status = PaymentStatus.FAILED
        self.error_message = error_message

    def void_payment(self):
        """Void payment (compensation action)"""
        self.status = PaymentStatus.VOIDED

    def increment_retry_attempts(self):
        """Increment retry attempts"""
        self.retry_attempts += 1


class IdempotencyRecord(Base):
    """Idempotency record entity"""
    __tablename__ = "idempotency_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    result_entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    result_data: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class AuditLog(Base):
    """Audit log entity"""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(String(1000))
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def order_created_log(order_id: int, customer_email: str) -> "AuditLog":
        """Create audit log for order creation"""
        return AuditLog(
            operation="CREATE",
            entity_type="ORDER",
            entity_id=order_id,
            details=f"Order created for customer {customer_email}"
        )

    @staticmethod
    def order_cancelled_log(order_id: int, reason: str) -> "AuditLog":
        """Create audit log for order cancellation"""
        return AuditLog(
            operation="CANCEL",
            entity_type="ORDER",
            entity_id=order_id,
            details=reason
        )
