from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas import UserCreate
from src.core.logger import logger


class UserService:
    """
    Service class to handle user-related operations.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize UserService with an asynchronous database session.

        Args:
            db (AsyncSession): Asynchronous database session.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """
        Create a new user with optional Gravatar avatar.

        Args:
            body (UserCreate): User creation data.

        Returns:
            User: The created user object.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            logger.error(f"Failed to get gravatar image: {e}")

        role = body.role if body.role else "user"

        return await self.repository.create_user(body, avatar, role)

    async def get_user_by_id(self, user_id: int):
        """
        Retrieve a user by their unique ID.

        Args:
            user_id (int): User's unique identifier.

        Returns:
            User | None: User object if found, else None.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        """
        Retrieve a user by their username.

        Args:
            username (str): Username string.

        Returns:
            User | None: User object if found, else None.
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str):
        """
        Retrieve a user by their email address.

        Args:
            email (str): Email address.

        Returns:
            User | None: User object if found, else None.
        """
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        """
        Mark user's email as confirmed.

        Args:
            email (str): Email address to confirm.

        Returns:
            None
        """
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """
        Update the avatar URL of a user by email.

        Args:
            email (str): Email of the user.
            url (str): New avatar URL.

        Raises:
            HTTPException: If user with the given email is not found.

        Returns:
            User: Updated user object.
        """
        user = await self.repository.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="Contact not found")
        return await self.repository.update_avatar_url(user, url)
