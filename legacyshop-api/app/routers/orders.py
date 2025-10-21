"""
Order management REST API endpoints.
Mirrors the Java OrderController implementation.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.schemas import OrderCreateRequest, OrderResponse, PaginatedOrderResponse
from app.services.order_service import order_service
from app.services.payment_service import payment_service
from app.services.exceptions import (
    BusinessValidationException,
    ResourceNotFoundException,
    PaymentException
)
from app.models.models import IdempotencyRecord

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
async def create_order(
    request: OrderCreateRequest,
    response: Response,
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Create order with idempotency support.
    POST /api/orders
    Header: Idempotency-Key: unique-key-per-request
    """
    if idempotency_key:
        existing_record = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.idempotency_key == idempotency_key
        ).first()
        
        if existing_record and existing_record.result_entity_id:
            response.status_code = status.HTTP_200_OK
            existing_order = order_service.get_order(existing_record.result_entity_id, db)
            return existing_order
    
    response.status_code = status.HTTP_201_CREATED
    order_response = order_service.create_order(request, idempotency_key, db)
    return order_response


@router.get("/{id}", response_model=OrderResponse)
async def get_order(id: int, db: Session = Depends(get_db)):
    """
    Get order by ID.
    GET /api/orders/{id}
    """
    return order_service.get_order(id, db)


@router.get("/customer/{email}", response_model=PaginatedOrderResponse)
async def get_customer_orders(
    email: str,
    page: int = 0,
    size: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get orders for customer with pagination.
    GET /api/orders/customer/{email}?page=0&size=10
    """
    return order_service.get_customer_orders(email, page, size, db)


@router.post("/{id}/authorize-payment")
async def authorize_payment(id: int, db: Session = Depends(get_db)):
    """
    Authorize payment for order.
    POST /api/orders/{id}/authorize-payment
    """
    await payment_service.authorize_payment(id, db)
    return {"status": "Payment authorized successfully"}


@router.post("/{id}/cancel", response_model=OrderResponse)
async def cancel_order(id: int, db: Session = Depends(get_db)):
    """
    Cancel order with compensating actions.
    POST /api/orders/{id}/cancel
    """
    return order_service.cancel_order(id, db)
