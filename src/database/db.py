import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import settings


class DatabaseSessionManager:
    """
    Manager for asynchronous database sessions using SQLAlchemy AsyncEngine.

    Args:
        url (str): Database connection URL.

    Attributes:
        _engine (AsyncEngine): The SQLAlchemy async engine instance.
        _session_maker (async_sessionmaker): Factory for creating async sessions.

    Usage:
        Use the 'session' async context manager to acquire a database session.
    """

    def __init__(self, url: str):
        self._engine: AsyncEngine = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Async context manager to provide a database session.

        Yields:
            AsyncSession: An asynchronous database session.

        Raises:
            Exception: If session maker is not initialized.
            SQLAlchemyError: On database operation errors, session rollback is performed.
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Dependency function for FastAPI to get an async database session.

    Yields:
        AsyncSession: An asynchronous database session.
    """
    async with sessionmanager.session() as session:
        yield session
