from decimal import Decimal
from app.config import settings


class DiscountService:
    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        applicable_discount = Decimal("0.00")
        
        for tier in sorted(settings.promotions.discount_tiers, key=lambda x: x.threshold, reverse=True):
            if subtotal >= tier.threshold:
                applicable_discount = subtotal * tier.percentage
                break
        
        return applicable_discount
