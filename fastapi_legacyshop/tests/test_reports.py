from fastapi import status

def test_reports_basic(client):
    r = client.get("/api/reports?page=1&pageSize=10")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert "orders" in data
    assert "total" in data
