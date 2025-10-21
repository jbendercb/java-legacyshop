"""
Order service implementing the complete order placement pipeline.
Mirrors the Java OrderService implementation.
"""

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from app.models.models import (
    Order, OrderItem, Customer, Product, IdempotencyRecord, AuditLog,
    OrderStatus, Payment, PaymentStatus
)
from app.schemas.schemas import OrderCreateRequest, OrderResponse, OrderItemResponse
from app.services.discount_service import discount_service
from app.services.payment_service import payment_service
from app.services.exceptions import BusinessValidationException, ResourceNotFoundException


class OrderService:
    """Service for Order operations demonstrating the complete order placement pipeline"""
    
    def create_order(self, request: OrderCreateRequest, idempotency_key: Optional[str], db: Session) -> OrderResponse:
        """
        Create order with complete pipeline: validate → stock check → price → persist → decrement stock.
        Demonstrates atomic rollback on any failure.
        """
        if idempotency_key:
            existing_order = db.query(Order).filter(Order.idempotency_key == idempotency_key).first()
            if existing_order:
                return self._order_to_response(existing_order)
        
        customer = self._find_or_create_customer(request.customerEmail, db)
        
        order = Order(
            customer_id=customer.id,
            idempotency_key=idempotency_key,
            status=OrderStatus.PENDING
        )
        db.add(order)
        db.flush()  # Get order ID without committing
        
        for item_request in request.items:
            self._process_order_item(order, item_request, db)
        
        db.flush()
        db.refresh(order)
        
        order.calculate_totals()
        discount_amount = discount_service.calculate_discount(Decimal(str(order.subtotal)))
        order.apply_discount(float(discount_amount))
        
        if order.total < 0.01:
            raise BusinessValidationException("Order total must be at least $0.01")
        
        db.commit()
        db.refresh(order)
        
        if idempotency_key:
            idempotency_record = IdempotencyRecord(
                idempotency_key=idempotency_key,
                operation_type="ORDER_CREATE",
                result_entity_id=order.id,
                result_status=order.status.value
            )
            db.add(idempotency_record)
        
        audit_log = AuditLog(
            entity_type="ORDER",
            entity_id=order.id,
            action="CREATED",
            details=f"Order created for customer {customer.email}"
        )
        db.add(audit_log)
        db.commit()
        
        return self._order_to_response(order)
    
    def _process_order_item(self, order: Order, item_request, db: Session):
        """Process individual order item with validation and atomic stock decrement"""
        product = db.query(Product).filter(Product.sku == item_request.productSku).first()
        if not product:
            raise ResourceNotFoundException(f"Product not found with SKU: {item_request.productSku}")
        
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
            subtotal=round(unit_price * item_request.quantity, 2)
        )
        db.add(order_item)
        
        product.decrement_stock(item_request.quantity)
    
    def _find_or_create_customer(self, email: str, db: Session) -> Customer:
        """Find existing customer or create new one"""
        customer = db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            local_part = email.split('@')[0]
            first_name = ''.join(c for c in local_part if c.isalpha())
            
            customer = Customer(
                email=email,
                first_name=first_name or "Customer",
                last_name="Customer"
            )
            db.add(customer)
            db.flush()
        return customer
    
    def get_order(self, order_id: int, db: Session) -> OrderResponse:
        """Get order by ID"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ResourceNotFoundException(f"Order not found with id: {order_id}")
        return self._order_to_response(order)
    
    def get_customer_orders(self, email: str, page: int, size: int, db: Session):
        """Get orders for customer with pagination"""
        customer = db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            raise ResourceNotFoundException(f"Customer not found with email: {email}")
        
        query = db.query(Order).filter(Order.customer_id == customer.id).order_by(Order.created_at.desc())
        total = query.count()
        orders = query.offset(page * size).limit(size).all()
        
        return {
            "content": [self._order_to_response(order) for order in orders],
            "totalElements": total,
            "totalPages": (total + size - 1) // size,
            "size": size,
            "number": page
        }
    
    def cancel_order(self, order_id: int, db: Session) -> OrderResponse:
        """Cancel order with compensating actions (restore stock, void payment)"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ResourceNotFoundException(f"Order not found with id: {order_id}")
        
        if not order.can_be_cancelled():
            raise BusinessValidationException(f"Order cannot be cancelled in status: {order.status.value}")
        
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.increment_stock(item.quantity)
        
        if order.payment and order.payment.status == PaymentStatus.AUTHORIZED:
            payment_service.void_payment(order.payment.id, db)
        
        order.cancel()
        
        audit_log = AuditLog(
            entity_type="ORDER",
            entity_id=order.id,
            action="CANCELLED",
            details="Customer requested cancellation"
        )
        db.add(audit_log)
        
        db.commit()
        db.refresh(order)
        
        return self._order_to_response(order)
    
    def _order_to_response(self, order: Order) -> OrderResponse:
        """Convert Order entity to OrderResponse"""
        items = [
            OrderItemResponse(
                id=item.id,
                productSku=item.product_sku,
                productName=item.product_name,
                quantity=item.quantity,
                unitPrice=item.unit_price,
                subtotal=item.subtotal
            )
            for item in order.items
        ]
        
        return OrderResponse(
            id=order.id,
            customerEmail=order.customer.email,
            status=order.status.value,
            subtotal=order.subtotal,
            discountAmount=order.discount_amount,
            total=order.total,
            idempotencyKey=order.idempotency_key,
            items=items,
            createdAt=order.created_at,
            updatedAt=order.updated_at
        )


order_service = OrderService()
