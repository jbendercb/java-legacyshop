from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    return await service.create_product(product)


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    page: int = Query(0, ge=0, description="Page number (0-based)"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    return await service.get_products(page, size)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    return await service.get_product(product_id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    return await service.update_product(product_id, product)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    await service.delete_product(product_id)


@router.get("/search/by-sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(
    sku: str,
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    return await service.get_product_by_sku(sku)


@router.get("/search/by-name", response_model=List[ProductResponse])
async def search_products_by_name(
    name: str = Query(..., min_length=1, description="Product name to search for"),
    page: int = Query(0, ge=0, description="Page number (0-based)"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    return await service.search_products_by_name(name, page, size)
