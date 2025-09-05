from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..schemas.product import ProductCreate, ProductUpdate, ProductOut
from ..repositories import product_repository as repo
from ..utils.problem_details import DuplicateResourceError, ResourceNotFoundError

router = APIRouter()

@router.get("/products", response_model=list[ProductOut])
def list_products(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return repo.list_products(db, skip=skip, limit=limit)

@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = repo.get_by_id(db, product_id)
    if not p:
        raise ResourceNotFoundError(f"Product {product_id} not found")
    return p

@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(body: ProductCreate, db: Session = Depends(get_db)):
    existing = repo.get_by_sku(db, body.sku)
    if existing:
        raise DuplicateResourceError(f"Product with SKU {body.sku} already exists")
    return repo.create(db, body.model_dump())

@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, body: ProductUpdate, db: Session = Depends(get_db)):
    p = repo.get_by_id(db, product_id)
    if not p:
        raise ResourceNotFoundError(f"Product {product_id} not found")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return repo.update(db, p, data)

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    p = repo.get_by_id(db, product_id)
    if not p:
        raise ResourceNotFoundError(f"Product {product_id} not found")
    repo.delete(db, p)
    return None
