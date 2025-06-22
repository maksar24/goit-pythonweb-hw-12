from typing import List
from fastapi import HTTPException

from src.schemas import ContactCreate, ContactUpdate
from src.database.models import Contact, User
from src.repository.contacts import ContactRepository


class ContactService:
    def __init__(self, repository: ContactRepository):
        self.repository = repository

    async def list_contacts(
        self, user: User, skip: int = 0, limit: int = 10
    ) -> List[Contact]:
        return await self.repository.get_contacts(user, skip=skip, limit=limit)

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact:
        contact = await self.repository.get_contact_by_id(contact_id, user)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        return contact

    async def create_contact(self, contact_data: ContactCreate, user: User) -> Contact:
        existing_contact = await self.repository.get_contact_by_email(
            contact_data.email, user
        )
        if existing_contact:
            raise HTTPException(status_code=400, detail="Email already exists")
        return await self.repository.create_contact(contact_data, user)

    async def update_contact(
        self, contact_id: int, contact_data: ContactUpdate, user: User
    ) -> Contact | None:
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
        contact = await self.repository.get_contact_by_id(contact_id, user)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        await self.repository.delete_contact(contact_id, user)
