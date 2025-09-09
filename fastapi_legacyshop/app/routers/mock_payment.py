from fastapi import APIRouter, Request
from uuid import uuid4
from .dev_inject import pop_next_failure

router = APIRouter()

@router.post("/mock/payment/authorize")
def authorize(req: Request):
    nxt = pop_next_failure()
    if nxt:
        return {"error": "Payment service temporarily unavailable"}, nxt
    data = {}
    try:
        data = req.json()
    except Exception:
        data = {}
    try:
        amount = float(str(data.get("amount", "0")))
    except Exception:
        amount = 0.0
    if amount < 0.01:
        return {"error": "Amount must be at least 0.01"}, 400
    if amount > 1000:
        return {"error": "Insufficient funds"}, 402
    auth_id = "AUTH_" + uuid4().hex
    return {"authorizationId": auth_id, "status": "AUTHORIZED", "amount": f"{amount:.2f}"}

@router.post("/mock/payment/void")
def void(req: Request):
    nxt = pop_next_failure()
    if nxt:
        return {"error": "Void service temporarily unavailable"}, nxt
    data = {}
    try:
        data = req.json()
    except Exception:
        data = {}
    authorization_id = data.get("authorizationId")
    if not authorization_id:
        return {"error": "Authorization ID is required"}, 400
    return {"authorizationId": authorization_id, "status": "VOIDED"}
