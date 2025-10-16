"""
Pydantic schemas for API request/response validation.
Replicates Java DTOs for compatibility.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import OrderStatus, PaymentStatus


class OrderItemRequest(BaseModel):
    """Request schema for order item"""
    product_sku: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)


class OrderCreateRequest(BaseModel):
    """Request schema for creating an order"""
    customer_email: EmailStr
    items: List[OrderItemRequest] = Field(..., min_items=1)


class OrderItemResponse(BaseModel):
    """Response schema for order item"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class PaymentResponse(BaseModel):
    """Response schema for payment"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: PaymentStatus
    amount: Decimal
    external_authorization_id: Optional[str] = None
    retry_attempts: int
    error_message: Optional[str] = None


class OrderResponse(BaseModel):
    """Response schema for order"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    customer_email: str
    status: OrderStatus
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    items: List[OrderItemResponse]
    payment: Optional[PaymentResponse] = None
    created_at: datetime
    
    @classmethod
    def from_order(cls, order, customer_email: str):
        """Create response from order entity"""
        return cls(
            id=order.id,
            customer_email=customer_email,
            status=order.status,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            total=order.total,
            items=[OrderItemResponse.model_validate(item) for item in order.items],
            payment=PaymentResponse.model_validate(order.payment) if order.payment else None,
            created_at=order.created_at
        )


class ProblemDetail(BaseModel):
    """RFC-7807 Problem Details response"""
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    page: int
    size: int
    total_elements: int
    total_pages: int


class PagedOrderResponse(BaseModel):
    """Paged order response"""
    content: List[OrderResponse]
    pageable: dict
    total_elements: int
    total_pages: int
    size: int
    number: int
    first: bool
    last: bool
