"""
In-memory database for Order Management system
Thread-safe implementation using locks
"""

import threading
from typing import Dict, List, Optional
from decimal import Decimal
from app.models import Product, Order, OrderItem, IdempotencyRecord, OrderStatus

_orders_lock = threading.Lock()
_products_lock = threading.Lock()
_idempotency_lock = threading.Lock()

_orders: Dict[int, Order] = {}
_products: Dict[int, Product] = {}
_idempotency_records: Dict[str, IdempotencyRecord] = {}

_order_id_counter = 1
_order_item_id_counter = 1


def init_database():
    """Initialize database with test products"""
    global _order_id_counter, _order_item_id_counter
    
    with _products_lock:
        _products.clear()
        _products[1] = Product(1, "Widget A", Decimal("10.00"), 100)
        _products[2] = Product(2, "Widget B", Decimal("25.00"), 50)
        _products[3] = Product(3, "Widget C", Decimal("50.00"), 25)
    
    with _orders_lock:
        _orders.clear()
        _order_id_counter = 1
        _order_item_id_counter = 1
    
    with _idempotency_lock:
        _idempotency_records.clear()



def get_product(product_id: int) -> Optional[Product]:
    """Get product by ID"""
    with _products_lock:
        return _products.get(product_id)


def get_all_products() -> List[Product]:
    """Get all products"""
    with _products_lock:
        return list(_products.values())


def update_product_stock(product_id: int, new_stock: int):
    """Update product stock"""
    with _products_lock:
        if product_id in _products:
            _products[product_id].stock = new_stock



def create_order(order: Order) -> Order:
    """Save a new order"""
    global _order_id_counter
    
    with _orders_lock:
        order.id = _order_id_counter
        _order_id_counter += 1
        _orders[order.id] = order
        return order


def get_order(order_id: int) -> Optional[Order]:
    """Get order by ID"""
    with _orders_lock:
        return _orders.get(order_id)


def get_orders_by_customer(customer_email: str, page: int = 1, size: int = 10) -> tuple[List[Order], int]:
    """
    Get orders for a customer with pagination
    Returns (orders, total_count)
    """
    with _orders_lock:
        customer_orders = [
            order for order in _orders.values()
            if order.customer_email == customer_email
        ]
        
        customer_orders.sort(key=lambda x: x.created_at, reverse=True)
        
        total_count = len(customer_orders)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        
        paginated_orders = customer_orders[start_idx:end_idx]
        
        return paginated_orders, total_count


def update_order_status(order_id: int, new_status: OrderStatus):
    """Update order status"""
    with _orders_lock:
        if order_id in _orders:
            _orders[order_id].status = new_status


def update_order_payment_id(order_id: int, payment_id: str):
    """Update order payment ID"""
    with _orders_lock:
        if order_id in _orders:
            _orders[order_id].payment_id = payment_id


def get_next_order_item_id() -> int:
    """Get next order item ID"""
    global _order_item_id_counter
    item_id = _order_item_id_counter
    _order_item_id_counter += 1
    return item_id



def check_idempotency_key(idempotency_key: str) -> Optional[int]:
    """
    Check if idempotency key exists
    Returns order_id if exists, None otherwise
    """
    with _idempotency_lock:
        record = _idempotency_records.get(idempotency_key)
        return record.order_id if record else None


def save_idempotency_record(idempotency_key: str, order_id: int):
    """Save idempotency record"""
    with _idempotency_lock:
        _idempotency_records[idempotency_key] = IdempotencyRecord(idempotency_key, order_id)


init_database()
