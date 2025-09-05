import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from ..config import settings
from ..models.product import Product

def main():
    if not (settings.APP_ENV == "test" or str(os.getenv("SEED", "false")).lower() == "true"):
        print("Seeding skipped. Set APP_ENV=test or SEED=true to enable.")
        return
    engine = create_engine(settings.DATABASE_URL, future=True)
    with Session(engine) as db:
        if not db.query(Product).first():
            db.add_all([
                Product(sku="SKU-001", name="Widget A", price=9.99, stock_quantity=100, active=True),
                Product(sku="SKU-002", name="Widget B", price=19.99, stock_quantity=50, active=True),
                Product(sku="SKU-003", name="Gadget C", price=5.49, stock_quantity=200, active=True),
            ])
            db.commit()
    print("Seeding complete.")

if __name__ == "__main__":
    main()
