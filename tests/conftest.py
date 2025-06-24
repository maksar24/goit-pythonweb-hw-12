import pytest
from datetime import date
from unittest.mock import AsyncMock


from main import app
from src.database.models import User, Contact
from src.schemas import ContactCreate


@pytest.fixture
def fake_session():
    """Мок для асинхронної сесії SQLAlchemy."""
    return AsyncMock()


@pytest.fixture
def fake_user():
    """Фейковий користувач для тестів."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        confirmed=False,
        avatar="http://example.com/avatar.png",
        role="user",
        hashed_password="hashed_pass",
    )


@pytest.fixture
def fake_contact(fake_user):
    """Фейковий контакт."""
    return Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone_number="1234567890",
        birthday=date(1990, 1, 1),
        additional_data="Friend from school",
        user_id=fake_user.id,
        user=fake_user,
    )


@pytest.fixture
def fake_contact_data():
    """Фейкові вхідні дані для створення контакту."""
    return ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone_number="1234567890",
        birthday=date(1990, 1, 1),
        additional_data="Friend from school",
    )
