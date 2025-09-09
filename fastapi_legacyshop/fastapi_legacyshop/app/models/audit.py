from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum

from app.database import Base


class OperationType(str, Enum):
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    PAYMENT_AUTHORIZED = "PAYMENT_AUTHORIZED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_VOIDED = "PAYMENT_VOIDED"
    INVENTORY_REPLENISHMENT = "INVENTORY_REPLENISHMENT"
    LOYALTY_POINTS_AWARDED = "LOYALTY_POINTS_AWARDED"
    STOCK_DECREMENTED = "STOCK_DECREMENTED"
    STOCK_INCREMENTED = "STOCK_INCREMENTED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(SQLEnum(OperationType), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, operation='{self.operation_type}', entity_type='{self.entity_type}')>"
