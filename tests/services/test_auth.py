import pytest
import json
from jose import jwt, JWTError
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from types import SimpleNamespace
from fastapi import HTTPException

from src.config.settings import settings
from src.database.models import User
from src.services.auth import (
    get_current_user,
    create_access_token,
    Hash,
    create_refresh_token,
    create_email_token,
    get_email_from_token,
    verify_refresh_token,
)


def test_password_hash_and_verify():
    hash_util = Hash()
    password = "supersecret"
    hashed = hash_util.get_password_hash(password)
    assert hashed != password
    assert hash_util.verify_password(password, hashed)
    assert not hash_util.verify_password("wrongpass", hashed)


@pytest.mark.asyncio
async def test_create_access_token_defaults():
    data = {"sub": "user1"}
    token = await create_access_token(data)
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == "user1"
    assert "exp" in payload
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.now()
    assert exp > now


@pytest.mark.asyncio
async def test_create_access_token_custom_expiration():
    data = {"sub": "user1"}
    expires = 60  # 1 minute
    token = await create_access_token(data, expires_delta=expires)
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    exp = datetime.fromtimestamp(payload["exp"])
    assert (exp - datetime.now()) <= timedelta(seconds=expires)


@pytest.mark.asyncio
async def test_create_refresh_token_defaults():
    data = {"sub": "user1"}
    token = await create_refresh_token(data)
    payload = jwt.decode(
        token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == "user1"
    assert payload["token_type"] == "refresh"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_create_refresh_token_custom_expiration():
    data = {"sub": "user1"}
    token = await create_refresh_token(data, expires_delta=5)
    payload = jwt.decode(
        token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    exp = datetime.fromtimestamp(payload["exp"])
    assert (exp - datetime.now()) <= timedelta(minutes=5)


@pytest.mark.asyncio
@patch("src.services.auth.UserService")
@patch("src.services.auth.get_redis")
@patch("src.services.auth.jwt.decode")
async def test_get_current_user_from_redis(
    mock_jwt_decode, mock_get_redis, mock_user_service, fake_session, fake_user
):
    mock_jwt_decode.return_value = {"sub": fake_user.username}

    redis_mock = AsyncMock()
    user_data = {
        "id": str(fake_user.id),
        "username": fake_user.username,
        "email": fake_user.email,
        "confirmed": fake_user.confirmed,
        "role": fake_user.role,
    }
    redis_mock.get.return_value = json.dumps(user_data)
    mock_get_redis.return_value = redis_mock

    user = await get_current_user(token="faketoken", db=fake_session)

    assert isinstance(user, SimpleNamespace)
    assert user.username == fake_user.username
    redis_mock.get.assert_awaited_once()
    mock_user_service.assert_not_called()


@pytest.mark.asyncio
@patch("src.services.auth.jwt.decode")
@patch("src.services.auth.get_redis")
@patch("src.services.auth.UserService")
async def test_get_current_user_from_db(
    mock_user_service, mock_get_redis, mock_jwt_decode, fake_session, fake_user
):
    mock_jwt_decode.return_value = {"sub": fake_user.username}

    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = AsyncMock()
    mock_get_redis.return_value = redis_mock

    instance = mock_user_service.return_value
    instance.get_user_by_username = AsyncMock(return_value=fake_user)

    user = await get_current_user(token="faketoken", db=fake_session)

    assert user.username == fake_user.username
    redis_mock.get.assert_awaited_once()
    redis_mock.set.assert_awaited_once()
    instance.get_user_by_username.assert_awaited_once_with(fake_user.username)


@pytest.mark.asyncio
@patch("src.services.auth.jwt.decode", side_effect=JWTError("bad token"))
async def test_get_current_user_invalid_token(mock_jwt_decode, fake_session):
    with pytest.raises(HTTPException):
        await get_current_user(token="badtoken", db=fake_session)


def test_create_email_token_and_decode():
    data = {"sub": "email@example.com"}
    token = create_email_token(data)
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == "email@example.com"
    assert "exp" in payload
    assert "iat" in payload


@pytest.mark.asyncio
async def test_get_email_from_token_valid():
    data = {"sub": "email@example.com"}
    token = create_email_token(data)
    email = await get_email_from_token(token)
    assert email == "email@example.com"


@pytest.mark.asyncio
async def test_get_email_from_token_invalid():
    with pytest.raises(HTTPException):
        await get_email_from_token("invalid.token.string")


@pytest.mark.asyncio
@patch("src.services.auth.jwt.decode")
async def test_verify_refresh_token_valid(mock_jwt_decode, fake_session):
    mock_jwt_decode.return_value = {"sub": "user1", "token_type": "refresh"}
    user_instance = MagicMock(spec=User)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user_instance
    fake_session.execute = AsyncMock(return_value=mock_result)
    user = await verify_refresh_token("fake_refresh_token", fake_session)
    assert user == user_instance

    mock_jwt_decode.assert_called_once_with(
        "fake_refresh_token", "refresh_token", algorithms=["HS256"]
    )


@pytest.mark.asyncio
@patch("src.services.auth.jwt.decode")
async def test_verify_refresh_token_invalid_token_type(mock_jwt_decode, fake_session):
    mock_jwt_decode.return_value = {"sub": "user1", "token_type": "access"}

    user = await verify_refresh_token("fake_refresh_token", fake_session)
    assert user is None


@pytest.mark.asyncio
@patch("src.services.auth.jwt.decode", side_effect=JWTError("decode error"))
async def test_verify_refresh_token_decode_error(fake_session):
    with pytest.raises(HTTPException):
        await verify_refresh_token("invalid_token", fake_session)
