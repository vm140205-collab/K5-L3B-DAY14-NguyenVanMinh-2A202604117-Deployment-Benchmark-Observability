"""Rate limiting (tiêu chí 7) — sliding window trong Redis."""
import time

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r

WINDOW_SECONDS = 60


def check_rate_limit(key: str) -> None:
    """Vượt RATE_LIMIT_PER_MINUTE request/60s → HTTP 429 (kèm Retry-After)."""
    now = time.time()
    window_key = f"rate:{key}"
    member = f"{now}:{time.monotonic_ns()}"
    pipe = r.pipeline()
    pipe.zremrangebyscore(window_key, 0, now - WINDOW_SECONDS)
    pipe.zcard(window_key)
    pipe.zadd(window_key, {member: now})
    pipe.expire(window_key, WINDOW_SECONDS)
    _, count, _, _ = pipe.execute()
    if count > settings.rate_limit_per_minute:
        retry_after = max(1, int(WINDOW_SECONDS - (now - float(r.zrange(window_key, 0, 0, withscores=True)[0][1]))))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit vượt {settings.rate_limit_per_minute} request/phút",
            headers={"Retry-After": str(retry_after)},
        )
