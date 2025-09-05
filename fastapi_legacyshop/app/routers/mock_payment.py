from fastapi import APIRouter, Request
from .dev_inject import pop_next_failure
from ..config import settings

router = APIRouter()

@router.post("/mock/payment/authorize")
def authorize(req: Request):
    nxt = pop_next_failure()
    if nxt:
        return {"error": "injected"}, nxt
    data = None
    try:
        data = req.json()
    except Exception:
        pass
    amount = 0
    if isinstance(data, dict):
        try:
            amount = float(data.get("amount", "0"))
        except Exception:
            amount = 0
    if amount > 1000:
        return {"error": "limit"}, 402
    return {"authorized": True, "authId": "mock-auth"}
