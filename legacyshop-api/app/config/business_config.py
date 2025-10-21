"""
Business configuration matching the Java application.yaml settings.
"""

from pydantic_settings import BaseSettings
from decimal import Decimal


class DiscountTier:
    """Discount tier configuration"""
    def __init__(self, threshold: Decimal, discount: Decimal):
        self.threshold = threshold
        self.discount = discount


class BusinessConfig(BaseSettings):
    """Business rules configuration"""
    
    tier1_threshold: Decimal = Decimal("50.00")
    tier1_discount: Decimal = Decimal("0.05")  # 5%
    
    tier2_threshold: Decimal = Decimal("100.00")
    tier2_discount: Decimal = Decimal("0.10")  # 10%
    
    tier3_threshold: Decimal = Decimal("200.00")
    tier3_discount: Decimal = Decimal("0.15")  # 15%
    
    payment_auth_url: str = "http://localhost:8001/mock/payment/authorize"
    payment_timeout_seconds: int = 10
    
    payment_max_attempts: int = 2
    payment_backoff_seconds: int = 1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = BusinessConfig()
