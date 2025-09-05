from fastapi import status

def test_payment_retry_once_then_success(client):
    body = {
        "customerEmail": "eve@example.com",
        "items": [{"productSku": "SKU-001", "quantity": 1}],
    }
    r = client.post("/api/orders", json=body)
    assert r.status_code == status.HTTP_201_CREATED
    order_id = r.json()["id"]

    inj = client.post("/_admin/payment/next_failure", params={"code": 500})
    assert inj.status_code == 200

    p = client.post(f"/api/orders/{order_id}/authorize-payment")
    assert p.status_code == 200
    data = p.json()
    assert data["status"] == "AUTHORIZED"
