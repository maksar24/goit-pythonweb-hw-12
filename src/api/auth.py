"""
Authentication API module.

Provides endpoints for user registration, login, token refresh,
email confirmation, password reset, and related authentication functionality.

Modules:
- FastAPI APIRouter with prefix "/auth"
- Depends on async DB session, background tasks, and security utilities

Endpoints:
- POST /register: Register a new user
- POST /login: Authenticate user and obtain JWT tokens
- POST /refresh-token: Refresh JWT access token
- GET /confirmed_email/{token}: Confirm user's email address
- POST /request_email: Request email confirmation
- POST /request-password-reset: Request password reset email
- POST /reset-password: Reset password with token
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt

from src.schemas import (
    UserCreate,
    Token,
    User,
    RequestEmail,
    TokenRefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from src.services.auth import (
    create_access_token,
    Hash,
    get_email_from_token,
    create_refresh_token,
    verify_refresh_token,
    create_email_token,
)
from src.database.models import UserRole
from src.services.users import UserService
from src.services.redis_cache import get_redis
from src.database.db import get_db
from src.services.email import send_email, send_password_reset_email
from src.core.logger import logger
from src.config.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    Args:
        user_data (UserCreate): User registration data.
        background_tasks (BackgroundTasks): Background tasks for sending emails.
        request (Request): Request object to get base URL.
        db (AsyncSession): Async database session.

    Raises:
        HTTPException: If user with email or username already exists.

    Returns:
        User: Newly created user data.
    """
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким іменем вже існує",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, str(request.base_url)
    )

    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and provide JWT tokens.

    Args:
        form_data (OAuth2PasswordRequestForm): Login form data (username and password).
        db (AsyncSession): Async database session.

    Raises:
        HTTPException: If credentials are invalid or email not confirmed.

    Returns:
        dict: Access token, refresh token and token type.
    """
    logger.debug(f"Username: {form_data.username}, Password: {form_data.password}")
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна адреса не підтверджена",
        )

    access_token = await create_access_token(data={"sub": user.username})
    refresh_token = await create_refresh_token(data={"sub": user.username})
    user.refresh_token = refresh_token
    await db.commit()
    await db.refresh(user)

    try:
        redis = await get_redis()
        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "confirmed": user.confirmed,
            "role": user.role.value if isinstance(user.role, UserRole) else user.role,
        }
        await redis.set(f"user:{user.username}", json.dumps(user_data), ex=3600)
        logger.info(f"User {user.username} cached in Redis")
    except Exception as e:
        logger.exception(f"Redis caching failed for user {user.username}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh-token", response_model=Token)
async def new_token(request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh JWT access token using a valid refresh token.

    Args:
        request (TokenRefreshRequest): Request body with refresh token.
        db (AsyncSession): Async database session.

    Raises:
        HTTPException: If refresh token is invalid or expired.

    Returns:
        dict: New access token, the same refresh token and token type.
    """
    user = await verify_refresh_token(request.refresh_token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    new_access_token = await create_access_token(data={"sub": user.username})
    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirm user email by token.

    Args:
        token (str): Email confirmation token.
        db (AsyncSession): Async database session.

    Raises:
        HTTPException: If token is invalid or user verification fails.

    Returns:
        dict: Confirmation message.
    """
    email = await get_email_from_token(token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    await user_service.confirmed_email(email)
    return {"message": "Електронну пошту підтверджено"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a confirmation email resend.

    Args:
        body (RequestEmail): Request body with user's email.
        background_tasks (BackgroundTasks): Background tasks for sending email.
        request (Request): Request object to get base URL.
        db (AsyncSession): Async database session.

    Raises:
        HTTPException: If user not found.

    Returns:
        dict: Message about email confirmation status.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Перевірте свою електронну пошту для підтвердження"}


@router.post("/request-password-reset")
async def request_password_reset(
    body: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset email.

    Args:
        body (PasswordResetRequest): Request body with user's email.
        background_tasks (BackgroundTasks): Background tasks for sending email.
        request (Request): Request object to get base URL.
        db (AsyncSession): Async database session.

    Returns:
        dict: Message about password reset email status.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if not user:
        return {"message": "Якщо такий email існує, перевірте пошту для інструкцій."}

    reset_token = create_email_token({"sub": user.email, "scope": "password_reset"})

    reset_link = f"{request.base_url}reset-password?token={reset_token}"

    background_tasks.add_task(
        send_password_reset_email, user.email, user.username, reset_link
    )

    return {"message": "Якщо такий email існує, перевірте пошту для інструкцій."}


@router.post("/reset-password")
async def reset_password(
    body: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset user password using a password reset token.

    Args:
        body (PasswordResetConfirm): Request body with token and new password.
        db (AsyncSession): Async database session.

    Raises:
        HTTPException: If token is invalid or user not found.

    Returns:
        dict: Message about password reset success.
    """
    try:
        payload = jwt.decode(
            body.token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        email = payload.get("sub")
        scope = payload.get("scope")
        if not email or scope != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    hashed_password = Hash().get_password_hash(body.new_password)
    user.hashed_password = hashed_password
    await db.commit()
    await db.refresh(user)

    return {"message": "Пароль успішно змінено"}
