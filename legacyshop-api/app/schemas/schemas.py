"""
Pydantic schemas for request/response validation.
Mirrors the Java DTO structure.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class OrderItemRequest(BaseModel):
    """Request schema for order item"""
    productSku: str = Field(..., min_length=1, description="Product SKU is required")
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")


class OrderCreateRequest(BaseModel):
    """Request schema for creating an order"""
    customerEmail: EmailStr = Field(..., description="Customer email is required")
    items: List[OrderItemRequest] = Field(..., min_length=1, description="Order must have at least one item")


class OrderItemResponse(BaseModel):
    """Response schema for order item"""
    id: int
    productSku: str
    productName: str
    quantity: int
    unitPrice: float
    subtotal: float
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Response schema for order"""
    id: int
    customerEmail: str
    status: str
    subtotal: float
    discountAmount: float
    total: float
    idempotencyKey: Optional[str] = None
    items: List[OrderItemResponse]
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True


class PaginatedOrderResponse(BaseModel):
    """Paginated response for orders"""
    content: List[OrderResponse]
    totalElements: int
    totalPages: int
    size: int
    number: int


class ProblemDetail(BaseModel):
    """RFC-7807 Problem Details for HTTP APIs"""
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
    fieldErrors: Optional[dict] = None
