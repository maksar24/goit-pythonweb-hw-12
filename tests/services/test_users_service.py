import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.users import UserService
from src.schemas import UserCreate


@pytest.mark.asyncio
async def test_create_user_success(fake_session):
    body = UserCreate(
        username="newuser", email="new@example.com", password="strong_password"
    )

    # Мокуємо репозиторій
    mock_repo = AsyncMock()
    mock_repo.create_user.return_value = "created_user"

    with (
        patch("src.services.users.UserRepository", return_value=mock_repo),
        patch("src.services.users.Gravatar") as mock_gravatar,
    ):

        mock_gravatar.return_value.get_image.return_value = (
            "http://gravatar.com/avatar.png"
        )

        service = UserService(fake_session)
        result = await service.create_user(body)

        assert result == "created_user"
        mock_repo.create_user.assert_awaited_once_with(
            body, "http://gravatar.com/avatar.png", "user"
        )


@pytest.mark.asyncio
async def test_get_user_by_id(fake_session, fake_user):
    mock_repo = AsyncMock()
    mock_repo.get_user_by_id.return_value = fake_user

    with patch("src.services.users.UserRepository", return_value=mock_repo):
        service = UserService(fake_session)
        result = await service.get_user_by_id(1)

        assert result == fake_user
        mock_repo.get_user_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_user_by_username(fake_session, fake_user):
    mock_repo = AsyncMock()
    mock_repo.get_user_by_username.return_value = fake_user

    with patch("src.services.users.UserRepository", return_value=mock_repo):
        service = UserService(fake_session)
        result = await service.get_user_by_username("testuser")

        assert result == fake_user
        mock_repo.get_user_by_username.assert_awaited_once_with("testuser")


@pytest.mark.asyncio
async def test_get_user_by_email(fake_session, fake_user):
    mock_repo = AsyncMock()
    mock_repo.get_user_by_email.return_value = fake_user

    with patch("src.services.users.UserRepository", return_value=mock_repo):
        service = UserService(fake_session)
        result = await service.get_user_by_email("test@example.com")

        assert result == fake_user
        mock_repo.get_user_by_email.assert_awaited_once_with("test@example.com")


@pytest.mark.asyncio
async def test_confirmed_email(fake_session):
    mock_repo = AsyncMock()
    mock_repo.confirmed_email.return_value = None

    with patch("src.services.users.UserRepository", return_value=mock_repo):
        service = UserService(fake_session)
        result = await service.confirmed_email("test@example.com")

        assert result is None
        mock_repo.confirmed_email.assert_awaited_once_with("test@example.com")


@pytest.mark.asyncio
async def test_update_avatar_url_success(fake_session, fake_user):
    mock_repo = AsyncMock()
    mock_repo.get_user_by_email.return_value = fake_user
    mock_repo.update_avatar_url.return_value = "updated_user"

    with patch("src.services.users.UserRepository", return_value=mock_repo):
        service = UserService(fake_session)
        result = await service.update_avatar_url(
            "test@example.com", "http://new.avatar/url.png"
        )

        assert result == "updated_user"
        mock_repo.get_user_by_email.assert_awaited_once_with("test@example.com")
        mock_repo.update_avatar_url.assert_awaited_once_with(
            fake_user, "http://new.avatar/url.png"
        )


@pytest.mark.asyncio
async def test_update_avatar_url_user_not_found(fake_session):
    mock_repo = AsyncMock()
    mock_repo.get_user_by_email.return_value = None

    with patch("src.services.users.UserRepository", return_value=mock_repo):
        service = UserService(fake_session)
        with pytest.raises(Exception) as exc:
            await service.update_avatar_url(
                "notfound@example.com", "http://new.avatar/url.png"
            )

        assert exc.value.status_code == 404
        assert "Contact not found" in str(exc.value)
