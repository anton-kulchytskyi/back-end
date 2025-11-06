"""
Authentication and authorization endpoints.
Handles user login, registration, and token management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import (  # ← Змінено
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth0 import Auth0Error, get_email_from_auth0_token, verify_auth0_token
from app.core.database import get_db
from app.core.logger import logger
from app.core.security import create_access_token, decode_access_token
from app.models.user import User
from app.schemas.user import SignUpRequest, UserDetailResponse
from app.services.user_service import UserService

router = APIRouter()

# HTTPBearer scheme for token authentication (simple and works in Swagger)
security = HTTPBearer()  # ← Змінено


@router.post(
    "/register", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: SignUpRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    - **email**: User email (must be unique)
    - **password**: User password (will be hashed automatically)
    - **full_name**: User full name
    """
    try:
        existing_user = await UserService.get_user_by_email(db, user_data.email)
        if existing_user:
            logger.warning(
                f"Registration failed: email {user_data.email} already exists"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = await UserService.create_user(db, user_data)
        logger.info(f"User registered successfully: {user.email}")

        return user

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password to get access token.

    - **username**: User email (OAuth2 standard uses 'username' field)
    - **password**: User password

    Returns JWT access token for authentication.
    """
    try:
        user = await UserService.authenticate_user(
            db, form_data.username, form_data.password
        )

        if not user:
            logger.warning(
                f"Login failed: invalid credentials for {form_data.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": str(user.id)})

        logger.info(f"User logged in successfully: {user.email}")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(security)
    ],  # ← Змінено
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials (Bearer token)
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials  # ← Змінено: витягуємо токен

        payload = decode_access_token(token)
        if payload is None:
            logger.warning("Token validation failed: invalid token")
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token validation failed: missing subject")
            raise credentials_exception

        user = await UserService.get_user_by_id(db, int(user_id))
        if user is None:
            logger.warning(f"Token validation failed: user {user_id} not found")
            raise credentials_exception

        logger.debug(f"User authenticated from token: {user.email}")
        return user

    except HTTPException:
        raise
    except ValueError:
        logger.warning("Token validation failed: invalid user_id format")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise credentials_exception


@router.get("/me", response_model=UserDetailResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    logger.info(f"User info retrieved: {current_user.email}")
    return current_user


class Auth0LoginRequest(BaseModel):
    """Request model for Auth0 login"""

    token: str  # Auth0 JWT token


@router.post("/auth0/login")
async def auth0_login(request: Auth0LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login with Auth0 token.

    - **token**: Valid Auth0 JWT access token

    Returns JWT access token for our application.
    User will be created automatically if not exists.
    """
    try:
        # Verify Auth0 token
        try:
            verify_auth0_token(request.token)
        except Auth0Error as e:
            logger.warning(f"Auth0 token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Auth0 token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract email from token
        email = get_email_from_auth0_token(request.token)
        if not email:
            logger.warning("No email found in Auth0 token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Auth0 token",
            )

        # Check if user exists
        user = await UserService.get_user_by_email(db, email)

        if not user:
            # User doesn't exist - will create in next subtask
            logger.info(f"Auth0 user not found in database: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please register first.",
            )

        # Create access token for our application
        access_token = create_access_token(data={"sub": str(user.id)})

        logger.info(f"User logged in via Auth0: {user.email}")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during Auth0 login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth0 login failed",
        )
