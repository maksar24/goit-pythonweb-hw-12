import pytest
from unittest.mock import AsyncMock, MagicMock

from src.schemas import ContactUpdate
from src.repository.contacts import ContactRepository


@pytest.mark.asyncio
async def test_get_contact_by_email(fake_session, fake_user, fake_contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_contact
    fake_session.execute = AsyncMock(return_value=mock_result)
    repo = ContactRepository(fake_session)

    result = await repo.get_contact_by_email("john@example.com", fake_user)

    assert result == fake_contact


@pytest.mark.asyncio
async def test_get_contacts(fake_session, fake_user, fake_contact):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake_contact]
    fake_session.execute = AsyncMock(return_value=mock_result)
    repo = ContactRepository(fake_session)

    results = await repo.get_contacts(fake_user)

    assert isinstance(results, list)
    assert results[0] == fake_contact


@pytest.mark.asyncio
async def test_get_contact_by_id(fake_session, fake_user, fake_contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_contact
    fake_session.execute = AsyncMock(return_value=mock_result)
    repo = ContactRepository(fake_session)

    result = await repo.get_contact_by_id(1, fake_user)

    assert result == fake_contact


@pytest.mark.asyncio
async def test_create_contact(fake_session, fake_user, fake_contact_data):
    fake_session.refresh = AsyncMock()
    fake_session.commit = AsyncMock()
    fake_session.add = AsyncMock()

    repo = ContactRepository(fake_session)

    result = await repo.create_contact(fake_contact_data, fake_user)

    fake_session.add.assert_called_once()
    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once()
    assert result.user_id == fake_user.id
    assert result.first_name == fake_contact_data.first_name


@pytest.mark.asyncio
async def test_update_contact(fake_session, fake_user, fake_contact):
    contact_data = ContactUpdate(first_name="Jane")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_contact

    fake_session.execute = AsyncMock(return_value=mock_result)
    fake_session.commit = AsyncMock()
    fake_session.refresh = AsyncMock()

    repo = ContactRepository(fake_session)

    updated = await repo.update_contact(fake_contact.id, contact_data, fake_user)

    assert updated is not None, "updated is None"
    assert updated.first_name == "Jane"
    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_delete_contact(fake_session, fake_user, fake_contact):
    fake_session.execute.return_value.scalar_one_or_none.return_value = fake_contact
    fake_session.delete = AsyncMock()
    fake_session.commit = AsyncMock()

    repo = ContactRepository(fake_session)

    result = await repo.delete_contact(fake_contact.id, fake_user)

    assert result is True
    fake_session.delete.assert_called_once()
    fake_session.commit.assert_called_once()
