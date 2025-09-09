from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
import uuid
import random

router = APIRouter()


class PaymentAuthRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    order_id: int
    card_number: str = Field(..., min_length=13, max_length=19)
    expiry_month: int = Field(..., ge=1, le=12)
    expiry_year: int = Field(..., ge=2024)
    cvv: str = Field(..., min_length=3, max_length=4)


class PaymentAuthResponse(BaseModel):
    payment_id: str
    status: str
    message: str


class PaymentVoidRequest(BaseModel):
    payment_id: str


@router.post("/authorize", response_model=PaymentAuthResponse)
async def authorize_payment(request: PaymentAuthRequest):
    if request.amount < Decimal("0.01"):
        raise HTTPException(status_code=400, detail="Amount must be at least 0.01")
    
    if request.amount > Decimal("1000.00"):
        raise HTTPException(status_code=402, detail="Insufficient funds")
    
    if random.random() < 0.1:
        raise HTTPException(status_code=500, detail="Payment service temporarily unavailable")
    
    if request.order_id == 999:
        raise HTTPException(status_code=502, detail="Payment gateway temporarily unavailable")
    
    if request.order_id == 888:
        raise HTTPException(status_code=400, detail="Invalid payment details")
    
    payment_id = str(uuid.uuid4())
    return PaymentAuthResponse(
        payment_id=payment_id,
        status="AUTHORIZED",
        message="Payment authorized successfully"
    )


@router.post("/void", status_code=200)
async def void_payment(request: PaymentVoidRequest):
    if not request.payment_id:
        raise HTTPException(status_code=400, detail="Payment ID is required")
    
    return {"message": f"Payment {request.payment_id} voided successfully"}
