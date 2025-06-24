"""
This module contains Pydantic schemas for the application.

Schemas are used for request and response validation and serialization.
"""

import enum
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: str
    role: UserRole

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "user"


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class ContactBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    phone_number: str = Field(min_length=5, max_length=20)
    birthday: date
    additional_data: Optional[str] = Field(default=None, max_length=255)


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(default=None, min_length=5, max_length=20)
    birthday: Optional[date] = None
    additional_data: Optional[str] = Field(default=None, max_length=255)


class ContactResponse(ContactBase):
    id: int

    model_config = {"from_attributes": True}


class RequestEmail(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
