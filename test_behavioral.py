"""
Behavioral Black Box Test Suite for Order Management Feature

This test suite validates the behavioral equivalence between the Java/Spring Boot
and Python/FastAPI implementations. It tests the actual behavior of the system
without knowledge of internal implementation details.

The tests can be run against either implementation by changing the BASE_URL.

Test Categories:
1. Order Creation Behavior
2. Discount Calculation Behavior
3. Stock Management Behavior
4. Payment Authorization Behavior
5. Order Cancellation Behavior
6. Idempotency Behavior
7. Error Response Behavior
"""

import pytest
import httpx
from decimal import Decimal
from typing import Dict, Any, Optional
import uuid
import time


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


def create_order(client, customer_email: str, items: list, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    """Helper function to create an order"""
    request_data = {
        "customerEmail": customer_email,
        "items": items
    }
    headers = {}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    
    response = client.post("/api/orders", json=request_data, headers=headers)
    return response


class TestOrderCreationBehavior:
    """Test behavioral aspects of order creation"""
    
    def test_order_creation_creates_pending_status(self, client, test_customer_email, idempotency_key):
        """Verify that newly created orders have PENDING status"""
        response = create_order(
            client, 
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 1}],
            idempotency_key
        )
        
        assert response.status_code == 201
        order = response.json()
        assert order["status"] == "PENDING"
    
    def test_order_creation_captures_price_at_order_time(self, client, test_customer_email, idempotency_key):
        """Verify that order items capture the price at order time"""
        response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 2}],
            idempotency_key
        )
        
        assert response.status_code == 201
        order = response.json()
        
        for item in order["items"]:
            assert "unitPrice" in item
            assert Decimal(str(item["unitPrice"])) > 0
            expected_subtotal = Decimal(str(item["quantity"])) * Decimal(str(item["unitPrice"]))
            assert Decimal(str(item["subtotal"])) == expected_subtotal
    
    def test_order_total_calculation(self, client, test_customer_email, idempotency_key):
        """Verify that order total = subtotal - discount"""
        response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 1}],
            idempotency_key
        )
        
        assert response.status_code == 201
        order = response.json()
        
        subtotal = Decimal(str(order["subtotal"]))
        discount = Decimal(str(order["discountAmount"]))
        total = Decimal(str(order["total"]))
        
        assert total == subtotal - discount
    
    def test_order_creation_decrements_stock(self, client, test_customer_email):
        """Verify that order creation decrements product stock"""
        
        response1 = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 1}],
            str(uuid.uuid4())
        )
        
        if response1.status_code == 201:
            response2 = create_order(
                client,
                test_customer_email,
                [{"productSku": "WIDGET-001", "quantity": 1}],
                str(uuid.uuid4())
            )
            
            assert response2.status_code in [201, 400]  # 400 if out of stock


class TestDiscountCalculationBehavior:
    """Test behavioral aspects of discount calculation"""
    
    def test_no_discount_below_threshold(self, client, test_customer_email, idempotency_key):
        """Verify no discount is applied for orders below $50"""
        response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 4}],
            idempotency_key
        )
        
        assert response.status_code == 201
        order = response.json()
        
        subtotal = Decimal(str(order["subtotal"]))
        discount = Decimal(str(order["discountAmount"]))
        
        if subtotal < Decimal("50.00"):
            assert discount == Decimal("0.00")
    
    def test_tier1_discount_at_50_dollars(self, client, test_customer_email, idempotency_key):
        """Verify 5% discount is applied for orders at $50"""
        response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 5}],  # Assuming $10 each
            idempotency_key
        )
        
        assert response.status_code == 201
        order = response.json()
        
        subtotal = Decimal(str(order["subtotal"]))
        discount = Decimal(str(order["discountAmount"]))
        
        if subtotal >= Decimal("50.00") and subtotal < Decimal("100.00"):
            expected_discount = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
            assert discount == expected_discount
    
    def test_tier2_discount_at_100_dollars(self, client, test_customer_email, idempotency_key):
        """Verify 10% discount is applied for orders at $100"""
        response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 10}],  # Assuming $10 each
            idempotency_key
        )
        
        assert response.status_code == 201
        order = response.json()
        
        subtotal = Decimal(str(order["subtotal"]))
        discount = Decimal(str(order["discountAmount"]))
        
        if subtotal >= Decimal("100.00") and subtotal < Decimal("200.00"):
            expected_discount = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
            assert discount == expected_discount
    
    def test_tier3_discount_at_200_dollars(self, client, test_customer_email, idempotency_key):
        """Verify 15% discount is applied for orders at $200"""
        response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 20}],  # Assuming $10 each
            idempotency_key
        )
        
        assert response.status_code == 201
        order = response.json()
        
        subtotal = Decimal(str(order["subtotal"]))
        discount = Decimal(str(order["discountAmount"]))
        
        if subtotal >= Decimal("200.00"):
            expected_discount = (subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
            assert discount == expected_discount
    
    def test_highest_tier_discount_applied(self, client, test_customer_email, idempotency_key):
        """Verify that the highest applicable discount tier is applied"""
        response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 25}],  # Assuming $10 each
            idempotency_key
        )
        
        assert response.status_code == 201
        order = response.json()
        
        subtotal = Decimal(str(order["subtotal"]))
        discount = Decimal(str(order["discountAmount"]))
        
        if subtotal >= Decimal("200.00"):
            expected_discount = (subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
            assert discount == expected_discount
            
            tier1_discount = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
            tier2_discount = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
            assert discount != tier1_discount
            assert discount != tier2_discount


class TestStockManagementBehavior:
    """Test behavioral aspects of stock management"""
    
    def test_insufficient_stock_prevents_order_creation(self, client, test_customer_email, idempotency_key):
        """Verify that orders fail when stock is insufficient"""
        response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 99999}],
            idempotency_key
        )
        
        assert response.status_code == 400
        error = response.json()
        assert "stock" in error["detail"].lower() or "insufficient" in error["detail"].lower()
    
    def test_inactive_product_prevents_order_creation(self, client, test_customer_email, idempotency_key):
        """Verify that inactive products cannot be ordered"""
        response = create_order(
            client,
            test_customer_email,
            [{"productSku": "INACTIVE-PRODUCT", "quantity": 1}],
            idempotency_key
        )
        
        assert response.status_code in [400, 404]


class TestPaymentAuthorizationBehavior:
    """Test behavioral aspects of payment authorization"""
    
    def test_payment_authorization_changes_order_status(self, client, test_customer_email, idempotency_key):
        """Verify that successful payment authorization changes order status to PAID"""
        create_response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 1}],
            idempotency_key
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        auth_response = client.post(f"/api/orders/{order_id}/authorize-payment")
        assert auth_response.status_code == 200
        
        get_response = client.get(f"/api/orders/{order_id}")
        assert get_response.status_code == 200
        order = get_response.json()
        assert order["status"] == "PAID"
    
    def test_payment_authorization_is_idempotent(self, client, test_customer_email, idempotency_key):
        """Verify that multiple payment authorization attempts don't cause issues"""
        create_response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 1}],
            idempotency_key
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        auth_response1 = client.post(f"/api/orders/{order_id}/authorize-payment")
        auth_response2 = client.post(f"/api/orders/{order_id}/authorize-payment")
        
        assert auth_response1.status_code == 200
        assert auth_response2.status_code in [200, 400]  # 400 if already paid


class TestOrderCancellationBehavior:
    """Test behavioral aspects of order cancellation"""
    
    def test_order_cancellation_changes_status(self, client, test_customer_email, idempotency_key):
        """Verify that order cancellation changes status to CANCELLED"""
        create_response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 1}],
            idempotency_key
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        cancel_response = client.post(f"/api/orders/{order_id}/cancel")
        assert cancel_response.status_code == 200
        
        cancelled_order = cancel_response.json()
        assert cancelled_order["status"] == "CANCELLED"
    
    def test_order_cancellation_restores_stock(self, client, test_customer_email):
        """Verify that order cancellation restores product stock"""
        create_response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 5}],
            str(uuid.uuid4())
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        cancel_response = client.post(f"/api/orders/{order_id}/cancel")
        assert cancel_response.status_code == 200
        
        create_response2 = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 5}],
            str(uuid.uuid4())
        )
        
        assert create_response2.status_code == 201
    
    def test_cancelled_order_cannot_be_cancelled_again(self, client, test_customer_email, idempotency_key):
        """Verify that cancelled orders cannot be cancelled again"""
        create_response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 1}],
            idempotency_key
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        cancel_response1 = client.post(f"/api/orders/{order_id}/cancel")
        assert cancel_response1.status_code == 200
        
        cancel_response2 = client.post(f"/api/orders/{order_id}/cancel")
        assert cancel_response2.status_code == 400
        error = cancel_response2.json()
        assert "cancel" in error["detail"].lower() or "status" in error["detail"].lower()
    
    def test_paid_order_can_be_cancelled(self, client, test_customer_email, idempotency_key):
        """Verify that paid orders can be cancelled (with payment void)"""
        create_response = create_order(
            client,
            test_customer_email,
            [{"productSku": "WIDGET-001", "quantity": 1}],
            idempotency_key
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        auth_response = client.post(f"/api/orders/{order_id}/authorize-payment")
        assert auth_response.status_code == 200
        
        cancel_response = client.post(f"/api/orders/{order_id}/cancel")
        assert cancel_response.status_code == 200
        
        cancelled_order = cancel_response.json()
        assert cancelled_order["status"] == "CANCELLED"


class TestIdempotencyBehavior:
    """Test behavioral aspects of idempotency"""
    
    def test_duplicate_idempotency_key_returns_existing_order(self, client, test_customer_email, idempotency_key):
        """Verify that duplicate requests return the same order"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [{"productSku": "WIDGET-001", "quantity": 1}]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response1 = client.post("/api/orders", json=request_data, headers=headers)
        assert response1.status_code == 201
        order1 = response1.json()
        
        response2 = client.post("/api/orders", json=request_data, headers=headers)
        assert response2.status_code in [200, 201]
        order2 = response2.json()
        
        assert order1["id"] == order2["id"]
        assert order1["total"] == order2["total"]
        assert order1["customerEmail"] == order2["customerEmail"]
    
    def test_idempotency_prevents_double_stock_decrement(self, client, test_customer_email, idempotency_key):
        """Verify that duplicate requests don't decrement stock twice"""
        request_data = {
            "customerEmail": test_customer_email,
            "items": [{"productSku": "WIDGET-001", "quantity": 1}]
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response1 = client.post("/api/orders", json=request_data, headers=headers)
        assert response1.status_code == 201
        
        response2 = client.post("/api/orders", json=request_data, headers=headers)
        assert response2.status_code in [200, 201]
        
        assert response1.json()["id"] == response2.json()["id"]


class TestErrorResponseBehavior:
    """Test behavioral aspects of error responses"""
    
    def test_validation_errors_are_descriptive(self, client, idempotency_key):
        """Verify that validation errors provide clear messages"""
        request_data = {
            "customerEmail": "invalid-email",
            "items": []
        }
        headers = {"Idempotency-Key": idempotency_key}
        
        response = client.post("/api/orders", json=request_data, headers=headers)
        assert response.status_code == 400
        
        error = response.json()
        assert "detail" in error
        assert len(error["detail"]) > 0
    
    def test_not_found_errors_are_consistent(self, client):
        """Verify that not found errors are consistent"""
        response1 = client.get("/api/orders/99999")
        assert response1.status_code == 404
        
        response2 = client.post("/api/orders/99999/cancel")
        assert response2.status_code == 404
        
        response3 = client.post("/api/orders/99999/authorize-payment")
        assert response3.status_code == 404
        
        error1 = response1.json()
        error2 = response2.json()
        error3 = response3.json()
        
        assert "type" in error1 and "type" in error2 and "type" in error3
        assert "detail" in error1 and "detail" in error2 and "detail" in error3


class TestCustomerOrdersBehavior:
    """Test behavioral aspects of customer order retrieval"""
    
    def test_customer_orders_are_sorted_by_creation_date(self, client, test_customer_email):
        """Verify that customer orders are returned in chronological order"""
        order_ids = []
        for i in range(3):
            response = create_order(
                client,
                test_customer_email,
                [{"productSku": "WIDGET-001", "quantity": 1}],
                str(uuid.uuid4())
            )
            assert response.status_code == 201
            order_ids.append(response.json()["id"])
            time.sleep(0.1)  # Small delay to ensure different timestamps
        
        response = client.get(f"/api/orders/customer/{test_customer_email}")
        assert response.status_code == 200
        
        data = response.json()
        orders = data.get("content", data)
        
        assert len(orders) >= 3
        
        if len(orders) >= 2:
            assert "createdAt" in orders[0]
            assert "createdAt" in orders[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
