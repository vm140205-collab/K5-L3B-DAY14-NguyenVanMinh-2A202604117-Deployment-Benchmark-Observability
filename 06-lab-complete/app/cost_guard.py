"""Cost guard (tiêu chí 8) — cộng dồn chi phí LLM theo ngày vào Redis."""
import time

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r

# Giá USD / 1K tokens (tham khảo gpt-4o-mini)
PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006

DEFAULT_INPUT_TOKENS = 10
DEFAULT_OUTPUT_TOKENS = 40


def _budget_key() -> str:
    day = time.strftime("%Y%m%d", time.gmtime())
    return f"cost:{day}"


def estimate_cost(input_tokens: int = DEFAULT_INPUT_TOKENS,
                  output_tokens: int = DEFAULT_OUTPUT_TOKENS) -> float:
    return (input_tokens * PRICE_INPUT_PER_1K + output_tokens * PRICE_OUTPUT_PER_1K) / 1000.0


def check_budget() -> None:
    """Gọi TRƯỚC khi gọi LLM. Hết budget → raise HTTPException(status_code=402)."""
    spent = float(r.get(_budget_key()) or 0.0)
    if spent >= settings.daily_budget_usd:
        raise HTTPException(status_code=402, detail="Vượt ngân sách LLM trong ngày")


def record_cost(cost_usd: float) -> None:
    key = _budget_key()
    pipe = r.pipeline()
    pipe.incrbyfloat(key, cost_usd)
    pipe.expire(key, 60 * 60 * 48)
    pipe.execute()
