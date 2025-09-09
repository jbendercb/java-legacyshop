from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.exceptions import ProductNotFoundError, ProductAlreadyExistsError


class ProductService:
    def __init__(self, db: Session):
        self.db = db

    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        existing = self.db.query(Product).filter(Product.sku == product_data.sku).first()
        if existing:
            raise ProductAlreadyExistsError(f"Product with SKU '{product_data.sku}' already exists")

        product = Product(**product_data.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return ProductResponse.model_validate(product)

    async def get_products(self, page: int = 0, size: int = 20) -> List[ProductResponse]:
        offset = page * size
        products = self.db.query(Product).offset(offset).limit(size).all()
        return [ProductResponse.model_validate(p) for p in products]

    async def get_product(self, product_id: int) -> ProductResponse:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")
        return ProductResponse.model_validate(product)

    async def get_product_by_sku(self, sku: str) -> ProductResponse:
        product = self.db.query(Product).filter(Product.sku == sku).first()
        if not product:
            raise ProductNotFoundError(f"Product with SKU '{sku}' not found")
        return ProductResponse.model_validate(product)

    async def search_products_by_name(self, name: str, page: int = 0, size: int = 20) -> List[ProductResponse]:
        offset = page * size
        products = (
            self.db.query(Product)
            .filter(Product.name.ilike(f"%{name}%"))
            .offset(offset)
            .limit(size)
            .all()
        )
        return [ProductResponse.model_validate(p) for p in products]

    async def update_product(self, product_id: int, product_data: ProductUpdate) -> ProductResponse:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")

        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)
        return ProductResponse.model_validate(product)

    async def delete_product(self, product_id: int):
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")

        self.db.delete(product)
        self.db.commit()
