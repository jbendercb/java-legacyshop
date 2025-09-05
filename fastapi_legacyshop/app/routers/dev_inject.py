from fastapi import APIRouter, Query

router = APIRouter()

_next_failure_code: int | None = None

@router.post("/payment/next_failure")
def next_failure(code: int = Query(500, ge=400, le=599)):
    global _next_failure_code
    _next_failure_code = code
    return {"scheduled": code}

def pop_next_failure() -> int | None:
    global _next_failure_code
    val = _next_failure_code
    _next_failure_code = None
    return val
