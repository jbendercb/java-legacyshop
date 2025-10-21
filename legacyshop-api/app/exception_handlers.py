"""
Global exception handlers that produce RFC-7807 Problem Details responses.
Mirrors the Java GlobalExceptionHandler implementation.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.services.exceptions import (
    BusinessValidationException,
    ResourceNotFoundException,
    DuplicateResourceException,
    PaymentException
)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors (400 Bad Request)"""
    field_errors = {}
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])  # Skip 'body'
        field_errors[field] = error["msg"]
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "type": "/problems/validation-error",
            "title": "Validation Failed",
            "status": 400,
            "detail": "One or more fields have invalid values",
            "fieldErrors": field_errors
        }
    )


async def business_validation_exception_handler(request: Request, exc: BusinessValidationException):
    """Handle business validation errors (400 Bad Request)"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "type": "/problems/business-validation-error",
            "title": "Business Rule Violation",
            "status": 400,
            "detail": str(exc)
        }
    )


async def resource_not_found_exception_handler(request: Request, exc: ResourceNotFoundException):
    """Handle resource not found errors (404 Not Found)"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "type": "/problems/resource-not-found",
            "title": "Resource Not Found",
            "status": 404,
            "detail": str(exc)
        }
    )


async def duplicate_resource_exception_handler(request: Request, exc: DuplicateResourceException):
    """Handle duplicate resource errors (409 Conflict)"""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "type": "/problems/duplicate-resource",
            "title": "Resource Already Exists",
            "status": 409,
            "detail": str(exc)
        }
    )


async def payment_exception_handler(request: Request, exc: PaymentException):
    """Handle payment service errors (502 Bad Gateway or 400 Bad Request)"""
    status_code = status.HTTP_502_BAD_GATEWAY if exc.retryable else status.HTTP_400_BAD_REQUEST
    title = "External Service Unavailable" if exc.retryable else "Payment Failed"
    
    return JSONResponse(
        status_code=status_code,
        content={
            "type": "/problems/payment-error",
            "title": title,
            "status": status_code,
            "detail": str(exc),
            "retryable": exc.retryable
        }
    )


async def illegal_state_exception_handler(request: Request, exc: ValueError):
    """Handle illegal state errors (400 Bad Request)"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "type": "/problems/invalid-state",
            "title": "Invalid State",
            "status": 400,
            "detail": str(exc)
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors (500 Internal Server Error)"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "/problems/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred"
        }
    )
