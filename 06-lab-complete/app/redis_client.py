"""Kết nối Redis dùng chung cho rate limiter và cost guard."""
import logging

import redis

from app.config import settings

logger = logging.getLogger(__name__)

# Tạo client là lazy (không kết nối cho tới lệnh đầu tiên) — app vẫn khởi động
# được khi Redis chưa sẵn sàng.
r: redis.Redis = redis.from_url(settings.redis_url, decode_responses=True)


def redis_healthy() -> bool:
    try:
        return bool(r.ping())
    except Exception:
        logger.info(json_event("redis_unhealthy"))
        return False


def json_event(event: str, **fields) -> str:
    import json
    import time
    return json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "lvl": "INFO", "event": event, **fields})
