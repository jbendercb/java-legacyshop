from fastapi import APIRouter

router = APIRouter()

@router.post("/orders")
def create_order():
    return {"status": "placeholder"}
