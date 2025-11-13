import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

# ==================== AUTH0 MOCK TESTS ====================


@pytest.mark.asyncio
async def test_auth0_token_creates_new_user(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Test GET /auth/me with Auth0 token - auto-creates new user"""

    def mock_verify_auth0_token(token: str):
        """Simulate successful Auth0 token verification"""
        return {
            "sub": "auth0|mock_new_user_123",
            "email": "newauth0user@example.com",
            "iss": "https://mock.auth0.com/",
            "aud": "mock-audience",
        }

    def mock_get_email_from_auth0_token(token: str):
        """Simulate email extraction from Auth0 token"""
        return "newauth0user@example.com"

    monkeypatch.setattr(
        "app.services.auth_service.verify_auth0_token", mock_verify_auth0_token
    )
    monkeypatch.setattr(
        "app.services.auth_service.get_email_from_auth0_token",
        mock_get_email_from_auth0_token,
    )
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer mock_auth0_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newauth0user@example.com"
    assert data["full_name"] == "Newauth0user"
    assert data["is_active"] is True

    from app.db.user_repository import user_repository

    user = await user_repository.get_by_email(db_session, "newauth0user@example.com")
    assert user is not None
    assert user.email == "newauth0user@example.com"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_auth0_token_existing_user(
    client: AsyncClient, test_user: User, monkeypatch
):
    """Test GET /auth/me with Auth0 token - uses existing user (no duplicate)"""

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

    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer mock_auth0_token_existing"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_auth0_token_no_email(client: AsyncClient, monkeypatch):
    """Test GET /auth/me - Auth0 token without email claim"""

    def mock_verify_auth0_token(token: str):
        return {
            "sub": "auth0|no_email_123",
            "iss": "https://mock.auth0.com/",
            "aud": "mock-audience",
        }

    def mock_get_email_from_auth0_token(token: str):
        return None

    monkeypatch.setattr(
        "app.services.auth_service.verify_auth0_token", mock_verify_auth0_token
    )
    monkeypatch.setattr(
        "app.services.auth_service.get_email_from_auth0_token",
        mock_get_email_from_auth0_token,
    )
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer mock_token_no_email"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth0_token_invalid(client: AsyncClient, monkeypatch):
    """Test GET /auth/me - invalid Auth0 token"""
    from app.core.auth0 import Auth0Error

    def mock_verify_auth0_token(token: str):
        raise Auth0Error("Invalid Auth0 token: signature verification failed")

    monkeypatch.setattr(
        "app.services.auth_service.verify_auth0_token", mock_verify_auth0_token
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401
