from fastapi import APIRouter

router = APIRouter()

@router.post("/trigger-replenishment")
def trigger_replenishment():
    return {"ok": True}

@router.post("/trigger-loyalty-processing")
def trigger_loyalty():
    return {"ok": True}
