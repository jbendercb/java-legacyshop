from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services import report_service as svc

router = APIRouter()

@router.get("/reports")
def get_reports(
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return svc.list_orders(db, startDate, endDate, page, pageSize)

@router.get("/reports/orders")
def list_orders_range(
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return svc.list_orders(db, startDate, endDate, page, size)

@router.get("/reports/orders/today")
def list_orders_today(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    start, end = svc.today_range()
    return svc.list_orders(db, start.isoformat(), end.isoformat(), page, size)

@router.get("/reports/orders/last-30-days")
def list_orders_last_30(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    start, end = svc.last_30_days_range()
    return svc.list_orders(db, start.isoformat(), end.isoformat(), page, size)

@router.get("/reports/orders/current-month")
def list_orders_current_month(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    start, end = svc.current_month_range()
    return svc.list_orders(db, start.isoformat(), end.isoformat(), page, size)
