from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from decimal import Decimal
import json

from ..repositories import order_repository as orders_repo
from ..utils.problem_details import ResourceNotFoundError, BusinessValidationError, DuplicateResourceError
from ..models.product import Product
from ..models.order import Order, OrderStatus
from ..models.order_item import OrderItem
from ..models.idempotency import IdempotencyRecord
from ..models.customer import Customer
from ..schemas.order import OrderCreate
from ..utils.money import quantize_2
from ..services.discount_service import calculate_discount
from ..utils.idempotency import canonicalize_request, compute_request_hash

def _get_or_create_customer(db: Session, email: str) -> Customer:
    cust = db.execute(select(Customer).where(Customer.email == email)).scalar_one_or_none()
    if cust:
        return cust
    cust = Customer(email=email)
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return cust

def create_order(db: Session, body: OrderCreate, idem_key: str | None) -> tuple[dict, int]:
    canonical = canonicalize_request(body.model_dump())
    req_hash = compute_request_hash(canonical)
    if idem_key:
        existing = db.get(IdempotencyRecord, idem_key)
        if existing:
            if existing.request_hash == req_hash:
                return json.loads(existing.response_body), 200
            raise DuplicateResourceError("Idempotency-Key reuse with different request body")
    customer = _get_or_create_customer(db, body.customerEmail)
    subtotal = Decimal("0.00")
    items: list[OrderItem] = []
    for item in body.items:
        prod = db.execute(select(Product).where(Product.sku == item.productSku)).scalar_one_or_none()
        if not prod or not prod.active:
            raise BusinessValidationError(f"Product {item.productSku} unavailable")
        if prod.stock_quantity < item.quantity:
            raise BusinessValidationError(f"Insufficient stock for {item.productSku}")
        unit = quantize_2(prod.price)
        sub = quantize_2(unit * item.quantity)
        subtotal += sub
        prod.stock_quantity -= item.quantity
        oi = OrderItem(product_id=prod.id, quantity=item.quantity, unit_price=unit, subtotal=sub)
        items.append(oi)
    subtotal = quantize_2(subtotal)
    discount = calculate_discount(subtotal)
    total = quantize_2(subtotal - discount)
    if total <= Decimal("0.00"):
        raise BusinessValidationError("Total must be positive")
    order = Order(status=OrderStatus.PENDING, subtotal=subtotal, discount=discount, total=total, customer_id=customer.id)
    order.items = items
    db.add(order)
    db.commit()
    db.refresh(order)
    resp = {
        "id": order.id,
        "status": order.status.value,
        "subtotal": str(order.subtotal),
        "discount": str(order.discount),
        "total": str(order.total),
        "items": [
            {
                "productId": it.product_id,
                "productSku": db.get(Product, it.product_id).sku,
                "quantity": it.quantity,
                "unitPrice": str(it.unit_price),
                "subtotal": str(it.subtotal),
            }
            for it in order.items
        ],
    }
    status_code = 201
    if idem_key:
        rec = IdempotencyRecord(
            key=idem_key,
            request_hash=req_hash,
            response_body=json.dumps(resp),
            status_code=status_code,
            operation_type="ORDER_CREATE",
        )
        db.add(rec)
        db.commit()
    return resp, status_code

def get_order(db: Session, order_id: int) -> dict:
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise ResourceNotFoundError("Order not found")
    return {
        "id": order.id,
        "status": order.status.value,
        "subtotal": str(order.subtotal),
        "discount": str(order.discount),
        "total": str(order.total),
        "items": [
            {
                "productId": it.product_id,
                "productSku": db.get(Product, it.product_id).sku,
                "quantity": it.quantity,
                "unitPrice": str(it.unit_price),
                "subtotal": str(it.subtotal),
            }
            for it in order.items
        ],
    }

def list_customer_orders(db: Session, email: str) -> list[dict]:
    from ..repositories.order_repository import get_by_customer_email
    orders = get_by_customer_email(db, email)
    res: list[dict] = []
    for order in orders:
        res.append({
            "id": order.id,
            "status": order.status.value,
            "subtotal": str(order.subtotal),
            "discount": str(order.discount),
            "total": str(order.total),
            "items": [
                {
                    "productId": it.product_id,
                    "productSku": getattr(it, "product", None).sku if getattr(it, "product", None) else db.get(Product, it.product_id).sku,
                    "quantity": it.quantity,
                    "unitPrice": str(it.unit_price),
                    "subtotal": str(it.subtotal),
                }
                for it in order.items
            ],
        })
    return res
