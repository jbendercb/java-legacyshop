from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.models.order import OrderEntity, OrderStatus
from app.models.customer import Customer
from app.models.payment import Payment
from app.schemas.report import OrderReportResponse


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    async def get_order_reports(
        self, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        page: int = 0,
        size: int = 20
    ) -> List[OrderReportResponse]:
        
        query = (
            self.db.query(OrderEntity)
            .options(
                joinedload(OrderEntity.customer),
                joinedload(OrderEntity.payment)
            )
        )

        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(OrderEntity.created_at >= start_datetime)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(OrderEntity.created_at <= end_datetime)
        
        if status:
            try:
                order_status = OrderStatus(status.upper())
                query = query.filter(OrderEntity.status == order_status)
            except ValueError:
                pass

        offset = page * size
        orders = query.offset(offset).limit(size).all()

        return [
            OrderReportResponse(
                order_id=order.id,
                customer_email=order.customer.email,
                customer_name=order.customer.name,
                order_status=order.status,
                subtotal=order.subtotal,
                discount_amount=order.discount_amount,
                total=order.total,
                payment_status=order.payment.status if order.payment else None,
                external_payment_id=order.payment.external_payment_id if order.payment else None,
                order_created_at=order.created_at
            )
            for order in orders
        ]
