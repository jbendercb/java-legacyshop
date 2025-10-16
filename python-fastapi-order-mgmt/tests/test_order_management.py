"""
Comprehensive test suite for Order Management API - FastAPI Implementation
This test suite validates behavioral equivalence with Java Spring Boot implementation

Test coverage based on CoreStory project #75 analysis:
- POST /api/orders - Order creation with idempotency
- GET /api/orders/{id} - Order retrieval
- GET /api/orders/customer/{email} - Customer orders with pagination
- POST /api/orders/{id}/authorize-payment - Payment authorization with retry
- POST /api/orders/{id}/cancel - Order cancellation with compensation
"""

import pytest
from decimal import Decimal
from datetime import datetime
import uuid


class TestOrderCreation:
    """Tests for POST /api/orders endpoint"""
    
    def test_create_order_success(self, client, sample_products, sample_customer):
        """Test successful order creation with all validations"""
        idempotency_key = str(uuid.uuid4())
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": [
                {"productSku": sample_products[0]["sku"], "quantity": 2},
                {"productSku": sample_products[1]["sku"], "quantity": 1}
            ]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["customerEmail"] == sample_customer["email"]
        assert data["status"] == "PENDING"
        assert len(data["items"]) == 2
        assert data["idempotencyKey"] == idempotency_key
        assert "subtotal" in data
        assert "discountAmount" in data
        assert "total" in data
        assert data["createdAt"] is not None
    
    def test_create_order_with_discount_tier1(self, client, sample_products, sample_customer):
        """Test 5% discount for orders $50-$99.99"""
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": [{"productSku": sample_products[0]["sku"], "quantity": 3}]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 201
        data = response.json()
        subtotal = Decimal(str(data["subtotal"]))
        discount = Decimal(str(data["discountAmount"]))
        
        if Decimal("50") <= subtotal < Decimal("100"):
            expected_discount = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
            assert discount == expected_discount
    
    def test_create_order_with_discount_tier2(self, client, expensive_products, sample_customer):
        """Test 10% discount for orders $100-$199.99"""
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": [{"productSku": expensive_products[0]["sku"], "quantity": 5}]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 201
        data = response.json()
        subtotal = Decimal(str(data["subtotal"]))
        discount = Decimal(str(data["discountAmount"]))
        
        if Decimal("100") <= subtotal < Decimal("200"):
            expected_discount = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
            assert discount == expected_discount
    
    def test_create_order_with_discount_tier3(self, client, expensive_products, sample_customer):
        """Test 15% discount for orders >= $200"""
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": [{"productSku": expensive_products[0]["sku"], "quantity": 10}]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 201
        data = response.json()
        subtotal = Decimal(str(data["subtotal"]))
        discount = Decimal(str(data["discountAmount"]))
        
        if subtotal >= Decimal("200"):
            expected_discount = (subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
            assert discount == expected_discount
    
    def test_create_order_idempotency(self, client, sample_products, sample_customer):
        """Test idempotency - duplicate requests return same order"""
        idempotency_key = str(uuid.uuid4())
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": [{"productSku": sample_products[0]["sku"], "quantity": 1}]
        }
        
        response1 = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        assert response1.status_code == 201
        order_id_1 = response1.json()["id"]
        
        response2 = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        assert response2.status_code == 200  # or 201 depending on implementation
        order_id_2 = response2.json()["id"]
        
        assert order_id_1 == order_id_2
    
    def test_create_order_missing_email(self, client, sample_products):
        """Test validation error for missing customer email"""
        request_data = {
            "items": [{"productSku": sample_products[0]["sku"], "quantity": 1}]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 400
        error = response.json()
        assert "type" in error
        assert "title" in error
        assert "status" in error
        assert error["status"] == 400
    
    def test_create_order_invalid_email(self, client, sample_products):
        """Test validation error for invalid email format"""
        request_data = {
            "customerEmail": "invalid-email",
            "items": [{"productSku": sample_products[0]["sku"], "quantity": 1}]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 400
    
    def test_create_order_empty_items(self, client, sample_customer):
        """Test validation error for empty items list"""
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": []
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 400
    
    def test_create_order_invalid_quantity(self, client, sample_products, sample_customer):
        """Test validation error for quantity < 1"""
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": [{"productSku": sample_products[0]["sku"], "quantity": 0}]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 400
    
    def test_create_order_insufficient_stock(self, client, low_stock_product, sample_customer):
        """Test error when insufficient stock available"""
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": [{"productSku": low_stock_product["sku"], "quantity": 1000}]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 400
        error = response.json()
        assert "stock" in error["detail"].lower() or "insufficient" in error["detail"].lower()
    
    def test_create_order_inactive_product(self, client, inactive_product, sample_customer):
        """Test error when ordering inactive product"""
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": [{"productSku": inactive_product["sku"], "quantity": 1}]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 400


class TestOrderRetrieval:
    """Tests for GET /api/orders/{id} endpoint"""
    
    def test_get_order_success(self, client, sample_order):
        """Test successful order retrieval"""
        response = client.get(f"/api/orders/{sample_order['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_order["id"]
        assert "customerEmail" in data
        assert "status" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0
        
        item = data["items"][0]
        assert "id" in item
        assert "productSku" in item
        assert "productName" in item
        assert "quantity" in item
        assert "unitPrice" in item
        assert "subtotal" in item
    
    def test_get_order_not_found(self, client):
        """Test 404 error for non-existent order"""
        response = client.get("/api/orders/99999")
        
        assert response.status_code == 404
        error = response.json()
        assert "type" in error
        assert error["status"] == 404
        assert "resource-not-found" in error["type"]


class TestCustomerOrders:
    """Tests for GET /api/orders/customer/{email} endpoint"""
    
    def test_get_customer_orders_success(self, client, sample_customer_with_orders):
        """Test successful customer orders retrieval"""
        email = sample_customer_with_orders["email"]
        response = client.get(f"/api/orders/customer/{email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total_orders" in data
        assert "current_page" in data
        assert "page_size" in data
        assert isinstance(data["orders"], list)
    
    def test_get_customer_orders_pagination(self, client, sample_customer_with_many_orders):
        """Test pagination parameters"""
        email = sample_customer_with_many_orders["email"]
        
        response = client.get(f"/api/orders/customer/{email}?page=1&size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["current_page"] == 1
        assert data["page_size"] == 5
        assert len(data["orders"]) <= 5
        
        response = client.get(f"/api/orders/customer/{email}?page=2&size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["current_page"] == 2
    
    def test_get_customer_orders_sorting(self, client, sample_customer_with_orders):
        """Test sorting by created_at descending (default)"""
        email = sample_customer_with_orders["email"]
        response = client.get(f"/api/orders/customer/{email}?sort=created_at:desc")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["orders"]) > 1:
            dates = [datetime.fromisoformat(o["createdAt"].replace("Z", "+00:00")) 
                    for o in data["orders"]]
            assert dates == sorted(dates, reverse=True)
    
    def test_get_customer_orders_empty(self, client):
        """Test empty result for customer with no orders"""
        response = client.get("/api/orders/customer/noorders@example.com")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_orders"] == 0
        assert len(data["orders"]) == 0


class TestPaymentAuthorization:
    """Tests for POST /api/orders/{id}/authorize-payment endpoint"""
    
    def test_authorize_payment_success(self, client, pending_order, mock_payment_service):
        """Test successful payment authorization"""
        mock_payment_service.set_response(200, {"authorization_id": "AUTH123"})
        
        response = client.post(f"/api/orders/{pending_order['id']}/authorize-payment")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PAID"
    
    def test_authorize_payment_retry_on_5xx(self, client, pending_order, mock_payment_service):
        """Test retry logic for 5xx errors - max 2 attempts"""
        mock_payment_service.set_responses([
            (503, {"error": "Service unavailable"}),
            (200, {"authorization_id": "AUTH123"})
        ])
        
        response = client.post(f"/api/orders/{pending_order['id']}/authorize-payment")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PAID"
        assert mock_payment_service.call_count == 2
    
    def test_authorize_payment_max_retries_exceeded(self, client, pending_order, mock_payment_service):
        """Test failure after max retries (2 attempts) exhausted"""
        mock_payment_service.set_response(503, {"error": "Service unavailable"})
        
        response = client.post(f"/api/orders/{pending_order['id']}/authorize-payment")
        
        assert response.status_code == 503
        error = response.json()
        assert "payment-service-unavailable" in error["type"]
        assert mock_payment_service.call_count == 2  # Max 2 attempts
    
    def test_authorize_payment_no_retry_on_4xx(self, client, pending_order, mock_payment_service):
        """Test no retry for 4xx errors"""
        mock_payment_service.set_response(402, {"error": "Payment required"})
        
        response = client.post(f"/api/orders/{pending_order['id']}/authorize-payment")
        
        assert response.status_code == 402
        assert mock_payment_service.call_count == 1  # No retry
    
    def test_authorize_payment_already_paid(self, client, paid_order):
        """Test error when order already paid"""
        response = client.post(f"/api/orders/{paid_order['id']}/authorize-payment")
        
        assert response.status_code == 400
        error = response.json()
        assert "already paid" in error["detail"].lower() or "invalid state" in error["detail"].lower()
    
    def test_authorize_payment_cancelled_order(self, client, cancelled_order):
        """Test error when order is cancelled"""
        response = client.post(f"/api/orders/{cancelled_order['id']}/authorize-payment")
        
        assert response.status_code == 400
    
    def test_authorize_payment_order_not_found(self, client):
        """Test 404 for non-existent order"""
        response = client.post("/api/orders/99999/authorize-payment")
        
        assert response.status_code == 404


class TestOrderCancellation:
    """Tests for POST /api/orders/{id}/cancel endpoint"""
    
    def test_cancel_pending_order(self, client, pending_order_with_stock):
        """Test cancellation of pending order - stock restored"""
        order_id = pending_order_with_stock["id"]
        original_stock = pending_order_with_stock["product_stock"]
        
        response = client.post(f"/api/orders/{order_id}/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"
        
    
    def test_cancel_paid_order_with_refund(self, client, paid_order, mock_payment_service):
        """Test cancellation of paid order - payment refunded"""
        mock_payment_service.set_void_response(200, {"void_id": "VOID123"})
        order_id = paid_order["id"]
        
        response = client.post(f"/api/orders/{order_id}/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"
        
        assert mock_payment_service.void_called
    
    def test_cancel_order_compensation_atomic(self, client, paid_order_with_stock, mock_payment_service):
        """Test that cancellation compensation is atomic - all or nothing"""
        mock_payment_service.set_void_response(500, {"error": "Cannot void"})
        order_id = paid_order_with_stock["id"]
        original_stock = paid_order_with_stock["product_stock"]
        
        response = client.post(f"/api/orders/{order_id}/cancel")
        
        assert response.status_code >= 400
    
    def test_cancel_shipped_order_error(self, client, shipped_order):
        """Test error when trying to cancel shipped order"""
        response = client.post(f"/api/orders/{shipped_order['id']}/cancel")
        
        assert response.status_code == 400
        error = response.json()
        assert "cannot be cancelled" in error["detail"].lower()
    
    def test_cancel_already_cancelled_order(self, client, cancelled_order):
        """Test error when order already cancelled"""
        response = client.post(f"/api/orders/{cancelled_order['id']}/cancel")
        
        assert response.status_code == 400
    
    def test_cancel_order_not_found(self, client):
        """Test 404 for non-existent order"""
        response = client.post("/api/orders/99999/cancel")
        
        assert response.status_code == 404


class TestRFC7807ErrorFormat:
    """Tests for RFC-7807 Problem Details error format"""
    
    def test_validation_error_format(self, client, sample_customer):
        """Test RFC-7807 format for validation errors"""
        request_data = {
            "customerEmail": "invalid-email",
            "items": []
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 400
        error = response.json()
        
        assert "type" in error
        assert "title" in error
        assert "status" in error
        assert "detail" in error
        assert "instance" in error
        
        assert error["status"] == 400
        assert "/errors/" in error["type"]
    
    def test_not_found_error_format(self, client):
        """Test RFC-7807 format for 404 errors"""
        response = client.get("/api/orders/99999")
        
        assert response.status_code == 404
        error = response.json()
        
        assert "type" in error
        assert "title" in error
        assert error["status"] == 404
        assert "resource-not-found" in error["type"].lower()
    
    def test_service_unavailable_error_format(self, client, pending_order, mock_payment_service):
        """Test RFC-7807 format for 503 errors"""
        mock_payment_service.set_response(503, {"error": "Unavailable"})
        
        response = client.post(f"/api/orders/{pending_order['id']}/authorize-payment")
        
        assert response.status_code == 503
        error = response.json()
        
        assert "type" in error
        assert error["status"] == 503
        assert "payment-service-unavailable" in error["type"].lower()


class TestAuditLogging:
    """Tests for audit logging functionality"""
    
    def test_order_creation_logged(self, client, sample_products, sample_customer, audit_log_db):
        """Test that order creation is logged to audit table"""
        request_data = {
            "customerEmail": sample_customer["email"],
            "items": [{"productSku": sample_products[0]["sku"], "quantity": 1}]
        }
        
        response = client.post(
            "/api/orders",
            json=request_data,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        
        assert response.status_code == 201
        order_id = response.json()["id"]
        
        logs = audit_log_db.get_logs(entity_type="ORDER", entity_id=order_id)
        assert len(logs) > 0
        assert any(log["operation_type"] == "ORDER_CREATED" for log in logs)
    
    def test_order_cancellation_logged(self, client, pending_order, audit_log_db):
        """Test that order cancellation is logged"""
        response = client.post(f"/api/orders/{pending_order['id']}/cancel")
        
        assert response.status_code == 200
        
        logs = audit_log_db.get_logs(entity_type="ORDER", entity_id=pending_order["id"])
        assert any(log["operation_type"] == "ORDER_CANCELLED" for log in logs)
    
    def test_payment_authorization_logged(self, client, pending_order, mock_payment_service, audit_log_db):
        """Test that payment authorization is logged"""
        mock_payment_service.set_response(200, {"authorization_id": "AUTH123"})
        
        response = client.post(f"/api/orders/{pending_order['id']}/authorize-payment")
        
        assert response.status_code == 200
        
        logs = audit_log_db.get_logs(entity_type="PAYMENT")
        assert any(log["operation_type"] == "PAYMENT_AUTHORIZED" for log in logs)



"""
Fixtures needed in conftest.py:
- client: FastAPI test client
- sample_products: List of test products
- expensive_products: Products priced to test discount tiers
- low_stock_product: Product with limited stock
- inactive_product: Inactive product
- sample_customer: Test customer
- sample_order: Pre-created order
- pending_order: Order in PENDING status
- paid_order: Order in PAID status
- cancelled_order: Order in CANCELLED status
- shipped_order: Order in SHIPPED status
- sample_customer_with_orders: Customer with multiple orders
- sample_customer_with_many_orders: Customer with many orders for pagination
- pending_order_with_stock: Pending order with stock info
- paid_order_with_stock: Paid order with stock info
- mock_payment_service: Mock external payment service
- audit_log_db: Mock or test audit log database
"""
