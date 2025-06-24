import json
from datetime import datetime, timedelta, UTC
from typing import Optional
from types import SimpleNamespace

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db
from src.database.models import User, UserRole
from src.config.settings import settings
from src.services.users import UserService
from src.services.redis_cache import get_redis


class Hash:
    """
    Provides methods to hash passwords and verify them using bcrypt.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password) -> bool:
        """
        Verify a plain password against a hashed password.

        Args:
            plain_password (str): The plaintext password to verify.
            hashed_password (str): The hashed password to compare against.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Generate a bcrypt hash of the given password.

        Args:
            password (str): The plaintext password to hash.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """
    Create a JWT access token with an optional expiration time.

    Args:
        data (dict): The data to encode into the token.
        expires_delta (Optional[int]): Expiration time in seconds.

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def create_refresh_token(data: dict, expires_delta: Optional[int] = None):
    """
    Create a JWT refresh token with an optional expiration time in minutes.

    Args:
        data (dict): The data to encode into the token.
        expires_delta (Optional[int]): Expiration time in minutes.

    Returns:
        str: The encoded JWT refresh token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.JWT_REFRESH_EXPIRATION_MINUTES
        )
    to_encode.update(
        {
            "token_type": "refresh",
            "exp": expire,
        }
    )
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> SimpleNamespace:
    """
    Retrieve the current user from the JWT token.

    Checks the token validity, tries to fetch cached user data from Redis,
    otherwise queries the database.

    Args:
        token (str): JWT token from the Authorization header.
        db (AsyncSession): Database session.

    Raises:
        HTTPException: If credentials are invalid or user not found.

    Returns:
        SimpleNamespace: User data namespace with id, username, email, confirmed status, and role.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception

    redis = await get_redis()
    cached_user = await redis.get(f"user:{username}")

    if cached_user:
        user_data = json.loads(cached_user)
        user_data["role"] = UserRole(user_data["role"])
        return SimpleNamespace(**user_data)

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception

    user_data = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "confirmed": user.confirmed,
        "role": user.role.value if isinstance(user.role, UserRole) else user.role,
    }

    await redis.set(f"user:{username}", json.dumps(user_data), ex=3600)
    return SimpleNamespace(**user_data)


def create_email_token(data: dict) -> str:
    """
    Create a JWT refresh token with an optional expiration time in minutes.

    Args:
        data (dict): The data to encode into the token.
        expires_delta (Optional[int]): Expiration time in minutes.

    Returns:
        str: The encoded JWT refresh token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str) -> Optional[str]:
    """
    Extract email (subject) from a JWT token.

    Args:
        token (str): JWT token.

    Raises:
        HTTPException: If token is invalid or cannot be decoded.

    Returns:
        Optional[str]: Extracted email if valid.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Неправильний токен для перевірки електронної пошти",
        )


async def verify_refresh_token(
    refresh_token: str, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Verify a JWT refresh token and return the corresponding user if valid.

    Args:
        refresh_token (str): The JWT refresh token.
        db (AsyncSession): Database session.

    Returns:
        Optional[User]: User object if token is valid and user exists, else None.
    """
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_REFRESH_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username = payload.get("sub")
        token_type = payload.get("token_type")
        if username is None or token_type != "refresh":
            return None
        stmt = select(User).where(
            User.username == username, User.refresh_token == refresh_token
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
