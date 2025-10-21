"""
Database configuration and session management.
Uses SQLite in-memory database for testing/development.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./legacyshop.db?check_same_thread=False"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    poolclass=None
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with schema and test data"""
    from app.models import models  # Import here to avoid circular imports
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        existing_count = db.query(models.Product).count()
        if existing_count > 0:
            return
        
        products = [
            models.Product(
                sku="WIDGET-001",
                name="Premium Widget",
                price=10.00,
                stock_quantity=1000,
                active=True
            ),
            models.Product(
                sku="GADGET-002",
                name="Super Gadget",
                price=25.00,
                stock_quantity=500,
                active=True
            ),
            models.Product(
                sku="TOOL-003",
                name="Mega Tool",
                price=50.00,
                stock_quantity=250,
                active=True
            ),
            models.Product(
                sku="INACTIVE-PRODUCT",
                name="Inactive Product",
                price=100.00,
                stock_quantity=100,
                active=False
            ),
        ]
        
        for product in products:
            db.add(product)
        
        db.commit()
    finally:
        db.close()
