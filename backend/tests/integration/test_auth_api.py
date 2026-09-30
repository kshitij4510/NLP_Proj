"""Integration tests for auth endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, sample_user_data: dict):
    resp = await client.post("/api/v1/auth/register", json=sample_user_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == sample_user_data["email"]
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, sample_user_data: dict):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    resp = await client.post("/api/v1/auth/register", json=sample_user_data)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, sample_user_data: dict):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    resp = await client.post("/api/v1/auth/login", json={
        "email": sample_user_data["email"],
        "password": sample_user_data["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, sample_user_data: dict):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    resp = await client.post("/api/v1/auth/login", json={
        "email": sample_user_data["email"],
        "password": "WrongPassword1",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client: AsyncClient):
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 401  # No Authorization header


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
