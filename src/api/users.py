from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import File, UploadFile
from src.schemas import User as UserSchema
from src.database.models import User
from src.services.auth import get_current_user
from src.limiter.limiter import limiter
from src.database.db import get_db
from src.services.cloudinary_service import CloudinaryService
from src.dependencies.cloudinary_dep import get_cloudinary_service
from src.dependencies.role_dep import require_admin
from src.services.users import UserService
from src.core.logger import logger


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
@limiter.limit("5/minute")
async def me(request: Request, user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's information.

    Rate limited to 5 requests per minute.
    """
    return user


@router.patch("/avatar", response_model=UserSchema)
async def update_avatar_user(
    file: UploadFile = File(),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    cloudinary_service: CloudinaryService = Depends(get_cloudinary_service),
):
    """
    Update the avatar of the current admin user.

    Uploads the provided file to Cloudinary and updates the user's avatar URL.

    Requires admin privileges.
    """
    public_id = f"RestApp/{admin_user.username}"

    avatar_url = await cloudinary_service.upload_file(file, public_id)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(admin_user.email, avatar_url)
    logger.info(f"Uploading avatar: {file.filename}")

    return user
