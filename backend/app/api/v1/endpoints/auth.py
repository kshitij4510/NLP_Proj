"""Authentication endpoints."""
from fastapi import APIRouter, status
from app.api.deps import DB
from app.schemas.auth import RefreshRequest, TokenResponse, UserLogin, UserRead, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: DB):
    svc = AuthService(db)
    user = await svc.register(data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: DB):
    svc = AuthService(db)
    return await svc.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: DB):
    svc = AuthService(db)
    return await svc.refresh(data.refresh_token)
