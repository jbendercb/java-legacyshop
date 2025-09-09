from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import json

from app.models.product import Product
from app.models.customer import Customer
from app.models.order import OrderEntity, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.idempotency import IdempotencyRecord
from app.models.audit import AuditLog, OperationType
from app.schemas.order import OrderCreateRequest, OrderResponse
from app.services.discount_service import DiscountService
from app.services.payment_service import PaymentService
from app.exceptions import (
    ProductNotFoundError, 
    InsufficientStockError, 
    OrderNotFoundError,
    BusinessValidationError
)


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.discount_service = DiscountService()
        self.payment_service = PaymentService(db)

    async def create_order(self, order_request: OrderCreateRequest, idempotency_key: Optional[str] = None) -> OrderResponse:
        if idempotency_key:
            existing_record = self.db.query(IdempotencyRecord).filter(
                IdempotencyRecord.idempotency_key == idempotency_key
            ).first()
            
            if existing_record:
                response_data = json.loads(existing_record.response_body)
                return OrderResponse(**response_data)

        try:
            customer = await self._get_or_create_customer(order_request.customer_email)
            
            order = OrderEntity(
                customer_id=customer.id,
                subtotal=Decimal("0.00"),
                discount_amount=Decimal("0.00"),
                total=Decimal("0.00"),
                idempotency_key=idempotency_key
            )
            self.db.add(order)
            self.db.flush()

            total_subtotal = Decimal("0.00")
            for item_request in order_request.items:
                product = self.db.query(Product).filter(Product.id == item_request.product_id).first()
                if not product:
                    raise ProductNotFoundError(f"Product with ID '{item_request.product_id}' not found")
                
                if not product.is_available():
                    raise BusinessValidationError(f"Product '{product.name}' is not available")
                
                if not product.decrement_stock(item_request.quantity):
                    raise InsufficientStockError(
                        f"Insufficient stock for product '{product.name}'. Available: {product.stock_quantity}, Requested: {item_request.quantity}"
                    )

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    sku=product.sku,
                    name=product.name,
                    unit_price=product.price,
                    quantity=item_request.quantity,
                    subtotal=product.price * item_request.quantity
                )
                self.db.add(order_item)
                total_subtotal += order_item.subtotal

                self._create_audit_log(OperationType.STOCK_DECREMENTED, "Product", product.id, 
                                     f"Stock decremented by {item_request.quantity} for order {order.id}")

            order.subtotal = total_subtotal
            order.discount_amount = self.discount_service.calculate_discount(total_subtotal)
            order.total = total_subtotal - order.discount_amount

            if order.total < Decimal("0.01"):
                raise BusinessValidationError("Order total must be at least $0.01")

            self.db.commit()

            self._create_audit_log(OperationType.ORDER_CREATED, "OrderEntity", order.id, 
                                 f"Order created for customer {customer.email}")

            order_response = OrderResponse.from_order_entity(order)

            if idempotency_key:
                idempotency_record = IdempotencyRecord(
                    idempotency_key=idempotency_key,
                    resource_type="OrderEntity",
                    resource_id=order.id,
                    response_body=order_response.model_dump_json(),
                    status_code=201
                )
                self.db.add(idempotency_record)
                self.db.commit()

            return order_response

        except Exception as e:
            self.db.rollback()
            raise

    async def get_order(self, order_id: int) -> OrderResponse:
        order = self.db.query(OrderEntity).filter(OrderEntity.id == order_id).first()
        if not order:
            raise OrderNotFoundError(f"Order with ID {order_id} not found")
        return OrderResponse.from_order_entity(order)

    async def get_customer_orders(self, customer_email: str) -> List[OrderResponse]:
        customer = self.db.query(Customer).filter(Customer.email == customer_email).first()
        if not customer:
            return []
        
        orders = self.db.query(OrderEntity).filter(OrderEntity.customer_id == customer.id).all()
        return [OrderResponse.from_order_entity(order) for order in orders]

    async def authorize_payment(self, order_id: int):
        order = self.db.query(OrderEntity).filter(OrderEntity.id == order_id).first()
        if not order:
            raise OrderNotFoundError(f"Order with ID {order_id} not found")

        if order.status != OrderStatus.PENDING:
            raise BusinessValidationError(f"Cannot authorize payment for order in status {order.status}")

        pass

    async def cancel_order(self, order_id: int):
        order = self.db.query(OrderEntity).filter(OrderEntity.id == order_id).first()
        if not order:
            raise OrderNotFoundError(f"Order with ID {order_id} not found")

        if not order.can_be_cancelled():
            raise BusinessValidationError(f"Cannot cancel order in status {order.status}")

        try:
            for item in order.items:
                product = self.db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.increment_stock(item.quantity)
                    self._create_audit_log(OperationType.STOCK_INCREMENTED, "Product", product.id,
                                         f"Stock restored by {item.quantity} for cancelled order {order.id}")

            if order.payment and order.payment.status == PaymentStatus.AUTHORIZED:
                await self.payment_service.void_payment(order.payment)

            order.status = OrderStatus.CANCELLED
            self.db.commit()

            self._create_audit_log(OperationType.ORDER_CANCELLED, "OrderEntity", order.id,
                                 f"Order cancelled and stock restored")

        except Exception as e:
            self.db.rollback()
            raise

    async def _get_or_create_customer(self, email: str) -> Customer:
        customer = self.db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            customer = Customer(email=email, name=email.split('@')[0])
            self.db.add(customer)
            self.db.flush()
        return customer

    def _create_audit_log(self, operation_type: OperationType, entity_type: str, entity_id: int, details: str):
        audit_log = AuditLog(
            operation_type=operation_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
        self.db.add(audit_log)
