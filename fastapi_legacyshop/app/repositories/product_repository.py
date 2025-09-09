from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.product import Product

def get_by_sku(db: Session, sku: str):
    return db.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()

def search_by_name(db: Session, name: str, page: int, size: int):
    q = db.query(Product).filter(Product.name.ilike(f"%{name}%")).order_by(Product.name.asc())
    return q.offset((page - 1) * size).limit(size).all()

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.product import Product

def list_products(db: Session, skip: int = 0, limit: int = 50):
    return db.query(Product).offset(skip).limit(limit).all()

def get_by_id(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)

def get_by_sku(db: Session, sku: str) -> Product | None:
    return db.query(Product).filter(Product.sku == sku).first()

def create(db: Session, data: dict) -> Product:
    p = Product(**data)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def update(db: Session, p: Product, data: dict) -> Product:
    for k, v in data.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p

def delete(db: Session, p: Product):
    db.delete(p)
    db.commit()
