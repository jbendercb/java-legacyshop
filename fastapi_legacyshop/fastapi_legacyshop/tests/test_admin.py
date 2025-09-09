import pytest
from fastapi.testclient import TestClient


def test_trigger_replenishment(client: TestClient):
    response = client.post("/api/admin/trigger-replenishment")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Inventory replenishment triggered successfully"


def test_trigger_loyalty(client: TestClient):
    response = client.post("/api/admin/trigger-loyalty")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Loyalty processing triggered successfully"


def test_replenish_product(client: TestClient, sample_product):
    update_data = {"stock_quantity": 5}
    client.put(f"/api/products/{sample_product.id}", json=update_data)
    
    response = client.post(f"/api/admin/replenish-product/{sample_product.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == f"Product {sample_product.id} replenished successfully"
    
    product_response = client.get(f"/api/products/{sample_product.id}")
    product_data = product_response.json()
    assert product_data["stock_quantity"] == 105  # 5 + 100 (default restock)


def test_replenish_nonexistent_product(client: TestClient):
    response = client.post("/api/admin/replenish-product/999")
    assert response.status_code == 404
    
    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "ProductNotFoundError"
    assert data["status"] == 404
