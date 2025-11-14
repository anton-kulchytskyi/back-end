"""Tests for user endpoints with authentication."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, test_user: User):
    response = await client.get(f"/users/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    response = await client.get("/users/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_all_users(client: AsyncClient, test_user: User):
    response = await client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_all_users_pagination(client: AsyncClient, test_user: User):
    response = await client.get("/users?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, test_user: User, test_user_token: str):
    """User can update their own profile with authentication."""
    update_data = {"full_name": "Updated Name"}

    response = await client.put(
        "/users/me",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_user_password(
    client: AsyncClient, test_user: User, test_user_token: str, db_session: AsyncSession
):
    """User can update their password with authentication."""
    from app.core.security import verify_password

    update_data = {"password": "newpassword123"}

    response = await client.put(
        "/users/me",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200

    # Refresh user from DB and verify password
    await db_session.refresh(test_user)
    assert verify_password("newpassword123", test_user.hashed_password)


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, test_user: User, test_user_token: str):
    """User can delete their own profile with authentication."""
    response = await client.delete(
        "/users/me", headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 204


# ===== BE #7 Validation Tests =====


@pytest.mark.asyncio
async def test_update_requires_authentication(client: AsyncClient):
    """Update endpoint requires authentication (403 Forbidden when no token)."""
    response = await client.put("/users/me", json={"full_name": "New Name"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_requires_authentication(client: AsyncClient):
    """Delete endpoint requires authentication (403 Forbidden when no token)."""
    response = await client.delete("/users/me")
    assert response.status_code == 403
