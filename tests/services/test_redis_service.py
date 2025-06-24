import pytest
from unittest.mock import patch, MagicMock
from src.services.redis_cache import get_redis, redis
from src.services import redis_cache


@pytest.mark.asyncio
async def test_get_redis_creates_instance():
    redis_cache.redis = None

    with patch("src.services.redis_cache.Redis") as mock_redis_class:
        mock_redis_instance = MagicMock()
        mock_redis_class.from_url.return_value = mock_redis_instance

        client = await get_redis()

        mock_redis_class.from_url.assert_called_once_with(
            redis_cache.settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

        assert client == mock_redis_instance


@pytest.mark.asyncio
async def test_get_redis_returns_cached_instance():
    redis_cache.redis = None

    with patch("src.services.redis_cache.Redis") as mock_redis_class:
        mock_redis_instance = MagicMock()
        mock_redis_class.from_url.return_value = mock_redis_instance

        client1 = await get_redis()
        client2 = await get_redis()

        mock_redis_class.from_url.assert_called_once()

        assert client1 == client2
