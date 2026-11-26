"""
Production AI Agent — Part 6 Final Project

Kiểm tra:
    python check_production_ready.py
"""
import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.cost_guard import check_budget, estimate_cost, record_cost
from app.rate_limiter import check_rate_limit
from app.redis_client import redis_healthy, r
from utils.mock_llm import ask as llm_ask


class JsonFormatter(logging.Formatter):
    """Mỗi dòng log là 1 JSON object (tiêu chí 10)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "lvl": record.levelname,
            "event": record.getMessage(),
        }
        extra = getattr(record, "fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger("agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", extra={"fields": {"environment": app.title}})
    yield
    # Graceful shutdown (tiêu chí 11): uvicorn nhận SIGTERM, ngừng nhận request
    # mới, xử lý nốt request đang chạy rồi thoát (không ghi đè signal handler).
    logger.info("shutdown")


app = FastAPI(title="Production AI Agent", lifespan=lifespan)


@app.middleware("http")
async def request_log(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    logger.info("request", extra={"fields": {
        "path": request.url.path,
        "method": request.method,
        "status": response.status_code,
        "ms": round((time.perf_counter() - started) * 1000, 2),
    }})
    return response


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@app.get("/health")
def health():
    # Liveness: luôn 200 khi process còn chạy, kể cả khi Redis chưa kết nối được.
    return {"status": "ok"}


@app.get("/ready")
def ready():
    # Readiness: 503 khi Redis không kết nối được.
    if not redis_healthy():
        return _json_response({"status": "unavailable", "reason": "redis unreachable"}, 503)
    return {"status": "ready"}


def _json_response(payload: dict, status: int):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=status, content=payload)


@app.post("/ask")
def ask(body: AskRequest, key: str = Depends(verify_api_key)):
    check_rate_limit(key)
    check_budget()
    answer = llm_ask(body.question)
    record_cost(estimate_cost())
    return {"question": body.question, "answer": answer}
