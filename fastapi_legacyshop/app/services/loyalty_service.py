from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.customer import Customer
from app.models.order import OrderEntity, OrderStatus
from app.models.idempotency import IdempotencyRecord
from app.models.audit import AuditLog, OperationType
from app.config import settings
import json


class LoyaltyService:
    def __init__(self, db: Session):
        self.db = db

    async def process_loyalty_points(self):
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        paid_orders = (
            self.db.query(OrderEntity)
            .filter(
                and_(
                    OrderEntity.status == OrderStatus.PAID,
                    OrderEntity.updated_at >= cutoff_time
                )
            )
            .all()
        )
        
        for order in paid_orders:
            await self._process_order_loyalty_points(order)

    async def _process_order_loyalty_points(self, order: OrderEntity):
        idempotency_key = f"loyalty_points_order_{order.id}"
        
        existing_record = self.db.query(IdempotencyRecord).filter(
            IdempotencyRecord.idempotency_key == idempotency_key
        ).first()
        
        if existing_record:
            return

        try:
            points_to_award = self._calculate_loyalty_points(order.total)
            
            if points_to_award > 0:
                customer = order.customer
                old_points = customer.loyalty_points
                customer.add_loyalty_points(points_to_award, settings.loyalty.max_points)
                
                self.db.commit()
                
                self._create_audit_log(
                    OperationType.LOYALTY_POINTS_AWARDED,
                    "Customer",
                    customer.id,
                    f"Awarded {points_to_award} points for order {order.id}. Points: {old_points} -> {customer.loyalty_points}"
                )
                
                idempotency_record = IdempotencyRecord(
                    idempotency_key=idempotency_key,
                    resource_type="LoyaltyPoints",
                    resource_id=customer.id,
                    response_body=json.dumps({"points_awarded": float(points_to_award)}),
                    status_code=200
                )
                self.db.add(idempotency_record)
                self.db.commit()
                
        except Exception as e:
            self.db.rollback()
            self._create_audit_log(
                OperationType.LOYALTY_POINTS_AWARDED,
                "Customer",
                order.customer_id,
                f"Failed to award loyalty points for order {order.id}: {str(e)}"
            )

    def _calculate_loyalty_points(self, order_total: Decimal) -> Decimal:
        return (order_total * settings.loyalty.points_per_dollar).quantize(Decimal('1'), rounding='ROUND_DOWN')

    async def get_customer_loyalty_points(self, customer_email: str) -> Decimal:
        customer = self.db.query(Customer).filter(Customer.email == customer_email).first()
        return customer.loyalty_points if customer else Decimal("0.00")

    def _create_audit_log(self, operation_type: OperationType, entity_type: str, entity_id: int, details: str):
        audit_log = AuditLog(
            operation_type=operation_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
        self.db.add(audit_log)
