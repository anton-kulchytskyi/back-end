from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.deps import get_auth_service

# HTTPBearer scheme for token authentication
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Dependency to get current authenticated user from token.

    Supports both authentication methods:
    - JWT token (HS256) from POST /auth/login
    - Auth0 token (RS256) from Auth0 flow
    """
    token = credentials.credentials
    return await auth_service.get_current_user_from_token(db, token)
