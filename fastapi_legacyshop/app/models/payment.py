from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import enum
from ..db.base import Base

class PaymentStatus(str, enum.Enum):
    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    FAILED = "FAILED"
    VOIDED = "VOIDED"

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    amount: Mapped[Numeric] = mapped_column(Numeric(12, 2))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.CREATED)
    external_authorization_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retry_attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
