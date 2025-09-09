import pytest
from fastapi.testclient import TestClient
from datetime import date


def test_get_order_reports_empty(client: TestClient):
    response = client.get("/api/reports/orders")
    assert response.status_code == 200
    
    data = response.json()
    assert data == []


def test_get_order_reports_with_data(client: TestClient, sample_product, sample_customer):
    order_data = {
        "customer_email": sample_customer.email,
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 1
            }
        ]
    }
    
    headers = {"Idempotency-Key": "test-report-001"}
    client.post("/api/orders/", json=order_data, headers=headers)
    
    response = client.get("/api/reports/orders")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["customer_email"] == sample_customer.email
    assert data[0]["order_status"] == "PENDING"
    assert data[0]["subtotal"] == "29.99"


def test_get_order_reports_with_pagination(client: TestClient, sample_product, sample_customer):
    for i in range(5):
        order_data = {
            "customer_email": sample_customer.email,
            "items": [
                {
                    "product_id": sample_product.id,
                    "quantity": 1
                }
            ]
        }
        
        headers = {"Idempotency-Key": f"test-report-{i:03d}"}
        client.post("/api/orders/", json=order_data, headers=headers)
    
    response = client.get("/api/reports/orders?page=0&size=3")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    
    response = client.get("/api/reports/orders?page=1&size=3")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2


def test_get_order_reports_with_status_filter(client: TestClient, sample_product, sample_customer):
    order_data = {
        "customer_email": sample_customer.email,
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 1
            }
        ]
    }
    
    headers = {"Idempotency-Key": "test-report-cancel"}
    create_response = client.post("/api/orders/", json=order_data, headers=headers)
    order_id = create_response.json()["id"]
    
    client.post(f"/api/orders/{order_id}/cancel")
    
    response = client.get("/api/reports/orders?status=CANCELLED")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["order_status"] == "CANCELLED"
    
    response = client.get("/api/reports/orders?status=PENDING")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 0
