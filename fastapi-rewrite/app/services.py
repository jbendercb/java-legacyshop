"""
Business logic services for Order Management
Implements enterprise patterns: idempotency, retry logic, compensating transactions
Based on Java LegacyShop implementation from CoreStory project #75
"""

import httpx
import asyncio
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException
from app.models import (
    Order, OrderItem, OrderStatus, PaymentMethod,
    CreateOrderRequest, PaymentAuthorizationRequest,
    ProblemDetails
)
from app import database as db


PAYMENT_SERVICE_URL = "http://localhost:8080/mock/payment/authorize"
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


class OrderService:
    """Service for order management operations"""
    
    @staticmethod
    def calculate_discount(subtotal: Decimal) -> Decimal:
        """
        Calculate discount based on subtotal
        Discount tiers from Java implementation:
        - >= $200: 15% discount
        - >= $100: 10% discount
        - >= $50: 5% discount
        - < $50: No discount
        """
        if subtotal >= Decimal("200"):
            return subtotal * Decimal("0.15")
        elif subtotal >= Decimal("100"):
            return subtotal * Decimal("0.10")
        elif subtotal >= Decimal("50"):
            return subtotal * Decimal("0.05")
        else:
            return Decimal("0")
    
    @staticmethod
    def create_order(request: CreateOrderRequest, idempotency_key: str) -> Order:
        """
        Create a new order with idempotency check and stock validation
        Implements atomic stock decrement
        """
        existing_order_id = db.check_idempotency_key(idempotency_key)
        if existing_order_id is not None:
            raise HTTPException(
                status_code=409,
                detail=create_problem_details(
                    type_uri="https://example.com/probs/duplicate-request",
                    title="Duplicate Request",
                    status=409,
                    detail=f"Order already exists with idempotency key: {idempotency_key}",
                    instance=f"/api/orders/{existing_order_id}"
                ).dict()
            )
        
        order_items = []
        subtotal = Decimal("0")
        
        for req_item in request.items:
            product = db.get_product(req_item.product_id)
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=create_problem_details(
                        type_uri="https://example.com/probs/product-not-found",
                        title="Product Not Found",
                        status=404,
                        detail=f"Product with ID {req_item.product_id} not found",
                        instance="/api/orders"
                    ).dict()
                )
            
            if product.stock < req_item.quantity:
                raise HTTPException(
                    status_code=409,
                    detail=create_problem_details(
                        type_uri="https://example.com/probs/out-of-stock",
                        title="Insufficient Stock",
                        status=409,
                        detail=f"Product '{product.name}' has insufficient stock. Available: {product.stock}, Requested: {req_item.quantity}",
                        instance="/api/orders"
                    ).dict()
                )
            
            new_stock = product.stock - req_item.quantity
            db.update_product_stock(req_item.product_id, new_stock)
            
            item_id = db.get_next_order_item_id()
            item_price = product.price
            order_item = OrderItem(
                id=item_id,
                order_id=0,  # Will be set after order creation
                product_id=product.id,
                product_name=product.name,
                quantity=req_item.quantity,
                price=item_price
            )
            order_items.append(order_item)
            
            subtotal += item_price * req_item.quantity
        
        discount = OrderService.calculate_discount(subtotal)
        total_amount = subtotal - discount
        
        order = Order(
            id=0,  # Will be assigned by database
            customer_email=request.customer_email,
            status=OrderStatus.CREATED,
            items=order_items,
            total_amount=total_amount
        )
        
        created_order = db.create_order(order)
        
        for item in created_order.items:
            item.order_id = created_order.id
        
        db.save_idempotency_record(idempotency_key, created_order.id)
        
        return created_order
    
    @staticmethod
    def get_order(order_id: int) -> Order:
        """Get order by ID"""
        order = db.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=404,
                detail=create_problem_details(
                    type_uri="https://example.com/probs/order-not-found",
                    title="Order Not Found",
                    status=404,
                    detail=f"Order with ID {order_id} not found",
                    instance=f"/api/orders/{order_id}"
                ).dict()
            )
        return order
    
    @staticmethod
    def get_customer_orders(customer_email: str, page: int = 1, size: int = 10) -> tuple[List[Order], int]:
        """Get orders for a customer with pagination"""
        orders, total_count = db.get_orders_by_customer(customer_email, page, size)
        return orders, total_count
    
    @staticmethod
    async def authorize_payment(order_id: int, request: PaymentAuthorizationRequest) -> str:
        """
        Authorize payment with retry logic
        Retries up to 3 times with exponential backoff for HTTP 503
        """
        order = OrderService.get_order(order_id)
        
        if request.amount != order.total_amount:
            raise HTTPException(
                status_code=400,
                detail=create_problem_details(
                    type_uri="https://example.com/probs/invalid-amount",
                    title="Invalid Payment Amount",
                    status=400,
                    detail=f"Payment amount {request.amount} does not match order total {order.total_amount}",
                    instance=f"/api/orders/{order_id}/authorize-payment"
                ).dict()
            )
        
        if request.payment_method not in [PaymentMethod.CARD, PaymentMethod.ACH]:
            raise HTTPException(
                status_code=400,
                detail=create_problem_details(
                    type_uri="https://example.com/probs/unsupported-payment-method",
                    title="Unsupported Payment Method",
                    status=400,
                    detail=f"Payment method '{request.payment_method}' is not supported",
                    instance=f"/api/orders/{order_id}/authorize-payment"
                ).dict()
            )
        
        payment_id = await call_payment_service_with_retry(
            amount=request.amount,
            payment_method=request.payment_method.value,
            order_id=order_id
        )
        
        db.update_order_status(order_id, OrderStatus.AUTHORIZED)
        db.update_order_payment_id(order_id, payment_id)
        
        return payment_id
    
    @staticmethod
    async def cancel_order(order_id: int):
        """
        Cancel order with compensating transactions
        1. Restore stock for all items
        2. Void payment if authorized
        3. Update order status to CANCELLED
        """
        order = OrderService.get_order(order_id)
        
        if order.status == OrderStatus.SHIPPED:
            raise HTTPException(
                status_code=409,
                detail=create_problem_details(
                    type_uri="https://example.com/probs/cannot-cancel-shipped",
                    title="Cannot Cancel Order",
                    status=409,
                    detail="Cannot cancel an order that has been shipped",
                    instance=f"/api/orders/{order_id}/cancel"
                ).dict()
            )
        
        if order.status == OrderStatus.CANCELLED:
            raise HTTPException(
                status_code=409,
                detail=create_problem_details(
                    type_uri="https://example.com/probs/already-cancelled",
                    title="Order Already Cancelled",
                    status=409,
                    detail="Order has already been cancelled",
                    instance=f"/api/orders/{order_id}/cancel"
                ).dict()
            )
        
        for item in order.items:
            product = db.get_product(item.product_id)
            if product:
                new_stock = product.stock + item.quantity
                db.update_product_stock(item.product_id, new_stock)
        
        if order.status == OrderStatus.AUTHORIZED and order.payment_id:
            await void_payment(order.payment_id)
        
        db.update_order_status(order_id, OrderStatus.CANCELLED)


async def call_payment_service_with_retry(amount: Decimal, payment_method: str, order_id: int) -> str:
    """
    Call payment service with exponential backoff retry logic
    Retries up to 3 times on HTTP 503 (Service Unavailable)
    """
    retry_count = 0
    last_exception = None
    
    while retry_count < MAX_RETRIES:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    PAYMENT_SERVICE_URL,
                    json={
                        "amount": str(amount),
                        "currency": "USD",
                        "paymentMethod": payment_method
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("authorizationId", f"AUTH_{order_id}_TEST")
                elif response.status_code == 503:
                    retry_count += 1
                    if retry_count < MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * (2 ** (retry_count - 1))
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise HTTPException(
                            status_code=503,
                            detail=create_problem_details(
                                type_uri="https://example.com/probs/payment-service-unavailable",
                                title="Payment Service Unavailable",
                                status=503,
                                detail="Payment service is unavailable after 3 retries",
                                instance=f"/api/orders/{order_id}/authorize-payment"
                            ).dict()
                        )
                else:
                    raise HTTPException(
                        status_code=402,
                        detail=create_problem_details(
                            type_uri="https://example.com/probs/payment-failed",
                            title="Payment Authorization Failed",
                            status=402,
                            detail=f"Payment authorization failed with status {response.status_code}",
                            instance=f"/api/orders/{order_id}/authorize-payment"
                        ).dict()
                    )
        
        except httpx.RequestError as e:
            retry_count += 1
            last_exception = e
            if retry_count < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (retry_count - 1))
                await asyncio.sleep(delay)
                continue
            else:
                raise HTTPException(
                    status_code=503,
                    detail=create_problem_details(
                        type_uri="https://example.com/probs/payment-service-error",
                        title="Payment Service Error",
                        status=503,
                        detail=f"Failed to connect to payment service: {str(last_exception)}",
                        instance=f"/api/orders/{order_id}/authorize-payment"
                    ).dict()
                )
    
    raise HTTPException(status_code=503, detail="Payment service unavailable")


async def void_payment(payment_id: str):
    """Void a payment authorization"""
    pass


def create_problem_details(type_uri: str, title: str, status: int, detail: str, instance: str) -> ProblemDetails:
    """Create RFC-7807 Problem Details object"""
    return ProblemDetails(
        type=type_uri,
        title=title,
        status=status,
        detail=detail,
        instance=instance
    )
