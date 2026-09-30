"""Authentication schemas."""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class UserRegister(BaseSchema):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseSchema):
    email: EmailStr
    password: str


class UserRead(IDSchema, TimestampSchema):
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseSchema):
    refresh_token: str
