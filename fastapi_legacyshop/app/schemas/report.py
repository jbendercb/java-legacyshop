from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.order import OrderStatus
from app.models.payment import PaymentStatus


class OrderReportResponse(BaseModel):
    order_id: int
    customer_email: str
    customer_name: str
    order_status: OrderStatus
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    payment_status: Optional[PaymentStatus]
    external_payment_id: Optional[str]
    order_created_at: datetime

    class Config:
        from_attributes = True
