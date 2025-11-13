import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

# ==================== USER CRUD TESTS ====================


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, test_user: User):
    response = await client.get(f"/users/{test_user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    response = await client.get("/users/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_all_users(
    client: AsyncClient, test_user: User, db_session: AsyncSession
):
    from app.core.security import hash_password
    from app.models.user import User

    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
    await db_session.commit()

    response = await client.get("/users?page=1&page_size=3")

    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 3
    assert data["total"] == 6
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert data["total_pages"] == 2


@pytest.mark.asyncio
async def test_get_all_users_pagination(client: AsyncClient, test_user: User):
    response = await client.get("/users?page=2&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 10


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, test_user: User):
    update_data = {"full_name": "Updated Name"}

    response = await client.put(f"/users/{test_user.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_update_user_password(
    client: AsyncClient, test_user: User, db_session: AsyncSession
):
    from app.core.security import verify_password

    update_data = {"password": "newpassword123"}

    response = await client.put(f"/users/{test_user.id}", json=update_data)

    assert response.status_code == 200

    await db_session.refresh(test_user)

    assert verify_password("newpassword123", test_user.hashed_password)
    assert not verify_password("testpassword123", test_user.hashed_password)


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient):
    update_data = {"full_name": "Updated Name"}

    response = await client.put("/users/99999", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, test_user: User):
    response = await client.delete(f"/users/{test_user.id}")

    assert response.status_code == 204

    get_response = await client.get(f"/users/{test_user.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient):
    response = await client.delete("/users/99999")

    assert response.status_code == 404
