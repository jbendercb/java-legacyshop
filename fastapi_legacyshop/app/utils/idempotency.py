import hashlib
import json
from decimal import Decimal
from typing import Any

def normalize(obj: Any):
    if isinstance(obj, dict):
        return {k: normalize(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [normalize(x) for x in obj]
    if isinstance(obj, Decimal):
        return f"{obj.quantize(Decimal('0.01'))}"
    return obj

def canonicalize_request(data: Any) -> str:
    norm = normalize(data)
    return json.dumps(norm, separators=(",", ":"), sort_keys=True)

def compute_request_hash(canonical_json: str) -> str:
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
