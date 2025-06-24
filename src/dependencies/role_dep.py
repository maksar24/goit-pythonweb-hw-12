from fastapi import Depends, HTTPException, status

from src.services.auth import get_current_user
from src.database.models import UserRole, User
from src.schemas import User


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тільки адміністратори мають доступ до цієї операції.",
        )
    return user
