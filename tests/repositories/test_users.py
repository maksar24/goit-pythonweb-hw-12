import pytest
from unittest.mock import MagicMock, AsyncMock

from src.repository.users import UserRepository
from src.schemas import UserCreate


@pytest.fixture
def user_repo(fake_session):
    return UserRepository(fake_session)


@pytest.mark.asyncio
async def test_get_user_by_id(user_repo, fake_session, fake_user):
    stmt_result = MagicMock()
    stmt_result.scalar_one_or_none.return_value = fake_user
    fake_session.execute.return_value = stmt_result

    result = await user_repo.get_user_by_id(1)

    assert result == fake_user


@pytest.mark.asyncio
async def test_get_user_by_username(user_repo, fake_session, fake_user):
    stmt_result = MagicMock()
    stmt_result.scalar_one_or_none.return_value = fake_user
    fake_session.execute.return_value = stmt_result

    result = await user_repo.get_user_by_username("testuser")

    assert result == fake_user


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo, fake_session, fake_user):
    stmt_result = MagicMock()
    stmt_result.scalar_one_or_none.return_value = fake_user
    fake_session.execute.return_value = stmt_result

    result = await user_repo.get_user_by_email("test@example.com")

    assert result == fake_user


@pytest.mark.asyncio
async def test_create_user(user_repo, fake_session):
    user_create = UserCreate(
        username="newuser", email="new@example.com", password="hashed_pass"
    )
    fake_session.commit.reset_mock()
    fake_session.refresh.reset_mock()
    fake_session.add.reset_mock()

    result = await user_repo.create_user(
        user_create, avatar="http://example.com/avatar.png", role="user"
    )

    fake_session.add.assert_called_once()
    fake_session.commit.assert_awaited_once()
    fake_session.refresh.assert_awaited_once()
    assert result.username == user_create.username


@pytest.mark.asyncio
async def test_confirmed_email(user_repo, fake_session, fake_user):
    user_repo.get_user_by_email = AsyncMock(return_value=fake_user)

    await user_repo.confirmed_email("test@example.com")

    assert fake_user.confirmed is True
    fake_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repo, fake_session, fake_user):
    new_url = "http://new.avatar.com"

    updated_user = await user_repo.update_avatar_url(fake_user, new_url)

    assert updated_user.avatar == new_url
    fake_session.commit.assert_awaited_once()
    fake_session.refresh.assert_awaited_once_with(fake_user)
