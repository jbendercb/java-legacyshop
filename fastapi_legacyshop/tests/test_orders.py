from fastapi import status

def test_order_idempotency(client):
    body = {
        "customerEmail": "alice@example.com",
        "items": [{"productSku": "SKU-001", "quantity": 2}],
    }
    headers = {"Idempotency-Key": "idem-abc-123"}
    r1 = client.post("/api/orders", json=body, headers=headers)
    assert r1.status_code == status.HTTP_201_CREATED
    data1 = r1.json()
    r2 = client.post("/api/orders", json=body, headers=headers)
    assert r2.status_code in (status.HTTP_200_OK, status.HTTP_208_ALREADY_REPORTED)
    data2 = r2.json()
    assert data1 == data2

def test_order_idempotency_conflict(client):
    b1 = {"customerEmail": "bob@example.com", "items": [{"productSku": "SKU-001", "quantity": 1}]}
    b2 = {"customerEmail": "bob@example.com", "items": [{"productSku": "SKU-002", "quantity": 1}]}
    headers = {"Idempotency-Key": "idem-conflict-1"}
    r1 = client.post("/api/orders", json=b1, headers=headers)
    assert r1.status_code == status.HTTP_201_CREATED
    r2 = client.post("/api/orders", json=b2, headers=headers)
    assert r2.status_code == status.HTTP_409_CONFLICT
    pd = r2.json()
    assert pd["title"] == "Resource Already Exists"
