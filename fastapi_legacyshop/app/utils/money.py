from decimal import Decimal, ROUND_HALF_UP, getcontext

TWOPLACES = Decimal(".01")

def quantize_2(value: Decimal | str | float | int) -> Decimal:
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
