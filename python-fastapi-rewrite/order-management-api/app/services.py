"""
Business logic services for Order Management.
Replicates Java service layer patterns.
"""
from decimal import Decimal
from typing import Optional, List
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Customer, Product, OrderEntity, OrderItem, Payment, 
    IdempotencyRecord, AuditLog, OrderStatus, PaymentStatus
)
from app.schemas import OrderCreateRequest


class BusinessValidationException(Exception):
    """Business rule violation exception"""
    pass


class ResourceNotFoundException(Exception):
    """Resource not found exception"""
    pass


class PaymentException(Exception):
    """Payment processing exception"""
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class CustomerService:
    """Customer service"""
    
    @staticmethod
    async def find_or_create_customer(
        db: AsyncSession,
        email: str,
        first_name: str,
        last_name: str
    ) -> Customer:
        """Find or create customer by email"""
        result = await db.execute(select(Customer).where(Customer.email == email))
        customer = result.scalar_one_or_none()
        
        if not customer:
            customer = Customer(
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            db.add(customer)
            await db.flush()
        
        return customer
    
    @staticmethod
    async def find_by_email(db: AsyncSession, email: str) -> Customer:
        """Find customer by email"""
        result = await db.execute(select(Customer).where(Customer.email == email))
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise ResourceNotFoundException(f"Customer not found with email: {email}")
        
        return customer


class DiscountService:
    """Discount calculation service"""
    
    DISCOUNT_TIERS = [
        (Decimal("1000.00"), Decimal("0.10")),  # 10% off for orders >= $1000
        (Decimal("500.00"), Decimal("0.05")),   # 5% off for orders >= $500
    ]
    
    @staticmethod
    def calculate_discount(subtotal: Decimal) -> Decimal:
        """Calculate discount based on subtotal"""
        for threshold, discount_rate in DiscountService.DISCOUNT_TIERS:
            if subtotal >= threshold:
                return subtotal * discount_rate
        return Decimal("0.00")


class PaymentService:
    """Payment service with retry logic"""
    
    PAYMENT_SERVICE_URL = "http://localhost:8080/mock/payment/authorize"
    VOID_URL = "http://localhost:8080/mock/payment/void"
    TIMEOUT_SECONDS = 30
    
    @staticmethod
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(PaymentException),
        reraise=True
    )
    async def authorize_payment(db: AsyncSession, order_id: int) -> Payment:
        """
        Authorize payment with retry logic.
        Retries on 5xx errors (max 2 attempts with 1s delay).
        """
        result = await db.execute(
            select(OrderEntity).where(OrderEntity.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise ResourceNotFoundException(f"Order not found with id: {order_id}")
        
        payment = Payment(order_id=order.id, amount=order.total)
        db.add(payment)
        await db.flush()
        
        try:
            authorization_id = await PaymentService._call_external_payment_service(order.total)
            
            payment.authorize(authorization_id)
            await db.flush()
            
            order.mark_as_paid()
            await db.flush()
            
            return payment
            
        except httpx.HTTPStatusError as e:
            payment.increment_retry_attempts()
            
            if 400 <= e.response.status_code < 500:
                error_message = f"Payment authorization failed: {e.response.text}"
                payment.fail(error_message)
                await db.flush()
                raise PaymentException(error_message, retryable=False)
            
            elif 500 <= e.response.status_code < 600:
                error_message = "Payment service temporarily unavailable"
                payment.fail(error_message)
                await db.flush()
                raise PaymentException(error_message, retryable=True)
            
            else:
                error_message = f"Unexpected payment error: {e.response.status_code}"
                payment.fail(error_message)
                await db.flush()
                raise PaymentException(error_message, retryable=False)
                
        except Exception as e:
            payment.increment_retry_attempts()
            error_message = f"Payment authorization failed: {str(e)}"
            payment.fail(error_message)
            await db.flush()
            raise PaymentException(error_message, retryable=True)
    
    @staticmethod
    async def _call_external_payment_service(amount: Decimal) -> str:
        """Call external payment authorization service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PaymentService.PAYMENT_SERVICE_URL,
                json={
                    "amount": str(amount),
                    "currency": "USD",
                    "paymentMethod": "CARD"
                },
                timeout=PaymentService.TIMEOUT_SECONDS
            )
            response.raise_for_status()
            
            data = response.json()
            if "authorizationId" not in data:
                raise PaymentException("Invalid response from payment service", retryable=False)
            
            return data["authorizationId"]
    
    @staticmethod
    async def void_payment(db: AsyncSession, payment_id: int):
        """Void payment (compensation action)"""
        result = await db.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise ResourceNotFoundException(f"Payment not found with id: {payment_id}")
        
        if payment.status != PaymentStatus.AUTHORIZED:
            raise ValueError("Can only void authorized payments")
        
        try:
            await PaymentService._call_external_void_service(payment.external_authorization_id)
            
            payment.void_payment()
            await db.flush()
            
        except Exception as e:
            raise PaymentException(f"Failed to void payment: {str(e)}", retryable=False)
    
    @staticmethod
    async def _call_external_void_service(authorization_id: str):
        """Call external payment void service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PaymentService.VOID_URL,
                json={"authorizationId": authorization_id},
                timeout=PaymentService.TIMEOUT_SECONDS
            )
            response.raise_for_status()


class OrderService:
    """Order service with complete order placement pipeline"""
    
    @staticmethod
    async def create_order(
        db: AsyncSession,
        request: OrderCreateRequest,
        idempotency_key: Optional[str] = None
    ) -> OrderEntity:
        """
        Create order with complete pipeline:
        validate → stock check → price → persist → decrement stock
        """
        if idempotency_key:
            result = await db.execute(
                select(OrderEntity).where(OrderEntity.idempotency_key == idempotency_key)
            )
            existing_order = result.scalar_one_or_none()
            if existing_order:
                await db.refresh(existing_order, ["items", "customer", "payment"])
                return existing_order
        
        customer = await CustomerService.find_or_create_customer(
            db,
            request.customer_email,
            OrderService._extract_first_name(request.customer_email),
            OrderService._extract_last_name(request.customer_email)
        )
        
        order = OrderEntity(
            customer_id=customer.id,
            idempotency_key=idempotency_key
        )
        db.add(order)
        await db.flush()
        
        for item_request in request.items:
            await OrderService._process_order_item(db, order, item_request)
        
        order.calculate_totals()
        discount_amount = DiscountService.calculate_discount(order.subtotal)
        order.apply_discount(discount_amount)
        
        if order.total < Decimal("0.01"):
            raise BusinessValidationException("Order total must be at least $0.01")
        
        await db.flush()
        
        if idempotency_key:
            idempotency_record = IdempotencyRecord(
                idempotency_key=idempotency_key,
                operation_type="ORDER_CREATE",
                result_entity_id=order.id,
                result_data=order.status.value
            )
            db.add(idempotency_record)
        
        audit_log = AuditLog.order_created_log(order.id, customer.email)
        db.add(audit_log)
        
        await db.flush()
        
        await db.refresh(order, ["items", "customer", "payment"])
        
        return order
    
    @staticmethod
    async def _process_order_item(
        db: AsyncSession,
        order: OrderEntity,
        item_request
    ):
        """Process individual order item with validation and atomic stock decrement"""
        result = await db.execute(select(Product).where(Product.sku == item_request.product_sku))
        product = result.scalar_one_or_none()
        
        if not product:
            raise ResourceNotFoundException(f"Product not found with SKU: {item_request.product_sku}")
        
        if not product.active:
            raise BusinessValidationException(f"Product {product.sku} is not available")
        
        if product.stock_quantity < item_request.quantity:
            raise BusinessValidationException(
                f"Insufficient stock for product {product.sku}. "
                f"Available: {product.stock_quantity}, Requested: {item_request.quantity}"
            )
        
        unit_price = product.price
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_sku=product.sku,
            product_name=product.name,
            quantity=item_request.quantity,
            unit_price=unit_price,
            subtotal=unit_price * item_request.quantity
        )
        db.add(order_item)
        order.items.append(order_item)
        
        product.decrement_stock(item_request.quantity)
        await db.flush()
    
    @staticmethod
    async def get_order(db: AsyncSession, order_id: int) -> OrderEntity:
        """Get order by ID"""
        result = await db.execute(
            select(OrderEntity)
            .options(selectinload(OrderEntity.items))
            .options(selectinload(OrderEntity.customer))
            .options(selectinload(OrderEntity.payment))
            .where(OrderEntity.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise ResourceNotFoundException(f"Order not found with id: {order_id}")
        
        return order
    
    @staticmethod
    async def get_customer_orders(
        db: AsyncSession,
        email: str,
        page: int = 0,
        size: int = 10
    ) -> tuple[List[OrderEntity], int]:
        """Get orders for customer with pagination"""
        customer = await CustomerService.find_by_email(db, email)
        
        count_result = await db.execute(
            select(OrderEntity).where(OrderEntity.customer_id == customer.id)
        )
        total = len(count_result.scalars().all())
        
        result = await db.execute(
            select(OrderEntity)
            .options(selectinload(OrderEntity.items))
            .options(selectinload(OrderEntity.customer))
            .options(selectinload(OrderEntity.payment))
            .where(OrderEntity.customer_id == customer.id)
            .order_by(OrderEntity.created_at.desc())
            .offset(page * size)
            .limit(size)
        )
        orders = result.scalars().all()
        
        return list(orders), total
    
    @staticmethod
    async def cancel_order(db: AsyncSession, order_id: int) -> OrderEntity:
        """Cancel order with compensating actions (restore stock, void payment)"""
        order = await OrderService.get_order(db, order_id)
        
        if not order.can_be_cancelled():
            raise BusinessValidationException(f"Order cannot be cancelled in status: {order.status}")
        
        for item in order.items:
            result = await db.execute(select(Product).where(Product.id == item.product_id))
            product = result.scalar_one()
            product.increment_stock(item.quantity)
        
        if order.payment and order.payment.status == PaymentStatus.AUTHORIZED:
            await PaymentService.void_payment(db, order.payment.id)
        
        order.cancel()
        await db.flush()
        
        audit_log = AuditLog.order_cancelled_log(order.id, "Customer requested cancellation")
        db.add(audit_log)
        
        await db.flush()
        await db.refresh(order, ["items", "customer", "payment"])
        
        return order
    
    @staticmethod
    def _extract_first_name(email: str) -> str:
        """Extract first name from email (simplified)"""
        local_part = email.split('@')[0]
        return ''.join(c for c in local_part if c.isalpha())
    
    @staticmethod
    def _extract_last_name(email: str) -> str:
        """Extract last name from email (simplified)"""
        return "Customer"
