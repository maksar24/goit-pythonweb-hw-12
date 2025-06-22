import os
from fastapi import Request
from fastapi.responses import JSONResponse
from src.config.settings import settings

DENIED_ORIGINS = settings.DENIED_ORIGINS
DENIED_USER_AGENTS = settings.DENIED_USER_AGENTS


async def block_denied_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    user_agent = request.headers.get("user-agent", "")
    if origin in DENIED_ORIGINS or any(
        bad_ua in user_agent for bad_ua in DENIED_USER_AGENTS
    ):
        return JSONResponse(
            status_code=403,
            content={"detail": "Доступ заборонено"},
        )
    return await call_next(request)
