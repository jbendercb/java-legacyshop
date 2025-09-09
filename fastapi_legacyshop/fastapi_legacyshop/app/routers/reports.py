from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.schemas.report import OrderReportResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/orders", response_model=List[OrderReportResponse])
async def get_order_reports(
    start_date: Optional[date] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Order status filter"),
    page: int = Query(0, ge=0, description="Page number (0-based)"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    return await service.get_order_reports(start_date, end_date, status, page, size)
