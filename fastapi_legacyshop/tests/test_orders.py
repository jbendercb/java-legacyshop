import pytest
from decimal import Decimal
from fastapi.testclient import TestClient


def test_create_order(client: TestClient, sample_product, sample_customer):
    order_data = {
        "customer_email": sample_customer.email,
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 2
            }
        ]
    }
    
    headers = {"Idempotency-Key": "test-key-001"}
    response = client.post("/api/orders/", json=order_data, headers=headers)
    assert response.status_code == 201
    
    data = response.json()
    assert data["customer_email"] == sample_customer.email
    assert data["status"] == "PENDING"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["subtotal"] == "59.98"  # 2 * 29.99


def test_create_order_idempotency(client: TestClient, sample_product, sample_customer):
    order_data = {
        "customer_email": sample_customer.email,
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 1
            }
        ]
    }
    
    headers = {"Idempotency-Key": "test-key-002"}
    
    response1 = client.post("/api/orders/", json=order_data, headers=headers)
    assert response1.status_code == 201
    
    response2 = client.post("/api/orders/", json=order_data, headers=headers)
    assert response2.status_code == 200  # Should return existing order
    
    data1 = response1.json()
    data2 = response2.json()
    assert data1["id"] == data2["id"]
    assert data1["total"] == data2["total"]


def test_create_order_insufficient_stock(client: TestClient, sample_product, sample_customer):
    order_data = {
        "customer_email": sample_customer.email,
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 150  # More than available stock (100)
            }
        ]
    }
    
    headers = {"Idempotency-Key": "test-key-003"}
    response = client.post("/api/orders/", json=order_data, headers=headers)
    assert response.status_code == 409
    
    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "InsufficientStockError"
    assert data["status"] == 409


def test_get_order(client: TestClient, sample_product, sample_customer):
    order_data = {
        "customer_email": sample_customer.email,
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 1
            }
        ]
    }
    
    headers = {"Idempotency-Key": "test-key-004"}
    create_response = client.post("/api/orders/", json=order_data, headers=headers)
    order_id = create_response.json()["id"]
    
    response = client.get(f"/api/orders/{order_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == order_id
    assert data["customer_email"] == sample_customer.email


def test_get_customer_orders(client: TestClient, sample_product, sample_customer):
    order_data = {
        "customer_email": sample_customer.email,
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 1
            }
        ]
    }
    
    headers = {"Idempotency-Key": "test-key-005"}
    client.post("/api/orders/", json=order_data, headers=headers)
    
    response = client.get(f"/api/orders/customer/{sample_customer.email}")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["customer_email"] == sample_customer.email


def test_cancel_order(client: TestClient, sample_product, sample_customer):
    order_data = {
        "customer_email": sample_customer.email,
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 2
            }
        ]
    }
    
    headers = {"Idempotency-Key": "test-key-006"}
    create_response = client.post("/api/orders/", json=order_data, headers=headers)
    order_id = create_response.json()["id"]
    
    product_response = client.get(f"/api/products/{sample_product.id}")
    initial_stock = product_response.json()["stock_quantity"]
    assert initial_stock == 98  # 100 - 2
    
    cancel_response = client.post(f"/api/orders/{order_id}/cancel")
    assert cancel_response.status_code == 200
    
    data = cancel_response.json()
    assert data["status"] == "CANCELLED"
    
    product_response = client.get(f"/api/products/{sample_product.id}")
    final_stock = product_response.json()["stock_quantity"]
    assert final_stock == 100  # Stock should be restored


def test_order_discount_calculation(client: TestClient, sample_product, sample_customer):
    high_value_product_data = {
        "sku": "HIGH-001",
        "name": "High Value Product",
        "description": "Expensive product for discount testing",
        "price": "150.00",
        "stock_quantity": 10
    }
    
    create_response = client.post("/api/products/", json=high_value_product_data)
    high_value_product_id = create_response.json()["id"]
    
    order_data = {
        "customer_email": sample_customer.email,
        "items": [
            {
                "product_id": high_value_product_id,
                "quantity": 2  # Total: $300, should get 15% discount
            }
        ]
    }
    
    headers = {"Idempotency-Key": "test-key-007"}
    response = client.post("/api/orders/", json=order_data, headers=headers)
    assert response.status_code == 201
    
    data = response.json()
    assert data["subtotal"] == "300.00"
    assert data["discount_amount"] == "45.00"  # 15% of 300
    assert data["total"] == "255.00"  # 300 - 45
