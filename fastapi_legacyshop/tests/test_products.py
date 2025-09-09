from fastapi import status

def test_products_crud_min(client):
    r = client.get("/api/products")
    assert r.status_code == status.HTTP_200_OK
    r1 = client.post("/api/products", json={"sku":"DUP-1","name":"X","price":1.23,"stock_quantity":5,"active":True})
    assert r1.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
    r2 = client.post("/api/products", json={"sku":"DUP-1","name":"Y","price":2.34,"stock_quantity":3,"active":True})
    assert r2.status_code == status.HTTP_409_CONFLICT
