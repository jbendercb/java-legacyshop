from sqlalchemy.orm import Session
from ..models.idempotency import IdempotencyRecord

def get(db: Session, key: str) -> IdempotencyRecord | None:
    return db.get(IdempotencyRecord, key)

def save(db: Session, record: IdempotencyRecord):
    db.add(record)
    db.commit()
