from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.inventory_service import InventoryService
from app.services.loyalty_service import LoyaltyService

router = APIRouter()


@router.post("/trigger-replenishment", status_code=200)
async def trigger_replenishment(
    db: Session = Depends(get_db)
):
    service = InventoryService(db)
    await service.replenish_inventory()
    return {"message": "Inventory replenishment triggered successfully"}


@router.post("/trigger-loyalty", status_code=200)
async def trigger_loyalty(
    db: Session = Depends(get_db)
):
    service = LoyaltyService(db)
    await service.process_loyalty_points()
    return {"message": "Loyalty processing triggered successfully"}


@router.post("/replenish-product/{product_id}", status_code=200)
async def replenish_product(
    product_id: int,
    quantity: int = 100,
    db: Session = Depends(get_db)
):
    service = InventoryService(db)
    await service.replenish_product(product_id, quantity)
    return {"message": f"Product {product_id} replenished successfully"}
