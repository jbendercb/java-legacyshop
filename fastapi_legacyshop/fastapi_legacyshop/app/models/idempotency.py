from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=False)
    status_code = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IdempotencyRecord(key='{self.idempotency_key}', resource_type='{self.resource_type}')>"
