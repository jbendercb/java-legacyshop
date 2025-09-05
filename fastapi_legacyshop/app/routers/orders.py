from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..schemas.order import OrderCreate, OrderOut
from ..services.order_service import create_order as svc_create
from ..services.payment_service import authorize_payment as svc_authorize

router = APIRouter()

@router.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(body: OrderCreate, db: Session = Depends(get_db), Idempotency_Key: str | None = Header(default=None, convert_underscores=False)):
    resp, code = svc_create(db, body, Idempotency_Key)
    return resp

@router.post("/orders/{order_id}/authorize-payment")
def authorize_payment(order_id: int, db: Session = Depends(get_db)):
    return svc_authorize(db, order_id)
