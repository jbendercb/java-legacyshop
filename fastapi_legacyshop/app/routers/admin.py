from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services.inventory_service import replenish_low_stock
from ..services.loyalty_service import process_loyalty

router = APIRouter()

@router.post("/trigger-replenishment")
def trigger_replenishment(db: Session = Depends(get_db)):
    return replenish_low_stock(db)

@router.post("/trigger-loyalty-processing")
def trigger_loyalty(db: Session = Depends(get_db)):
    return process_loyalty(db)
