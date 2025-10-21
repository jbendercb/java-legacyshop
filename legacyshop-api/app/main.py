from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.database import init_db
from app.routers import orders, mock_payment
from app.exception_handlers import (
    validation_exception_handler,
    business_validation_exception_handler,
    resource_not_found_exception_handler,
    duplicate_resource_exception_handler,
    payment_exception_handler,
    illegal_state_exception_handler,
    generic_exception_handler
)
from app.services.exceptions import (
    BusinessValidationException,
    ResourceNotFoundException,
    DuplicateResourceException,
    PaymentException
)

app = FastAPI(title="LegacyShop Order Management API")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(BusinessValidationException, business_validation_exception_handler)
app.add_exception_handler(ResourceNotFoundException, resource_not_found_exception_handler)
app.add_exception_handler(DuplicateResourceException, duplicate_resource_exception_handler)
app.add_exception_handler(PaymentException, payment_exception_handler)
app.add_exception_handler(ValueError, illegal_state_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(orders.router)
app.include_router(mock_payment.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
