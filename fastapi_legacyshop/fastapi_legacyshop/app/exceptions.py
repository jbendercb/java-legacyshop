from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class LegacyShopException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ProductNotFoundError(LegacyShopException):
    def __init__(self, message: str):
        super().__init__(message, 404)


class ProductAlreadyExistsError(LegacyShopException):
    def __init__(self, message: str):
        super().__init__(message, 409)


class OrderNotFoundError(LegacyShopException):
    def __init__(self, message: str):
        super().__init__(message, 404)


class InsufficientStockError(LegacyShopException):
    def __init__(self, message: str):
        super().__init__(message, 409)


class BusinessValidationError(LegacyShopException):
    def __init__(self, message: str):
        super().__init__(message, 400)


class PaymentError(LegacyShopException):
    def __init__(self, message: str):
        super().__init__(message, 400)


class PaymentGatewayError(LegacyShopException):
    def __init__(self, message: str):
        super().__init__(message, 502)


def create_problem_details(title: str, detail: str, status: int, instance: str = None) -> dict:
    problem = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail
    }
    if instance:
        problem["instance"] = instance
    return problem


def setup_exception_handlers(app: FastAPI):
    
    @app.exception_handler(LegacyShopException)
    async def legacy_shop_exception_handler(request: Request, exc: LegacyShopException):
        problem_details = create_problem_details(
            title=exc.__class__.__name__,
            detail=exc.message,
            status=exc.status_code,
            instance=str(request.url)
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem_details,
            headers={"Content-Type": "application/problem+json"}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        problem_details = create_problem_details(
            title="Validation Error",
            detail=f"Request validation failed: {str(exc)}",
            status=400,
            instance=str(request.url)
        )
        return JSONResponse(
            status_code=400,
            content=problem_details,
            headers={"Content-Type": "application/problem+json"}
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        problem_details = create_problem_details(
            title="Validation Error",
            detail=f"Data validation failed: {str(exc)}",
            status=400,
            instance=str(request.url)
        )
        return JSONResponse(
            status_code=400,
            content=problem_details,
            headers={"Content-Type": "application/problem+json"}
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        problem_details = create_problem_details(
            title="HTTP Error",
            detail=exc.detail,
            status=exc.status_code,
            instance=str(request.url)
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem_details,
            headers={"Content-Type": "application/problem+json"}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        problem_details = create_problem_details(
            title="Internal Server Error",
            detail="An unexpected error occurred",
            status=500,
            instance=str(request.url)
        )
        return JSONResponse(
            status_code=500,
            content=problem_details,
            headers={"Content-Type": "application/problem+json"}
        )
