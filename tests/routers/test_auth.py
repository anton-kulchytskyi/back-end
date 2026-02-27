from datetime import timedelta

from httpx import AsyncClient

from app.models import User

# ==================== REGISTRATION TESTS ====================


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


async def test_register_user_duplicate_email(client: AsyncClient, test_user: User):
    user_data = {
        "email": test_user.email,
        "full_name": "Another User",
        "password": "password123",
    }

    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


async def test_register_user_invalid_email(client: AsyncClient):
    user_data = {
        "email": "invalid-email",
        "full_name": "Test User",
        "password": "password123",
    }

    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 422


async def test_register_user_short_password(client: AsyncClient):
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "short",
    }

    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 422


# ==================== LOGIN TESTS ====================


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


async def test_login_invalid_email(client: AsyncClient):
    login_data = {
        "username": "nonexistent@example.com",
        "password": "password123",
    }

    response = await client.post("/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


async def test_login_invalid_password(client: AsyncClient, test_user: User):
    login_data = {
        "username": test_user.email,
        "password": "wrongpassword",
    }

    response = await client.post("/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


# ==================== /ME ENDPOINT TESTS ====================


async def test_get_me_success(client: AsyncClient, test_user_token: str):
    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "hashed_password" not in data


async def test_get_me_no_token(client: AsyncClient):
    response = await client.get("/auth/me")

    assert response.status_code == 403


async def test_get_me_invalid_token(client: AsyncClient):
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401


async def test_get_me_expired_token(client: AsyncClient, test_user: User):
    from app.core.security import create_access_token

    expired_token = create_access_token(
        data={"sub": str(test_user.id)}, expires_delta=timedelta(seconds=-1)
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401


# ==================== REFRESH TOKEN TESTS ====================


async def test_refresh_success(client: AsyncClient, test_user: User):
    login_data = {"username": test_user.email, "password": "testpassword123"}
    login_response = await client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]

    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200, refresh_response.text
    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"] != tokens["access_token"]
    assert data["refresh_token"] != tokens["refresh_token"]


async def test_refresh_invalid_token(client: AsyncClient):
    response = await client.post(
        "/auth/refresh", json={"refresh_token": "invalid_token_here"}
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


async def test_refresh_expired_token(client: AsyncClient, test_user: User):
    from datetime import timedelta

    from app.core.security import create_refresh_token

    expired_refresh = create_refresh_token(
        data={"sub": str(test_user.id)}, expires_delta=timedelta(seconds=-1)
    )

    response = await client.post(
        "/auth/refresh", json={"refresh_token": expired_refresh}
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


async def test_refresh_user_not_found(client: AsyncClient):
    from app.core.security import create_refresh_token

    fake_refresh = create_refresh_token(data={"sub": "99999"})

    response = await client.post("/auth/refresh", json={"refresh_token": fake_refresh})
    assert response.status_code == 401
    assert "User not found" in response.json()["detail"]
