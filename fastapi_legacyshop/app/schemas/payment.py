from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.payment import PaymentStatus


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    status: PaymentStatus
    external_payment_id: Optional[str]
    retry_count: int
    last_error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
