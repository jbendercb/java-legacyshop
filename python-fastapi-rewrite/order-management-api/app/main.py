"""
FastAPI Order Management API
Replicates Java/Spring Boot Order Management functionality
"""
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, init_db
from app.schemas import (
    OrderCreateRequest, OrderResponse, PagedOrderResponse, ProblemDetail
)
from app.services import (
    OrderService, PaymentService,
    BusinessValidationException, ResourceNotFoundException, PaymentException
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    await init_db()
    yield


app = FastAPI(title="Order Management API", lifespan=lifespan)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.exception_handler(BusinessValidationException)
async def business_validation_exception_handler(request, exc: BusinessValidationException):
    """Handle business validation errors (400 Bad Request)"""
    problem = ProblemDetail(
        type="/problems/business-validation-error",
        title="Business Rule Violation",
        status=400,
        detail=str(exc)
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=problem.model_dump()
    )


@app.exception_handler(ResourceNotFoundException)
async def resource_not_found_exception_handler(request, exc: ResourceNotFoundException):
    """Handle resource not found errors (404 Not Found)"""
    problem = ProblemDetail(
        type="/problems/resource-not-found",
        title="Resource Not Found",
        status=404,
        detail=str(exc)
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=problem.model_dump()
    )


@app.exception_handler(PaymentException)
async def payment_exception_handler(request, exc: PaymentException):
    """Handle payment service errors (502 Bad Gateway or 400)"""
    http_status = status.HTTP_BAD_GATEWAY if exc.retryable else status.HTTP_BAD_REQUEST
    problem = ProblemDetail(
        type="/problems/payment-error",
        title="External Service Unavailable" if exc.retryable else "Payment Failed",
        status=http_status,
        detail=str(exc)
    )
    return JSONResponse(
        status_code=http_status,
        content=problem.model_dump()
    )


@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/api/admin/seed-test-data")
async def seed_test_data(db: AsyncSession = Depends(get_db)):
    """Seed test data for development/testing"""
    from app.models import Product
    from decimal import Decimal
    
    products = [
        Product(sku="LAPTOP-001", name="Gaming Laptop", price=Decimal("1200.00"), stock_quantity=10, active=True),
        Product(sku="MOUSE-001", name="Wireless Mouse", price=Decimal("25.00"), stock_quantity=50, active=True),
        Product(sku="KEYBOARD-001", name="Mechanical Keyboard", price=Decimal("75.00"), stock_quantity=30, active=True),
        Product(sku="MONITOR-001", name="4K Monitor", price=Decimal("400.00"), stock_quantity=20, active=True),
    ]
    
    db.add_all(products)
    await db.flush()
    
    return {"status": "success", "products_created": len(products)}


@app.post("/api/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Create order with idempotency support.
    POST /api/orders
    Header: Idempotency-Key: unique-key-per-request
    """
    if idempotency_key:
        from app.models import IdempotencyRecord
        from sqlalchemy import select
        
        result = await db.execute(
            select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == idempotency_key)
        )
        existing_record = result.scalar_one_or_none()
        
        if existing_record and existing_record.result_entity_id:
            existing_order = await OrderService.get_order(db, existing_record.result_entity_id)
            return OrderResponse.from_order(existing_order, existing_order.customer.email)
    
    order = await OrderService.create_order(db, request, idempotency_key)
    return OrderResponse.from_order(order, order.customer.email)


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get order by ID.
    GET /api/orders/{id}
    """
    order = await OrderService.get_order(db, order_id)
    return OrderResponse.from_order(order, order.customer.email)


@app.get("/api/orders/customer/{email}", response_model=PagedOrderResponse)
async def get_customer_orders(
    email: str,
    page: int = 0,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get orders for customer with pagination.
    GET /api/orders/customer/{email}?page=0&size=10
    """
    orders, total = await OrderService.get_customer_orders(db, email, page, size)
    
    total_pages = (total + size - 1) // size
    
    return PagedOrderResponse(
        content=[OrderResponse.from_order(order, order.customer.email) for order in orders],
        pageable={
            "page_number": page,
            "page_size": size,
            "sort": {"sorted": True, "by": "createdAt"}
        },
        total_elements=total,
        total_pages=total_pages,
        size=size,
        number=page,
        first=page == 0,
        last=page >= total_pages - 1
    )


@app.post("/api/orders/{order_id}/authorize-payment")
async def authorize_payment(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Authorize payment for order.
    POST /api/orders/{id}/authorize-payment
    """
    try:
        await PaymentService.authorize_payment(db, order_id)
        return {"status": "Payment authorized successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_BAD_GATEWAY,
            detail=f"Payment authorization failed: {str(e)}"
        )


@app.post("/api/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel order with compensating actions.
    POST /api/orders/{id}/cancel
    """
    order = await OrderService.cancel_order(db, order_id)
    return OrderResponse.from_order(order, order.customer.email)
