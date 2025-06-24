from redis.asyncio import Redis
import logging
from src.config.settings import settings

redis: Redis | None = None


async def get_redis() -> Redis:
    """
    Get a singleton Redis client instance.

    This function initializes and returns an asynchronous Redis client.
    It creates a connection on the first call and reuses it on subsequent calls.

    Returns:
        Redis: An instance of an asynchronous Redis client.
    """
    global redis
    if not redis:
        logging.info(f"Connecting to Redis at {settings.REDIS_URL}")
        redis = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis
