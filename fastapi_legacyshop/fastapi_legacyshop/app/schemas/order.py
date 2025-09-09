from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime

from app.models.order import OrderStatus


class OrderItemRequest(BaseModel):
    product_id: int = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity to order")

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class OrderCreateRequest(BaseModel):
    customer_email: EmailStr = Field(..., description="Customer email address")
    items: List[OrderItemRequest] = Field(..., min_length=1, description="Order items")

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError('Order must contain at least one item')
        return v


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_sku: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    customer_email: str
    customer_name: str
    status: OrderStatus
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    idempotency_key: Optional[str]
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_order_entity(cls, order):
        items = []
        for item in order.items:
            items.append(OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.name,
                product_sku=item.sku,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.subtotal
            ))
        
        return cls(
            id=order.id,
            customer_email=order.customer.email,
            customer_name=order.customer.name,
            status=order.status,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            total=order.total,
            idempotency_key=order.idempotency_key,
            items=items,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
