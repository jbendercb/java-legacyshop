from decimal import Decimal
from typing import List, Optional
from pydantic_settings import BaseSettings


class DiscountTier(BaseSettings):
    threshold: Decimal
    percentage: Decimal


class Promotions(BaseSettings):
    discount_tiers: List[DiscountTier] = [
        DiscountTier(threshold=Decimal("50.00"), percentage=Decimal("0.05")),
        DiscountTier(threshold=Decimal("100.00"), percentage=Decimal("0.10")),
        DiscountTier(threshold=Decimal("200.00"), percentage=Decimal("0.15")),
    ]


class Loyalty(BaseSettings):
    points_per_dollar: Decimal = Decimal("0.1")
    max_points: int = 500


class Payments(BaseSettings):
    auth_url: str = "http://localhost:8080/mock/payment/authorize"
    timeout_seconds: int = 5
    retry_attempts: int = 1


class Inventory(BaseSettings):
    default_restock_quantity: int = 100
    low_stock_threshold: int = 10


class Settings(BaseSettings):
    database_url: str = "sqlite:///./legacyshop.db"
    secret_key: str = "your-secret-key-here"
    
    promotions: Promotions = Promotions()
    loyalty: Loyalty = Loyalty()
    payments: Payments = Payments()
    inventory: Inventory = Inventory()

    model_config = {"env_file": ".env", "env_nested_delimiter": "__"}


settings = Settings()
