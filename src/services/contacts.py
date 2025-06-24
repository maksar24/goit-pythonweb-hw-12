from typing import List
from fastapi import HTTPException

from src.schemas import ContactCreate, ContactUpdate
from src.database.models import Contact, User
from src.repository.contacts import ContactRepository


class ContactService:
    """
    Service class to handle contact-related operations.
    """

    def __init__(self, repository: ContactRepository):
        """
        Initialize ContactService with a ContactRepository instance.

        Args:
            repository (ContactRepository): Repository to manage contact data.
        """
        self.repository = repository

    async def list_contacts(
        self, user: User, skip: int = 0, limit: int = 10
    ) -> List[Contact]:
        """
        Retrieve a list of contacts for a given user with pagination.

        Args:
            user (User): The owner of the contacts.
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 10.

        Returns:
            List[Contact]: List of Contact objects.
        """
        return await self.repository.get_contacts(user, skip=skip, limit=limit)

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact:
        """
        Retrieve a specific contact by its ID for a given user.

        Args:
            contact_id (int): The ID of the contact.
            user (User): The owner of the contact.

        Raises:
            HTTPException: If contact with given ID is not found.

        Returns:
            Contact: The found contact object.
        """
        contact = await self.repository.get_contact_by_id(contact_id, user)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        return contact

    async def create_contact(self, contact_data: ContactCreate, user: User) -> Contact:
        """
        Create a new contact for the given user.

        Args:
            contact_data (ContactCreate): Data required to create a contact.
            user (User): The owner of the contact.

        Raises:
            HTTPException: If a contact with the same email already exists.

        Returns:
            Contact: The newly created contact object.
        """
        existing_contact = await self.repository.get_contact_by_email(
            contact_data.email, user
        )
        if existing_contact:
            raise HTTPException(status_code=400, detail="Email already exists")
        return await self.repository.create_contact(contact_data, user)

    async def update_contact(
        self, contact_id: int, contact_data: ContactUpdate, user: User
    ) -> Contact | None:
        """
        Update an existing contact identified by contact_id for a given user.

        Args:
            contact_id (int): ID of the contact to update.
            contact_data (ContactUpdate): Updated contact data.
            user (User): The owner of the contact.

        Raises:
            HTTPException: If the contact is not found or if the new email already exists on another contact.

        Returns:
            Contact | None: Updated contact object if successful.
        """
        contact = await self.repository.get_contact_by_id(contact_id, user)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        existing_contact = await self.repository.get_contact_by_email(
            contact_data.email, user
        )
        if existing_contact and existing_contact.id != contact_id:
            raise HTTPException(status_code=400, detail="Email already exists")
        return await self.repository.update_contact(contact_id, contact_data, user)

    async def delete_contact(self, contact_id: int, user: User) -> None:
        """
        Delete a contact by its ID for a given user.

        Args:
            contact_id (int): ID of the contact to delete.
            user (User): The owner of the contact.

        Raises:
            HTTPException: If the contact is not found.

        Returns:
            None
        """
        contact = await self.repository.get_contact_by_id(contact_id, user)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        await self.repository.delete_contact(contact_id, user)
