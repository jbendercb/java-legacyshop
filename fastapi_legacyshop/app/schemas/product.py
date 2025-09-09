from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional

class ProductCreate(BaseModel):
    sku: str = Field(min_length=1)
    name: str
    description: Optional[str] = None
    price: Decimal
    stock_quantity: int = 0
    active: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    active: Optional[bool] = None

class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    price: Decimal
    stock_quantity: int
    active: bool

    class Config:
        from_attributes = True
