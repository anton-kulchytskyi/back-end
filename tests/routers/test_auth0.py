from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

# ==================== AUTH0 MOCK TESTS ====================


async def test_auth0_token_creates_new_user(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    def mock_verify_auth0_token(token: str):
        return {
            "sub": "auth0|mock_new_user_123",
            "email": "newauth0user@example.com",
            "iss": "https://mock.auth0.com/",
            "aud": "mock-audience",
        }

    def mock_get_email_from_auth0_token(token: str):
        return "newauth0user@example.com"

    monkeypatch.setattr(
        "app.services.users.auth_service.verify_auth0_token", mock_verify_auth0_token
    )
    monkeypatch.setattr(
        "app.services.users.auth_service.get_email_from_auth0_token",
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

    from app.db.user.user_repository import UserRepository

    user_repository = UserRepository(db_session)

    user = await user_repository.get_by_email("newauth0user@example.com")
    assert user is not None
    assert user.email == "newauth0user@example.com"
    assert user.is_active is True


async def test_auth0_token_existing_user(
    client: AsyncClient, test_user: User, monkeypatch
):
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
        "app.services.users.auth_service.verify_auth0_token", mock_verify_auth0_token
    )
    monkeypatch.setattr(
        "app.services.users.auth_service.get_email_from_auth0_token",
        mock_get_email_from_auth0_token,
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer mock_auth0_token_existing"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


async def test_auth0_token_no_email(client: AsyncClient, monkeypatch):
    def mock_verify_auth0_token(token: str):
        return {
            "sub": "auth0|no_email_123",
            "iss": "https://mock.auth0.com/",
            "aud": "mock-audience",
        }

    def mock_get_email_from_auth0_token(token: str):
        return None

    monkeypatch.setattr(
        "app.services.users.auth_service.verify_auth0_token", mock_verify_auth0_token
    )
    monkeypatch.setattr(
        "app.services.users.auth_service.get_email_from_auth0_token",
        mock_get_email_from_auth0_token,
    )
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer mock_token_no_email"}
    )

    assert response.status_code == 401


async def test_auth0_token_invalid(client: AsyncClient, monkeypatch):
    from app.core.auth0 import Auth0Error

    def mock_verify_auth0_token(token: str):
        raise Auth0Error("Invalid Auth0 token: signature verification failed")

    monkeypatch.setattr(
        "app.services.users.auth_service.verify_auth0_token", mock_verify_auth0_token
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401
