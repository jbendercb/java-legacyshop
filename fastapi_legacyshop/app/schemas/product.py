from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50, description="Unique product SKU")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, max_length=1000, description="Product description")
    price: Decimal = Field(..., ge=0, description="Product price")
    stock_quantity: int = Field(..., ge=0, description="Initial stock quantity")
    active: bool = Field(True, description="Whether product is active")

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v

    @field_validator('stock_quantity')
    @classmethod
    def validate_stock_quantity(cls, v):
        if v < 0:
            raise ValueError('Stock quantity must be non-negative')
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Decimal] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price must be non-negative')
        return v

    @field_validator('stock_quantity')
    @classmethod
    def validate_stock_quantity(cls, v):
        if v is not None and v < 0:
            raise ValueError('Stock quantity must be non-negative')
        return v


class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    price: Decimal
    stock_quantity: int
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
