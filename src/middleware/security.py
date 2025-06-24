from fastapi import Request
from fastapi.responses import JSONResponse
from src.config.settings import settings
from src.core.logger import logger

DENIED_ORIGINS = settings.DENIED_ORIGINS
DENIED_USER_AGENTS = settings.DENIED_USER_AGENTS


async def block_denied_requests(request: Request, call_next):
    """
    Middleware to block requests from denied origins or user agents.

    Checks the request headers for 'origin' and 'user-agent'.
    If the origin is in the denied origins list or the user-agent matches any denied user agents,
    the request is blocked with a 403 Forbidden response.

    Args:
        request (Request): Incoming HTTP request.
        call_next (Callable): Function to call the next middleware or route handler.

    Returns:
        JSONResponse: 403 response if request is blocked; otherwise, the response from the next handler.

    Logs any unexpected errors during request processing.
    """
    origin = request.headers.get("origin")
    user_agent = request.headers.get("user-agent", "")
    if origin in DENIED_ORIGINS or any(
        bad_ua in user_agent for bad_ua in DENIED_USER_AGENTS
    ):
        return JSONResponse(
            status_code=403,
            content={"detail": "Доступ заборонено"},
        )
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Error in middleware: {e}")
        raise e
