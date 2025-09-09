from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
import yaml
from decimal import ROUND_HALF_UP, getcontext

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./legacyshop.db"

    PAYMENT_RANDOM_ENABLED: bool = False
    PAYMENT_FAIL_RATE_5XX: float = 0.10
    PAYMENT_FAIL_RATE_4XX: float = 0.05

    IDEMPOTENCY_TTL_DAYS: int = 7
    SCHEDULER_ENABLED: bool = True

    PROMOTION_TIERS: list[dict] = Field(default_factory=list)
    LOYALTY_POINTS_PER_DOLLAR: int = 1
    LOYALTY_MAX_POINTS: int = 500
    PAYMENTS_AUTH_URL: str = "http://localhost:8000/mock/payment/authorize"
    PAYMENTS_TIMEOUT_SECONDS: int = 5
    INVENTORY_RESTOCK_QUANTITY: int = 50
    INVENTORY_LOW_STOCK_THRESHOLD: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def load_yaml_overrides(self):
        path = os.getenv("APP_CONFIG_YAML")
        if path and os.path.exists(path):
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
            promos = (((data or {}).get("business") or {}).get("promotions") or {})
            tiers = promos.get("discountTiers") or promos.get("tiers") or []
            self.PROMOTION_TIERS = tiers
            loyalty = ((data.get("business") or {}).get("loyalty") or {})
            self.LOYALTY_POINTS_PER_DOLLAR = int(loyalty.get("pointsPerDollar", self.LOYALTY_POINTS_PER_DOLLAR))
            self.LOYALTY_MAX_POINTS = int(loyalty.get("maxPoints", self.LOYALTY_MAX_POINTS))
            payments = ((data.get("business") or {}).get("payments") or {})
            self.PAYMENTS_AUTH_URL = payments.get("authUrl", self.PAYMENTS_AUTH_URL)
            self.PAYMENTS_TIMEOUT_SECONDS = int(payments.get("timeoutSeconds", self.PAYMENTS_TIMEOUT_SECONDS))
            inventory = ((data.get("business") or {}).get("inventory") or {})
            self.INVENTORY_RESTOCK_QUANTITY = int(inventory.get("defaultRestockQuantity", self.INVENTORY_RESTOCK_QUANTITY))
            self.INVENTORY_LOW_STOCK_THRESHOLD = int(inventory.get("lowStockThreshold", self.INVENTORY_LOW_STOCK_THRESHOLD))

settings = Settings()
settings.load_yaml_overrides()
getcontext().rounding = ROUND_HALF_UP
