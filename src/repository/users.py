from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate


class UserRepository:
    """
    Repository for user-related database operations.

    Args:
        session (AsyncSession): Async SQLAlchemy session instance.
    """

    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by their ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            User | None: The user object if found, else None.
        """
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by their username.

        Args:
            username (str): The username of the user.

        Returns:
            User | None: The user object if found, else None.
        """
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by their email.

        Args:
            email (str): The email address of the user.

        Returns:
            User | None: The user object if found, else None.
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(
        self, body: UserCreate, avatar: str | None, role: str
    ) -> User:
        """
        Create a new user in the database.

        Args:
            body (UserCreate): Data for creating a user.
            avatar (str | None): URL of the user's avatar.
            role (str): User role.

        Returns:
            User: The created user object.
        """
        user = User(
            username=body.username,
            email=body.email,
            hashed_password=body.password,
            avatar=avatar,
            role=role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Mark a user's email as confirmed.

        Args:
            email (str): Email address to confirm.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.confirmed = True
            await self.db.commit()

    async def update_avatar_url(self, user: User, url: str) -> User:
        """
        Update the avatar URL of a user.

        Args:
            user (User): The user object.
            url (str): New avatar URL.

        Returns:
            User: Updated user object.
        """
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user
