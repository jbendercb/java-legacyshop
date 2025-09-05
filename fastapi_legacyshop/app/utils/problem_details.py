from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class BusinessValidationError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class ResourceNotFoundError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class DuplicateResourceError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class PaymentError(Exception):
    def __init__(self, detail: str, retryable: bool):
        self.detail = detail
        self.retryable = retryable

def _problem(title: str, status: int, detail: str, type_: str, extra: dict | None = None):
    body = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
    }
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status, content=body)

def register_problem_handlers(app: FastAPI):
    @app.exception_handler(BusinessValidationError)
    async def handle_business(_: Request, exc: BusinessValidationError):
        return _problem("Business Rule Violation", 400, exc.detail, "/problems/business-validation-error")

    @app.exception_handler(ResourceNotFoundError)
    async def handle_not_found(_: Request, exc: ResourceNotFoundError):
        return _problem("Resource Not Found", 404, exc.detail, "/problems/resource-not-found")

    @app.exception_handler(DuplicateResourceError)
    async def handle_duplicate(_: Request, exc: DuplicateResourceError):
        return _problem("Resource Already Exists", 409, exc.detail, "/problems/duplicate-resource")

    @app.exception_handler(PaymentError)
    async def handle_payment(_: Request, exc: PaymentError):
        if exc.retryable:
            return _problem("External Service Unavailable", 502, exc.detail, "/problems/payment-error", {"retryable": True})
        return _problem("Payment Failed", 400, exc.detail, "/problems/payment-error", {"retryable": False})
