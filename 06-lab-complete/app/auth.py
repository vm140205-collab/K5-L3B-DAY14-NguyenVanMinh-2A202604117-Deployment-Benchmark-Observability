"""API Key authentication (tiêu chí 6)."""
from fastapi import HTTPException, Request

from app.config import settings


async def verify_api_key(request: Request) -> str:
    key = request.headers.get("X-API-Key")
    if not key or key != settings.agent_api_key:
        raise HTTPException(status_code=401, detail="Thiếu hoặc sai API key (header X-API-Key)")
    return key
