from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import products, orders, admin, reports, mock_payment
from app.scheduler import start_scheduler, stop_scheduler
from app.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="LegacyShop API",
    description="FastAPI migration of Java Spring Boot LegacyShop monolith",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(mock_payment.router, prefix="/mock/payment", tags=["mock-payment"])


@app.get("/")
async def root():
    return {"message": "LegacyShop FastAPI - Migrated from Java Spring Boot"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
