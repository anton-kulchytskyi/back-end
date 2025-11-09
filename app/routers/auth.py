"""
Authentication and authorization endpoints.
Handles user login, registration, and token management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import Auth0LoginRequest, TokenResponse
from app.schemas.user import SignUpRequest, UserDetailResponse
from app.services.auth_service import AuthService
from app.services.deps import get_auth_service, get_user_service
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=UserDetailResponse, status_code=201)
async def register(
    user_data: SignUpRequest,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
):
    """
    Register a new user.

    - **email**: User email (must be unique)
    - **password**: User password (will be hashed automatically)
    - **full_name**: User full name
    """
    return await user_service.register_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login with email and password to get access token.

    - **username**: User email (OAuth2 standard uses 'username' field)
    - **password**: User password

    Returns JWT access token for authentication.
    """
    result = await auth_service.authenticate_with_credentials(
        db, form_data.username, form_data.password
    )
    return TokenResponse(**result)


@router.get("/me", response_model=UserDetailResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return current_user


@router.post("/auth0/login", response_model=TokenResponse)
async def auth0_login(
    request: Auth0LoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login with Auth0 token.

    - **token**: Valid Auth0 JWT access token

    Returns JWT access token for our application.
    User will be created automatically if not exists.
    """
    result = await auth_service.authenticate_with_auth0(db, request.token)
    return TokenResponse(**result)
