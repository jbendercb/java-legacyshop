"""
SQLAlchemy database models for Order Management.
Mirrors the Java/Spring Boot entity structure.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    FAILED = "FAILED"
    VOIDED = "VOIDED"


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    order_items = relationship("OrderItem", back_populates="product")
    
    def decrement_stock(self, quantity: int):
        """Decrement stock quantity"""
        if self.stock_quantity < quantity:
            raise ValueError(f"Insufficient stock for {self.sku}")
        self.stock_quantity -= quantity
    
    def increment_stock(self, quantity: int):
        """Increment stock quantity (for cancellations)"""
        self.stock_quantity += quantity


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint('idempotency_key', name='uk_order_idempotency_key'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)
    subtotal = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, nullable=False, default=0)
    
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    
    def calculate_totals(self):
        """Calculate subtotal and total"""
        self.subtotal = sum(item.subtotal for item in self.items)
        self.total = round(self.subtotal - self.discount_amount, 2)
    
    def apply_discount(self, discount_amount: float):
        """Apply discount and recalculate total"""
        self.discount_amount = round(discount_amount, 2)
        self.calculate_totals()
    
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PAID]
    
    def cancel(self):
        """Cancel the order"""
        if not self.can_be_cancelled():
            raise ValueError(f"Order cannot be cancelled in status: {self.status}")
        self.status = OrderStatus.CANCELLED
    
    def mark_as_paid(self):
        """Mark order as paid"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Order must be PENDING to mark as PAID")
        self.status = OrderStatus.PAID


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_sku = Column(String(50), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    external_authorization_id = Column(String(255), nullable=True)
    retry_attempts = Column(Integer, nullable=False, default=0)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    order = relationship("Order", back_populates="payment")
    
    def authorize(self, authorization_id: str):
        """Mark payment as authorized"""
        self.status = PaymentStatus.AUTHORIZED
        self.external_authorization_id = authorization_id
    
    def fail(self, error_message: str):
        """Mark payment as failed"""
        self.status = PaymentStatus.FAILED
        self.error_message = error_message
    
    def void(self):
        """Void the payment"""
        if self.status != PaymentStatus.AUTHORIZED:
            raise ValueError("Can only void authorized payments")
        self.status = PaymentStatus.VOIDED
    
    def increment_retry_attempts(self):
        """Increment retry attempts counter"""
        self.retry_attempts += 1


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    
    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(100), unique=True, nullable=False, index=True)
    operation_type = Column(String(50), nullable=False)
    result_entity_id = Column(Integer, nullable=True)
    result_status = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    details = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
