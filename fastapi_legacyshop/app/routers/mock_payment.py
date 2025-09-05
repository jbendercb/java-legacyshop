from fastapi import APIRouter

router = APIRouter()

@router.post("/payment/authorize")
def authorize():
    return {"authorized": True}
