"""
Authentication service — registration, login, token refresh.
Passwords are hashed via bcrypt; tokens are JWT.
"""
from __future__ import annotations

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.logging import get_logger
from app.core.security import (
    decode_token, create_access_token, create_refresh_token,
    get_subject_from_token, hash_password, verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse, UserLogin, UserRegister

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._users = UserRepository(db)

    async def register(self, data: UserRegister) -> User:
        email = data.email.lower()
        if await self._users.email_exists(email):
            raise ConflictError("Email already registered")
        if await self._users.username_exists(data.username):
            raise ConflictError("Username already taken")

        user = await self._users.create(
            email=email,
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            is_active=True,
        )
        logger.info("user.registered", user_id=str(user.id), email=email)
        return user

    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self._users.get_by_email(data.email.lower())
        if user is None or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        logger.info("user.login", user_id=str(user.id))
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        from jose import JWTError
        try:
            if decode_token(refresh_token).get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")
        except JWTError:
            raise AuthenticationError("Invalid refresh token")
        subject = get_subject_from_token(refresh_token)
        if subject is None:
            raise AuthenticationError("Invalid refresh token")
        try:
            user_id = uuid.UUID(subject)
        except (ValueError, TypeError):
            raise AuthenticationError("Invalid refresh token")
        user = await self._users.get(user_id)
        if user is None:
            raise AuthenticationError("Invalid refresh token")
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        access = create_access_token(str(user.id))
        new_refresh = create_refresh_token(str(user.id))
        return TokenResponse(
            access_token=access,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
