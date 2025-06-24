from fastapi import APIRouter, Depends
from typing import List

from src.schemas import ContactCreate, ContactUpdate, ContactResponse
from src.database.db import get_db
from src.repository.contacts import ContactRepository
from src.services.contacts import ContactService
from src.services.auth import get_current_user
from src.database.models import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/contacts")


def get_service(session: AsyncSession = Depends(get_db)) -> ContactService:
    """
    Dependency to get ContactService instance.

    Args:
        session (AsyncSession): Async DB session.

    Returns:
        ContactService: Service instance for contacts.
    """
    repo = ContactRepository(session)
    service = ContactService(repo)
    return service


@router.get("/", response_model=List[ContactResponse])
async def list_contacts(
    user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    service: ContactService = Depends(get_service),
):
    """
    Get a list of contacts for the current user with pagination.

    Args:
        user (User): Current authenticated user.
        skip (int): Number of records to skip (offset).
        limit (int): Maximum number of contacts to return.
        service (ContactService): Contact service instance.

    Returns:
        List[ContactResponse]: List of user's contacts.
    """
    return await service.list_contacts(user, skip=skip, limit=limit)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    service: ContactService = Depends(get_service),
    user: User = Depends(get_current_user),
):
    """
    Retrieve a single contact by its ID.

    Args:
        contact_id (int): ID of the contact to retrieve.
        service (ContactService): Contact service instance.
        user (User): Current authenticated user.

    Returns:
        ContactResponse: Contact data.
    """
    return await service.get_contact_by_id(contact_id, user)


@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(
    contact_data: ContactCreate,
    service: ContactService = Depends(get_service),
    user: User = Depends(get_current_user),
):
    """
    Create a new contact for the current user.

    Args:
        contact_data (ContactCreate): Data to create the contact.
        service (ContactService): Contact service instance.
        user (User): Current authenticated user.

    Returns:
        ContactResponse: Newly created contact data.
    """
    return await service.create_contact(contact_data, user)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    service: ContactService = Depends(get_service),
    user: User = Depends(get_current_user),
):
    """
    Update an existing contact by its ID.

    Args:
        contact_id (int): ID of the contact to update.
        contact_data (ContactUpdate): Updated contact data.
        service (ContactService): Contact service instance.
        user (User): Current authenticated user.

    Returns:
        ContactResponse: Updated contact data.
    """
    return await service.update_contact(contact_id, contact_data, user)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    service: ContactService = Depends(get_service),
    user: User = Depends(get_current_user),
):
    """
    Delete a contact by its ID.

    Args:
        contact_id (int): ID of the contact to delete.
        service (ContactService): Contact service instance.
        user (User): Current authenticated user.

    Returns:
        None
    """
    await service.delete_contact(contact_id, user)
