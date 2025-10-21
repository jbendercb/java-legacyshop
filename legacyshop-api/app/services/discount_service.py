"""
Discount calculation service.
Implements tiered discount logic matching the Java implementation.
"""

from decimal import Decimal, ROUND_HALF_UP
from app.config.business_config import config


class DiscountService:
    """Service for calculating discounts based on order subtotal"""
    
    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        """
        Calculate discount amount based on order subtotal.
        Uses tiered discount structure from configuration.
        
        Returns the discount amount (not the rate).
        """
        if subtotal is None:
            return Decimal("0.00").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        if subtotal >= config.tier3_threshold:
            discount = (subtotal * config.tier3_discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return discount
        
        if subtotal >= config.tier2_threshold:
            discount = (subtotal * config.tier2_discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return discount
        
        if subtotal >= config.tier1_threshold:
            discount = (subtotal * config.tier1_discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return discount
        
        return Decimal("0.00").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


discount_service = DiscountService()
