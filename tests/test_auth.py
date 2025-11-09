from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.models.user import User

# ==================== REGISTRATION TESTS ====================


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    user_data = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "password123",
    }

    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_user_duplicate_email(client: AsyncClient, test_user: User):
    user_data = {
        "email": test_user.email,
        "full_name": "Another User",
        "password": "password123",
    }

    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_user_invalid_email(client: AsyncClient):
    user_data = {
        "email": "invalid-email",
        "full_name": "Test User",
        "password": "password123",
    }

    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_user_short_password(client: AsyncClient):
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "short",
    }

    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 422


# ==================== LOGIN TESTS ====================


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    login_data = {
        "username": test_user.email,
        "password": "testpassword123",
    }

    response = await client.post("/auth/login", data=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_email(client: AsyncClient):
    login_data = {
        "username": "nonexistent@example.com",
        "password": "password123",
    }

    response = await client.post("/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user: User):
    login_data = {
        "username": test_user.email,
        "password": "wrongpassword",
    }

    response = await client.post("/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


# ==================== /ME ENDPOINT TESTS ====================


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient, test_user_token: str):
    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    response = await client.get("/auth/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_expired_token(client: AsyncClient, test_user: User):
    from app.core.security import create_access_token

    expired_token = create_access_token(
        data={"sub": str(test_user.id)}, expires_delta=timedelta(seconds=-1)
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
