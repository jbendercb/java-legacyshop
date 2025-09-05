from decimal import Decimal
from ..config import settings
from ..utils.money import quantize_2

def calculate_discount(subtotal: Decimal) -> Decimal:
    tiers = settings.PROMOTION_TIERS or []
    subtotal = quantize_2(subtotal)
    best = Decimal("0.00")
    for t in tiers:
        threshold = Decimal(str(t.get("threshold", "0")))
        rate = Decimal(str(t.get("rate", "0")))
        if subtotal >= threshold:
            d = quantize_2(subtotal * rate)
            if d > best:
                best = d
    return best
