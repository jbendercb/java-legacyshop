"""
Integration Test Suite for Order Management Feature

This test suite validates the API contracts and integration points of the Order Management feature.
It ensures that the FastAPI implementation preserves the same contracts as the Java/Spring Boot version.

Test Categories:
1. Order Creation - POST /api/orders
2. Order Retrieval - GET /api/orders/{id}
3. Customer Orders - GET /api/orders/customer/{email}
4. Payment Authorization - POST /api/orders/{id}/authorize-payment
5. Order Cancellation - POST /api/orders/{id}/cancel
6. Idempotency - Duplicate request handling
7. Error Handling - RFC-7807 Problem Details
"""

import pytest
import httpx
from decimal import Decimal
from typing import Dict, Any
import uuid


BASE_URL = "http://localhost:8001"


@pytest.fixture
def client():
    """HTTP client for making API requests"""
    return httpx.Client(base_url=BASE_URL, timeout=30.0)


@pytest.fixture
def test_customer_email():
    """Generate unique customer email for each test"""
    return f"test-{uuid.uuid4()}@example.com"


@pytest.fixture
def idempotency_key():
    """Generate unique idempotency key for each test"""
    return str(uuid.uuid4())


class TestOrderCreation:
    """Test suite for POST /api/orders endpoint"""
    
    def test_create_order_success(self, client, test_customer_email, idempotency_key):
        """Test successful order creation with valid data"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 2},
                {"productSku": "GADGET-002", "quantity": 1}
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["customerEmail"] == test_customer_email
        assert data["status"] == "PENDING"
        assert "subtotal" in data
        assert "discountAmount" in data
        assert "total" in data
        assert data["idempotencyKey"] == idempotency_key
        assert len(data["items"]) == 2
        assert data["createdAt"] is not None
    
    def test_create_order_with_discount_tier1(self, client, test_customer_email, idempotency_key):
        """Test order creation with tier 1 discount (5% at $50+)"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 5}  # Assuming $10 each = $50 subtotal
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        subtotal = Decimal(str(data["subtotal"]))
        discount = Decimal(str(data["discountAmount"]))
        
        if subtotal >= Decimal("50.00"):
            expected_discount = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
            assert discount == expected_discount
    
    def test_create_order_with_discount_tier2(self, client, test_customer_email, idempotency_key):
        """Test order creation with tier 2 discount (10% at $100+)"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 10}  # Assuming $10 each = $100 subtotal
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        subtotal = Decimal(str(data["subtotal"]))
        discount = Decimal(str(data["discountAmount"]))
        
        if subtotal >= Decimal("100.00"):
            expected_discount = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
            assert discount == expected_discount
    
    def test_create_order_with_discount_tier3(self, client, test_customer_email, idempotency_key):
        """Test order creation with tier 3 discount (15% at $200+)"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 20}  # Assuming $10 each = $200 subtotal
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        subtotal = Decimal(str(data["subtotal"]))
        discount = Decimal(str(data["discountAmount"]))
        
        if subtotal >= Decimal("200.00"):
            expected_discount = (subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
            assert discount == expected_discount
    
    def test_create_order_invalid_email(self, client, idempotency_key):
        """Test order creation with invalid email format"""
        request_data = {
            "customerEmail": "not-an-email",
            "items": [
                {"productSku": "WIDGET-001", "quantity": 1}
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 400
        assert "detail" in data
    
    def test_create_order_empty_items(self, client, test_customer_email, idempotency_key):
        """Test order creation with no items"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": []
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "type" in data
        assert data["status"] == 400
    
    def test_create_order_insufficient_stock(self, client, test_customer_email, idempotency_key):
        """Test order creation with insufficient stock"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 99999}  # Unrealistic quantity
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "type" in data
        assert data["status"] == 400
        assert "stock" in data["detail"].lower() or "insufficient" in data["detail"].lower()
    
    def test_create_order_product_not_found(self, client, test_customer_email, idempotency_key):
        """Test order creation with non-existent product"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "NONEXISTENT-SKU", "quantity": 1}
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert data["status"] == 404


class TestIdempotency:
    """Test suite for idempotency behavior"""
    
    def test_duplicate_request_returns_same_order(self, client, test_customer_email, idempotency_key):
        """Test that duplicate requests with same idempotency key return the same order"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 1}
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response1 = client.post("/api/orders", json=request_data, headers=headers)
        assert response1.status_code == 201
        order1 = response1.json()
        
        response2 = client.post("/api/orders", json=request_data, headers=headers)
        assert response2.status_code == 200  # Should return existing order
        order2 = response2.json()
        
        assert order1["id"] == order2["id"]
        assert order1["customerEmail"] == order2["customerEmail"]
        assert order1["total"] == order2["total"]
    
    def test_different_idempotency_keys_create_different_orders(self, client, test_customer_email):
        """Test that different idempotency keys create different orders"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 1}
            ]
        }
        
        headers1 = {"Idempotency-Key": str(uuid.uuid4())}
        response1 = client.post("/api/orders", json=request_data, headers=headers1)
        assert response1.status_code == 201
        order1 = response1.json()
        
        headers2 = {"Idempotency-Key": str(uuid.uuid4())}
        response2 = client.post("/api/orders", json=request_data, headers=headers2)
        assert response2.status_code == 201
        order2 = response2.json()
        
        assert order1["id"] != order2["id"]


class TestOrderRetrieval:
    """Test suite for GET /api/orders/{id} endpoint"""
    
    def test_get_order_success(self, client, test_customer_email, idempotency_key):
        """Test successful order retrieval"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 1}
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        create_response = client.post("/api/orders", json=request_data, headers=headers)
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        response = client.get(f"/api/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["customerEmail"] == test_customer_email
        assert "status" in data
        assert "items" in data
    
    def test_get_order_not_found(self, client):
        """Test retrieval of non-existent order"""
        response = client.get("/api/orders/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert data["status"] == 404


class TestCustomerOrders:
    """Test suite for GET /api/orders/customer/{email} endpoint"""
    
    def test_get_customer_orders_success(self, client, test_customer_email):
        """Test successful retrieval of customer orders"""
        for i in range(3):
            request_data = {
                "customerEmail": test_customer_email,
                "items": [
                    {"productSku": "WIDGET-001", "quantity": 1}
                ]
            }
            headers = {"Idempotency-Key": str(uuid.uuid4())}
            response = client.post("/api/orders", json=request_data, headers=headers)
            assert response.status_code == 201
        
        response = client.get(f"/api/orders/customer/{test_customer_email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data or isinstance(data, list)
        orders = data.get("content", data)
        assert len(orders) >= 3
    
    def test_get_customer_orders_pagination(self, client, test_customer_email):
        """Test pagination of customer orders"""
        for i in range(5):
            request_data = {
                "customerEmail": test_customer_email,
                "items": [
                    {"productSku": "WIDGET-001", "quantity": 1}
                ]
            }
            headers = {"Idempotency-Key": str(uuid.uuid4())}
            response = client.post("/api/orders", json=request_data, headers=headers)
            assert response.status_code == 201
        
        response = client.get(f"/api/orders/customer/{test_customer_email}?page=0&size=2")
        
        assert response.status_code == 200
        data = response.json()
        if "content" in data:
            assert len(data["content"]) <= 2
    
    def test_get_customer_orders_not_found(self, client):
        """Test retrieval of orders for non-existent customer"""
        response = client.get("/api/orders/customer/nonexistent@example.com")
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            orders = data.get("content", data)
            assert len(orders) == 0


class TestPaymentAuthorization:
    """Test suite for POST /api/orders/{id}/authorize-payment endpoint"""
    
    def test_authorize_payment_success(self, client, test_customer_email, idempotency_key):
        """Test successful payment authorization"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 1}
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        create_response = client.post("/api/orders", json=request_data, headers=headers)
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        response = client.post(f"/api/orders/{order_id}/authorize-payment")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "Payment authorized" in str(data)
    
    def test_authorize_payment_order_not_found(self, client):
        """Test payment authorization for non-existent order"""
        response = client.post("/api/orders/99999/authorize-payment")
        
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert data["status"] == 404


class TestOrderCancellation:
    """Test suite for POST /api/orders/{id}/cancel endpoint"""
    
    def test_cancel_order_success(self, client, test_customer_email, idempotency_key):
        """Test successful order cancellation"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 1}
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        create_response = client.post("/api/orders", json=request_data, headers=headers)
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        response = client.post(f"/api/orders/{order_id}/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"
        assert data["id"] == order_id
    
    def test_cancel_order_not_found(self, client):
        """Test cancellation of non-existent order"""
        response = client.post("/api/orders/99999/cancel")
        
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert data["status"] == 404
    
    def test_cancel_order_invalid_status(self, client, test_customer_email, idempotency_key):
        """Test that already cancelled orders cannot be cancelled again"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [
                {"productSku": "WIDGET-001", "quantity": 1}
            ]
        }
        headers = {"Idempotency-Key": idempotency_key}
        create_response = client.post("/api/orders", json=request_data, headers=headers)
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        response1 = client.post(f"/api/orders/{order_id}/cancel")
        assert response1.status_code == 200
        
        response2 = client.post(f"/api/orders/{order_id}/cancel")
        assert response2.status_code == 400
        data = response2.json()
        assert "type" in data
        assert data["status"] == 400


class TestErrorHandling:
    """Test suite for RFC-7807 Problem Details error responses"""
    
    def test_validation_error_format(self, client, idempotency_key):
        """Test that validation errors follow RFC-7807 format"""
        request_data = {
            "customerEmail": "invalid-email",
            "items": []
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert data["status"] == 400
    
    def test_not_found_error_format(self, client):
        """Test that not found errors follow RFC-7807 format"""
        response = client.get("/api/orders/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert data["status"] == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
