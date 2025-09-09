from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter()


class PaymentAuthRequest(BaseModel):
    amount: float
    order_id: int


class PaymentAuthResponse(BaseModel):
    payment_id: str
    status: str
    message: str


class PaymentVoidRequest(BaseModel):
    payment_id: str


@router.post("/authorize", response_model=PaymentAuthResponse)
async def authorize_payment(request: PaymentAuthRequest):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
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
