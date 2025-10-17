"""
Data models for Order Management system
Based on Java LegacyShop entities from CoreStory project #75
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration"""
    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    CANCELLED = "CANCELLED"
    SHIPPED = "SHIPPED"


class PaymentMethod(str, Enum):
    """Supported payment methods"""
    CARD = "CARD"
    ACH = "ACH"



class OrderItemRequest(BaseModel):
    """Order item in create order request"""
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity must be positive")


class CreateOrderRequest(BaseModel):
    """Request model for creating an order"""
    customer_email: EmailStr = Field(..., description="Customer email address")
    items: List[OrderItemRequest] = Field(..., min_items=1, description="Order items")


class OrderItemResponse(BaseModel):
    """Order item in responses"""
    id: int
    product_id: int
    product_name: str
    quantity: int
    price: Decimal
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response model"""
    order_id: int
    customer_email: str
    status: OrderStatus
    items: List[OrderItemResponse]
    total_amount: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaginatedOrdersResponse(BaseModel):
    """Paginated orders response"""
    orders: List[OrderResponse]
    page: int
    size: int
    total_pages: int


class PaymentAuthorizationRequest(BaseModel):
    """Request for payment authorization"""
    payment_method: PaymentMethod
    amount: Decimal = Field(..., gt=0)


class PaymentAuthorizationResponse(BaseModel):
    """Response from payment authorization"""
    order_id: int
    status: OrderStatus
    payment_id: str


class OrderCancellationResponse(BaseModel):
    """Response from order cancellation"""
    order_id: int
    status: OrderStatus



class Product:
    """Product domain model"""
    def __init__(self, id: int, name: str, price: Decimal, stock: int):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock


class OrderItem:
    """Order item domain model"""
    def __init__(self, id: int, order_id: int, product_id: int, product_name: str, quantity: int, price: Decimal):
        self.id = id
        self.order_id = order_id
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.price = price


class Order:
    """Order domain model"""
    def __init__(self, id: int, customer_email: str, status: OrderStatus, items: List[OrderItem], total_amount: Decimal):
        self.id = id
        self.customer_email = customer_email
        self.status = status
        self.items = items
        self.total_amount = total_amount
        self.created_at = datetime.utcnow()
        self.payment_id: Optional[str] = None


class IdempotencyRecord:
    """Idempotency record domain model"""
    def __init__(self, idempotency_key: str, order_id: int):
        self.idempotency_key = idempotency_key
        self.order_id = order_id
        self.created_at = datetime.utcnow()



class ProblemDetails(BaseModel):
    """RFC-7807 Problem Details for HTTP API error responses"""
    type: str = Field(..., description="URI reference that identifies the problem type")
    title: str = Field(..., description="Short, human-readable summary")
    status: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Human-readable explanation")
    instance: str = Field(..., description="URI reference to the specific occurrence")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "https://example.com/probs/out-of-stock",
                "title": "Insufficient Stock",
                "status": 409,
                "detail": "The product 'Widget A' has insufficient stock",
                "instance": "/api/orders/123"
            }
        }
