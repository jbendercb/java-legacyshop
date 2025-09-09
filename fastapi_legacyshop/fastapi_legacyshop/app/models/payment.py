from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    FAILED = "FAILED"
    VOIDED = "VOIDED"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    external_payment_id = Column(String(255), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("OrderEntity", back_populates="payment")

    def increment_retry_count(self):
        self.retry_count += 1

    def is_retryable(self, max_retries: int = 1) -> bool:
        return self.retry_count < max_retries and self.status == PaymentStatus.PENDING

    def __repr__(self):
        return f"<Payment(id={self.id}, order_id={self.order_id}, status='{self.status}')>"
