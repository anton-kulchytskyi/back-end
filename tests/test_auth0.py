import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

# ==================== AUTH0 MOCK TESTS ====================


@pytest.mark.asyncio
async def test_auth0_login_creates_new_user(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    # Mock Auth0 verification functions
    def mock_verify_auth0_token(token: str):
        return {
            "sub": "auth0|mock_new_user_123",
            "email": "newauth0user@example.com",
            "iss": "https://mock.auth0.com/",
            "aud": "mock-audience",
        }

    def mock_get_email_from_auth0_token(token: str):
        return "newauth0user@example.com"

    # Apply mocks to auth_service
    monkeypatch.setattr(
        "app.services.auth_service.verify_auth0_token", mock_verify_auth0_token
    )
    monkeypatch.setattr(
        "app.services.auth_service.get_email_from_auth0_token",
        mock_get_email_from_auth0_token,
    )

    # Send Auth0 login request
    auth0_data = {"token": "mock_auth0_token_12345"}
    response = await client.post("/auth/auth0/login", json=auth0_data)

    # Verify successful login
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0

    # Verify user was auto-created in database
    from app.db.user_repository import user_repository

    user = await user_repository.get_by_email(db_session, "newauth0user@example.com")
    assert user is not None
    assert user.email == "newauth0user@example.com"
    assert user.full_name == "Newauth0user"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_auth0_login_existing_user(
    client: AsyncClient, test_user: User, monkeypatch
):
    # Mock Auth0 to return existing user's email
    def mock_verify_auth0_token(token: str):
        return {
            "sub": "auth0|existing_user_456",
            "email": test_user.email,
            "iss": "https://mock.auth0.com/",
            "aud": "mock-audience",
        }

    def mock_get_email_from_auth0_token(token: str):
        return test_user.email

    monkeypatch.setattr(
        "app.services.auth_service.verify_auth0_token", mock_verify_auth0_token
    )
    monkeypatch.setattr(
        "app.services.auth_service.get_email_from_auth0_token",
        mock_get_email_from_auth0_token,
    )

    # Send Auth0 login request
    auth0_data = {"token": "mock_auth0_token_existing"}
    response = await client.post("/auth/auth0/login", json=auth0_data)

    # Verify successful login
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify we can use the token to access /me
    our_token = data["access_token"]
    me_response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {our_token}"}
    )

    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == test_user.email
    assert user_data["id"] == test_user.id


@pytest.mark.asyncio
async def test_auth0_login_no_email_in_token(client: AsyncClient, monkeypatch):
    # Mock Auth0 to return token WITHOUT email
    def mock_verify_auth0_token(token: str):
        return {
            "sub": "auth0|no_email_123",
            "iss": "https://mock.auth0.com/",
            "aud": "mock-audience",
            # No email!
        }

    def mock_get_email_from_auth0_token(token: str):
        return None  # No email found

    monkeypatch.setattr(
        "app.services.auth_service.verify_auth0_token", mock_verify_auth0_token
    )
    monkeypatch.setattr(
        "app.services.auth_service.get_email_from_auth0_token",
        mock_get_email_from_auth0_token,
    )

    # Send Auth0 login request
    auth0_data = {"token": "mock_token_no_email"}
    response = await client.post("/auth/auth0/login", json=auth0_data)

    # Should return 401 (email required)
    assert response.status_code == 401
    assert "email" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_auth0_login_invalid_token(client: AsyncClient, monkeypatch):
    from app.core.auth0 import Auth0Error

    # Mock Auth0 to raise error for invalid token
    def mock_verify_auth0_token(token: str):
        raise Auth0Error("Invalid Auth0 token: signature verification failed")

    monkeypatch.setattr(
        "app.services.auth_service.verify_auth0_token", mock_verify_auth0_token
    )

    # Send Auth0 login request with "invalid" token
    auth0_data = {"token": "invalid_mock_token"}
    response = await client.post("/auth/auth0/login", json=auth0_data)

    # Should return 401
    assert response.status_code == 401
    assert "Invalid Auth0 token" in response.json()["detail"]
