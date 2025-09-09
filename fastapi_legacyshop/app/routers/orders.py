from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.order import OrderCreateRequest, OrderResponse
from app.services.order_service import OrderService
from app.models.idempotency import IdempotencyRecord

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    order_request: OrderCreateRequest,
    db: Session = Depends(get_db),
    idempotency_key: str = Header(None, alias="Idempotency-Key")
):
    service = OrderService(db)
    if idempotency_key:
        existing_record = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.idempotency_key == idempotency_key
        ).first()
        if existing_record:
            result = await service.create_order(order_request, idempotency_key)
            return JSONResponse(status_code=200, content=result.model_dump(mode='json'))
    
    result = await service.create_order(order_request, idempotency_key)
    return result


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    return await service.get_order(order_id)


@router.get("/customer/{customer_email}", response_model=List[OrderResponse])
async def get_customer_orders(
    customer_email: str,
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    return await service.get_customer_orders(customer_email)


@router.post("/{order_id}/authorize-payment", status_code=200)
async def authorize_payment(
    order_id: int,
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    await service.authorize_payment(order_id)
    return {"message": "Payment authorization initiated"}


@router.post("/{order_id}/cancel", status_code=200)
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    await service.cancel_order(order_id)
    order = await service.get_order(order_id)
    return order
