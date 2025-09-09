from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    loyalty_points = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("OrderEntity", back_populates="customer")

    def add_loyalty_points(self, points: Decimal, max_points: int = 500):
        new_total = self.loyalty_points + points
        self.loyalty_points = min(new_total, Decimal(str(max_points)))

    def __repr__(self):
        return f"<Customer(id={self.id}, email='{self.email}', name='{self.name}')>"
