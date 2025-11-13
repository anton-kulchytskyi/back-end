from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth0 import Auth0Error, get_email_from_auth0_token, verify_auth0_token
from app.core.exceptions import ServiceException, UnauthorizedException
from app.core.logger import logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    verify_password,
)
from app.db.user_repository import user_repository
from app.models.user import User
from app.services.user_service import user_service


class AuthService:
    """Service for authentication operations."""

    async def authenticate_with_credentials(
        self, db: AsyncSession, email: str, password: str
    ) -> dict[str, str]:
        """
        Authenticate user with email and password.
        """
        try:
            user = await user_repository.get_by_email(db, email)

            if not user:
                logger.debug(
                    f"Authentication failed: user with email {email} not found"
                )
                raise UnauthorizedException("Invalid email or password")

            if not verify_password(password, user.hashed_password):
                logger.debug(
                    f"Authentication failed: invalid password for user {email}"
                )
                raise UnauthorizedException("Invalid email or password")

            access_token = create_access_token(data={"sub": str(user.id)})
            refresh_token = create_refresh_token(data={"sub": str(user.id)})

            logger.info(f"User authenticated successfully: {email}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

        except UnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {str(e)}")
            raise ServiceException("Authentication failed")

    async def get_current_user_from_token(self, db: AsyncSession, token: str) -> User:
        """
        Get current user from token.
        Supports both our JWT tokens (HS256) and Auth0 tokens (RS256).
        """
        user = await self._try_get_user_from_jwt(db, token)
        if user:
            return user

        user = await self._try_get_user_from_auth0(db, token)
        if user:
            return user

        raise UnauthorizedException("Could not validate credentials")

    async def _try_get_user_from_jwt(self, db: AsyncSession, token: str) -> User | None:
        """
        Try to authenticate user with our JWT token.
        Returns User if successful, None if token is not valid JWT.
        """
        try:
            payload = decode_access_token(token)
            if not payload:
                return None

            user_id = payload.get("sub")
            if not user_id:
                logger.debug("JWT token missing user ID")
                return None

            user = await user_repository.get_one(db, int(user_id))
            if not user:
                logger.debug(f"User with ID {user_id} not found")
                return None

            logger.debug(f"User authenticated from JWT token: {user.email}")
            return user

        except ValueError as e:
            logger.debug(f"JWT token validation failed: {str(e)}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error validating JWT token: {str(e)}")
            return None

    async def _try_get_user_from_auth0(
        self, db: AsyncSession, token: str
    ) -> User | None:
        """
        Try to authenticate user with Auth0 token.
        Returns User if successful, None if token is not valid Auth0 token.
        Auto-creates user if they don't exist.
        """
        try:
            verify_auth0_token(token)
            email = get_email_from_auth0_token(token)

            if not email:
                logger.warning("No email found in Auth0 token")
                return None

            user = await user_repository.get_by_email(db, email)
            if not user:
                logger.info(f"Auth0 user not found, creating new user: {email}")
                user = await user_service.create_user(db, email, is_external=True)
            else:
                logger.debug(f"User authenticated from Auth0 token: {user.email}")

            return user

        except Auth0Error as e:
            logger.debug(f"Auth0 token verification failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error validating Auth0 token: {str(e)}")
            return None

    async def refresh_access_token(
        self, db: AsyncSession, refresh_token: str
    ) -> dict[str, str]:
        """
        Refresh user's access and refresh tokens.

        Validates the provided refresh token, retrieves the user,
        and issues new access and refresh tokens.
        """
        payload = decode_refresh_token(refresh_token)
        if not payload:
            raise UnauthorizedException("Invalid or expired refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid refresh token payload")

        user = await user_repository.get_one(db, int(user_id))
        if not user:
            raise UnauthorizedException("User not found")

        new_access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        logger.info(f"Issued new tokens for user {user.email}")

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }


auth_service = AuthService()
