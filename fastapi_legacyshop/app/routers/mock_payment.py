from fastapi import APIRouter

router = APIRouter()

@router.post("/mock/payment/authorize")
def authorize():
    return {"authorized": True}
