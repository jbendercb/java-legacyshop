import pytest
from decimal import Decimal
from fastapi.testclient import TestClient


def test_create_product(client: TestClient):
    product_data = {
        "sku": "TEST-001",
        "name": "Test Product",
        "description": "A test product",
        "price": "29.99",
        "stock_quantity": 100
    }
    
    response = client.post("/api/products/", json=product_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["sku"] == "TEST-001"
    assert data["name"] == "Test Product"
    assert data["price"] == "29.99"
    assert data["stock_quantity"] == 100


def test_get_products(client: TestClient, sample_product):
    response = client.get("/api/products/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["sku"] == "TEST-001"


def test_get_product_by_id(client: TestClient, sample_product):
    response = client.get(f"/api/products/{sample_product.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["sku"] == "TEST-001"
    assert data["name"] == "Test Product"


def test_get_product_not_found(client: TestClient):
    response = client.get("/api/products/999")
    assert response.status_code == 404
    
    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "ProductNotFoundError"
    assert data["status"] == 404


def test_update_product(client: TestClient, sample_product):
    update_data = {
        "name": "Updated Product",
        "price": "39.99"
    }
    
    response = client.put(f"/api/products/{sample_product.id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Product"
    assert data["price"] == "39.99"


def test_delete_product(client: TestClient, sample_product):
    response = client.delete(f"/api/products/{sample_product.id}")
    assert response.status_code == 204
    
    get_response = client.get(f"/api/products/{sample_product.id}")
    assert get_response.status_code == 404


def test_search_product_by_sku(client: TestClient, sample_product):
    response = client.get("/api/products/search/by-sku/TEST-001")
    assert response.status_code == 200
    
    data = response.json()
    assert data["sku"] == "TEST-001"


def test_search_products_by_name(client: TestClient, sample_product):
    response = client.get("/api/products/search/by-name?name=Test")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Product"


def test_create_product_duplicate_sku(client: TestClient, sample_product):
    product_data = {
        "sku": "TEST-001",  # Same SKU as sample_product
        "name": "Another Product",
        "description": "Another test product",
        "price": "19.99",
        "stock_quantity": 50
    }
    
    response = client.post("/api/products/", json=product_data)
    assert response.status_code == 409
    
    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "ProductAlreadyExistsError"
    assert data["status"] == 409
