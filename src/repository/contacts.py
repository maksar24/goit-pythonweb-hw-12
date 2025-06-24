from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate


class ContactRepository:
    """
    Repository for managing user contacts in the database.

    Args:
        session (AsyncSession): Async SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_contact_by_email(
        self, email: str | None, user: User
    ) -> Contact | None:
        """
        Retrieve a contact by email for a specific user.

        Args:
            email (str | None): Email of the contact.
            user (User): User who owns the contact.

        Returns:
            Contact | None: Contact if found, else None.
        """
        if email is None:
            return None
        stmt = select(Contact).where(Contact.email == email, Contact.user_id == user.id)
        result = await self.session.execute(stmt)
        contact = result.scalar_one_or_none()
        return contact

    async def get_contacts(
        self, user: User, skip: int = 0, limit: int = 10
    ) -> List[Contact]:
        """
        Retrieve a list of contacts for a user with pagination.

        Args:
            user (User): User who owns the contacts.
            skip (int): Number of contacts to skip.
            limit (int): Maximum number of contacts to return.

        Returns:
            List[Contact]: List of contacts.
        """
        stmt = select(Contact).filter_by(user_id=user.id).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        contacts = list(result.scalars().all())
        return contacts

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Retrieve a contact by ID for a specific user.

        Args:
            contact_id (int): ID of the contact.
            user (User): User who owns the contact.

        Returns:
            Optional[Contact]: Contact if found, else None.
        """
        stmt = select(Contact).where(
            Contact.id == contact_id, Contact.user_id == user.id
        )
        result = await self.session.execute(stmt)
        contact = result.scalar_one_or_none()
        return contact

    async def create_contact(self, contact: ContactCreate, user: User) -> Contact:
        """
        Create a new contact for a user.

        Args:
            contact (ContactCreate): Contact data to create.
            user (User): User who owns the new contact.

        Returns:
            Contact: Created contact object.
        """
        new_contact = Contact(**contact.model_dump(), user_id=user.id)
        self.session.add(new_contact)
        await self.session.commit()
        await self.session.refresh(new_contact)
        return new_contact

    async def update_contact(
        self, contact_id: int, contact_data: ContactUpdate, user: User
    ) -> Optional[Contact]:
        """
        Update an existing contact's details.

        Args:
            contact_id (int): ID of the contact to update.
            contact_data (ContactUpdate): Updated contact data.
            user (User): User who owns the contact.

        Returns:
            Optional[Contact]: Updated contact if found, else None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact is None:
            return None
        for field, value in contact_data.model_dump(exclude_unset=True).items():
            setattr(contact, field, value)
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> bool:
        """
        Delete a contact by ID for a specific user.

        Args:
            contact_id (int): ID of the contact to delete.
            user (User): User who owns the contact.

        Returns:
            bool: True if deleted successfully, False if not found.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact is None:
            return False
        await self.session.delete(contact)
        await self.session.commit()
        return True
