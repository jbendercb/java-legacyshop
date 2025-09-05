from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal

class OrderItemIn(BaseModel):
    productSku: str = Field(min_length=1)
    quantity: int = Field(gt=0)

class OrderCreate(BaseModel):
    customerEmail: str
    items: List[OrderItemIn]

class OrderItemOut(BaseModel):
    productId: int
    productSku: str
    quantity: int
    unitPrice: Decimal
    subtotal: Decimal

class OrderOut(BaseModel):
    id: int
    status: str
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    items: List[OrderItemOut]

    class Config:
        from_attributes = True
