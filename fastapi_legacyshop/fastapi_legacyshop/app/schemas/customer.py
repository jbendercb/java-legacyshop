from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class CustomerCreate(BaseModel):
    email: EmailStr = Field(..., description="Customer email address")
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")


class CustomerResponse(BaseModel):
    id: int
    email: str
    name: str
    loyalty_points: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
