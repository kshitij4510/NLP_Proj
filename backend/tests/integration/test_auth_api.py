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


@pytest.mark.asyncio
async def test_token_types_are_enforced(client, sample_user_data):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    response = await client.post("/api/v1/auth/login", json={"email": sample_user_data["email"], "password": sample_user_data["password"]})
    tokens = response.json()
    response = await client.get("/api/v1/projects", headers={"Authorization": "Bearer " + tokens["refresh_token"]})
    assert response.status_code == 401
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client, sample_user_data):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    response = await client.post("/api/v1/auth/login", json={"email": sample_user_data["email"], "password": sample_user_data["password"]})
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": response.json()["refresh_token"]})
    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_report_generation_and_authenticated_ieee_export(client, sample_user_data):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    tokens = (await client.post("/api/v1/auth/login", json={"email": sample_user_data["email"], "password": sample_user_data["password"]})).json()
    headers = {"Authorization": "Bearer " + tokens["access_token"]}
    project = await client.post("/api/v1/projects", headers=headers, json={"title": "IEEE export test"})
    assert project.status_code == 201, project.text
    pid = project.json()["id"]
    response = await client.post(f"/api/v1/projects/{pid}/reports/generate", headers=headers, json={"project_id": pid, "verify_claims": False})
    assert response.status_code == 202, response.text
    report = response.json()
    assert report["status"] == "draft"
    response = await client.get(f"/api/v1/projects/{pid}/reports", headers=headers)
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 1
    url = f"/api/v1/projects/{pid}/reports/{report['id']}/export/ieee"
    response = await client.get(url, headers=headers)
    assert response.status_code == 200, response.text
    assert "IEEEtran" in response.text
    assert (await client.get(url)).status_code == 401
    other = dict(sample_user_data, email="other@example.com", username="other_user")
    await client.post("/api/v1/auth/register", json=other)
    tokens = (await client.post("/api/v1/auth/login", json={"email": other["email"], "password": other["password"]})).json()
    assert (await client.get(url, headers={"Authorization": "Bearer " + tokens["access_token"]})).status_code == 404
