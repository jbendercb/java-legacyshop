"""
Order Management API - FastAPI Implementation
Rewrite of Java Spring Boot LegacyShop Order Management
Maintains 100% behavioral compatibility with enterprise patterns:
- Idempotency via Idempotency-Key header
- Retry logic with exponential backoff for payment service
- Compensating transactions (saga pattern)
- RFC-7807 Problem Details error responses
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import math

from app.models import (
    CreateOrderRequest, OrderResponse, PaginatedOrdersResponse,
    PaymentAuthorizationRequest, PaymentAuthorizationResponse,
    OrderCancellationResponse, OrderItemResponse, OrderStatus,
    ProblemDetails
)
from app.services import OrderService, create_problem_details
from app import database as db

app = FastAPI(title="Order Management API", version="1.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/api/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    request: CreateOrderRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Create a new order with idempotency support
    
    - **Idempotency-Key** header is required
    - Validates stock availability
    - Applies discount based on subtotal (5%/$50, 10%/$100, 15%/$200)
    - Atomically decrements stock
    - Returns 201 on success, 409 on duplicate key
    """
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail=create_problem_details(
                type_uri="https://example.com/probs/missing-idempotency-key",
                title="Missing Idempotency Key",
                status=400,
                detail="Idempotency-Key header is required for order creation",
                instance="/api/orders"
            ).dict()
        )
    
    order = OrderService.create_order(request, idempotency_key)
    
    return OrderResponse(
        order_id=order.id,
        customer_email=order.customer_email,
        status=order.status,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price
            )
            for item in order.items
        ],
        total_amount=order.total_amount,
        created_at=order.created_at
    )


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int):
    """
    Retrieve an order by ID
    
    - Returns 200 on success
    - Returns 404 if order not found
    """
    order = OrderService.get_order(order_id)
    
    return OrderResponse(
        order_id=order.id,
        customer_email=order.customer_email,
        status=order.status,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price
            )
            for item in order.items
        ],
        total_amount=order.total_amount,
        created_at=order.created_at
    )


@app.get("/api/orders/customer/{email}", response_model=PaginatedOrdersResponse)
async def get_customer_orders(email: str, page: int = 1, size: int = 10):
    """
    Get all orders for a customer with pagination
    
    - **email**: Customer email address
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10)
    - Returns paginated list of orders
    """
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail=create_problem_details(
                type_uri="https://example.com/probs/invalid-page",
                title="Invalid Page Number",
                status=400,
                detail="Page number must be >= 1",
                instance=f"/api/orders/customer/{email}"
            ).dict()
        )
    
    if size < 1 or size > 100:
        raise HTTPException(
            status_code=400,
            detail=create_problem_details(
                type_uri="https://example.com/probs/invalid-size",
                title="Invalid Page Size",
                status=400,
                detail="Page size must be between 1 and 100",
                instance=f"/api/orders/customer/{email}"
            ).dict()
        )
    
    orders, total_count = OrderService.get_customer_orders(email, page, size)
    
    total_pages = math.ceil(total_count / size) if total_count > 0 else 0
    
    return PaginatedOrdersResponse(
        orders=[
            OrderResponse(
                order_id=order.id,
                customer_email=order.customer_email,
                status=order.status,
                items=[
                    OrderItemResponse(
                        id=item.id,
                        product_id=item.product_id,
                        product_name=item.product_name,
                        quantity=item.quantity,
                        price=item.price
                    )
                    for item in order.items
                ],
                total_amount=order.total_amount,
                created_at=order.created_at
            )
            for order in orders
        ],
        page=page,
        size=size,
        total_pages=total_pages
    )


@app.post("/api/orders/{order_id}/authorize-payment", response_model=PaymentAuthorizationResponse)
async def authorize_payment(order_id: int, request: PaymentAuthorizationRequest):
    """
    Authorize payment for an order with retry logic
    
    - Retries up to 3 times with exponential backoff on HTTP 503
    - Validates payment amount matches order total
    - Returns 200 on success, 402 on payment failure, 503 if service unavailable
    """
    payment_id = await OrderService.authorize_payment(order_id, request)
    
    return PaymentAuthorizationResponse(
        order_id=order_id,
        status=OrderStatus.AUTHORIZED,
        payment_id=payment_id
    )


@app.post("/api/orders/{order_id}/cancel", response_model=OrderCancellationResponse)
async def cancel_order(order_id: int):
    """
    Cancel an order with compensating transactions
    
    - Restores stock for all items
    - Voids authorized payment if applicable
    - Updates order status to CANCELLED
    - Returns 200 on success, 409 if cannot cancel
    """
    await OrderService.cancel_order(order_id)
    
    return OrderCancellationResponse(
        order_id=order_id,
        status=OrderStatus.CANCELLED
    )



@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Ensure all HTTP exceptions return RFC-7807 format"""
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    problem = create_problem_details(
        type_uri="https://example.com/probs/http-error",
        title="HTTP Error",
        status=exc.status_code,
        detail=str(exc.detail),
        instance=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.dict()
    )
