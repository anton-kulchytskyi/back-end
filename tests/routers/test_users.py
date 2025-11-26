import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


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

    assert "results" in data
    assert isinstance(data["results"], list)

    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_all_users_pagination(client: AsyncClient, test_user: User):
    response = await client.get("/users?page=1&limit=5")
    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 5
    assert "results" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_update_user(
    client: AsyncClient, test_user: User, test_user_token: str, db_session: AsyncSession
):
    update_data = {"full_name": "Updated Name"}

    response = await client.put(
        "/users/me",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200

    db_session.expunge(test_user)

    updated = await db_session.get(User, test_user.id)

    assert updated.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_update_user_password(
    client: AsyncClient, test_user: User, test_user_token: str, db_session: AsyncSession
):
    from app.core.security import verify_password

    update_data = {"password": "newpassword123"}
    original_password_hash = test_user.hashed_password

    response = await client.put(
        "/users/me",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200

    db_session.expunge(test_user)

    updated = await db_session.get(User, test_user.id)

    assert updated.hashed_password != original_password_hash
    assert verify_password("newpassword123", updated.hashed_password)


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, test_user: User, test_user_token: str):
    response = await client.delete(
        "/users/me", headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 204


# ===== BE #7 Validation Tests =====


@pytest.mark.asyncio
async def test_update_requires_authentication(client: AsyncClient):
    response = await client.put("/users/me", json={"full_name": "New Name"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_requires_authentication(client: AsyncClient):
    response = await client.delete("/users/me")
    assert response.status_code == 403
