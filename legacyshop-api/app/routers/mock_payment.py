"""
Mock payment service endpoint for testing.
This simulates an external payment gateway.
"""

from fastapi import APIRouter
import uuid

router = APIRouter(prefix="/mock/payment", tags=["mock"])


@router.post("/authorize")
async def authorize_payment(request: dict):
    """
    Mock payment authorization endpoint.
    Returns a fake authorization ID.
    """
    return {
        "authorizationId": f"AUTH-{uuid.uuid4().hex[:12].upper()}",
        "status": "AUTHORIZED",
        "amount": request.get("amount", "0.00"),
        "currency": request.get("currency", "USD")
    }
