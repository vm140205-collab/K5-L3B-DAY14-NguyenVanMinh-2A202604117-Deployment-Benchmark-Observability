"""Config — 12-Factor: mọi cấu hình đọc từ biến môi trường."""
import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


@dataclass
class Settings:
    port: int
    environment: str
    agent_api_key: str
    redis_url: str
    rate_limit_per_minute: int
    daily_budget_usd: float

    def __init__(self) -> None:
        self.port = int(_env("PORT", "8000"))
        self.environment = _env("ENVIRONMENT", "development")
        self.agent_api_key = _env("AGENT_API_KEY", "")
        self.redis_url = _env("REDIS_URL", "redis://127.0.0.1:6379/0")
        self.rate_limit_per_minute = int(_env("RATE_LIMIT_PER_MINUTE", "10"))
        self.daily_budget_usd = float(_env("DAILY_BUDGET_USD", _env("MONTHLY_BUDGET_USD", "1.0")))


settings = Settings()
