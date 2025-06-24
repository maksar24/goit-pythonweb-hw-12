"""
Main application entry point for the Contacts API.

This module initializes the FastAPI app, configures middleware, rate limiting,
CORS, exception handlers, and includes API routers for health checks, authentication,
users, and contacts management.

It also configures integration with Cloudinary for media handling and applies
custom security middleware to block denied requests.

Usage:
    Run the application using Uvicorn server:

        uvicorn main:app --host 127.0.0.1 --port 8000 --reload
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from src.middleware.security import block_denied_requests
from src.limiter.limiter import limiter
from src.api import health, auth, users, contacts
from src.services.cloudinary_service import CloudinaryService
from src.config.settings import settings


app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.state.cloudinary_service = CloudinaryService(
    cloud_name=settings.CLD_NAME,
    api_key=settings.CLD_API_KEY,
    api_secret=settings.CLD_API_SECRET,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(block_denied_requests)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Exception handler for rate limit exceeded errors.

    Args:
        request (Request): The incoming HTTP request.
        exc (RateLimitExceeded): The rate limit exceeded exception.

    Returns:
        JSONResponse: Response with status code 429 and error message.
    """
    return JSONResponse(
        status_code=429,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )


app.include_router(contacts.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
