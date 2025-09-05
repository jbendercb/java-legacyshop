from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services.report_service import list_orders

router = APIRouter()

@router.get("/reports")
def get_reports(
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return list_orders(db, startDate, endDate, page, pageSize)
