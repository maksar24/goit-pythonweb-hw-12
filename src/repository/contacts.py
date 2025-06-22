from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_contact_by_email(
        self, email: str | None, user: User
    ) -> Contact | None:
        if email is None:
            return None
        stmt = select(Contact).where(Contact.email == email, Contact.user_id == user.id)
        result = await self.session.execute(stmt)
        contact = result.scalar_one_or_none()
        return contact

    async def get_contacts(
        self, user: User, skip: int = 0, limit: int = 10
    ) -> List[Contact]:
        stmt = select(Contact).filter_by(user_id=user.id).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        contacts = list(result.scalars().all())
        return contacts

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        stmt = select(Contact).where(
            Contact.id == contact_id, Contact.user_id == user.id
        )
        result = await self.session.execute(stmt)
        contact = result.scalar_one_or_none()
        return contact

    async def create_contact(self, contact: ContactCreate, user: User) -> Contact:
        new_contact = Contact(**contact.model_dump(), user_id=user.id)
        self.session.add(new_contact)
        await self.session.commit()
        await self.session.refresh(new_contact)
        return new_contact

    async def update_contact(
        self, contact_id: int, contact_data: ContactUpdate, user: User
    ) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact is None:
            return None
        for field, value in contact_data.model_dump(exclude_unset=True).items():
            setattr(contact, field, value)
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> bool:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact is None:
            return False
        await self.session.delete(contact)
        await self.session.commit()
        return True
