import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth0 import Auth0Error, get_email_from_auth0_token, verify_auth0_token
from app.core.exceptions import ServiceException, UnauthorizedException
from app.core.logger import logger
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.user_repository import user_repository
from app.models.user import User


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

            logger.info(f"User authenticated successfully: {email}")

            return {"access_token": access_token, "token_type": "bearer"}

        except UnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {str(e)}")
            raise ServiceException("Authentication failed")

    async def authenticate_with_auth0(
        self, db: AsyncSession, auth0_token: str
    ) -> dict[str, str]:
        """
        Authenticate user with Auth0 token and return our JWT token.
        Creates user automatically if not exists.
        """
        try:
            # Verify Auth0 token and extract email
            try:
                verify_auth0_token(auth0_token)
            except Auth0Error as e:
                logger.warning(f"Auth0 token verification failed: {str(e)}")
                raise UnauthorizedException(f"Invalid Auth0 token: {str(e)}")

            email = get_email_from_auth0_token(auth0_token)
            if not email:
                logger.warning("No email found in Auth0 token")
                raise UnauthorizedException("Email not found in Auth0 token")

            # Get or create user
            user = await user_repository.get_by_email(db, email)
            if not user:
                logger.info(f"Auth0 user not found, creating new user: {email}")
                user = await self._create_user_from_auth0(db, email)

            # Create our access token
            access_token = create_access_token(data={"sub": str(user.id)})

            logger.info(f"User logged in via Auth0: {user.email}")

            return {"access_token": access_token, "token_type": "bearer"}

        except UnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"Error during Auth0 authentication: {str(e)}")
            raise ServiceException("Auth0 authentication failed")

    async def _create_user_from_auth0(self, db: AsyncSession, email: str) -> User:
        """
        Create a new user from Auth0 email.
        Generates random password for Auth0 users.
        """
        try:
            random_password = secrets.token_urlsafe(32)
            hashed_password = hash_password(random_password)
            full_name = email.split("@")[0].capitalize()

            user = User(
                email=email,
                full_name=full_name,
                hashed_password=hashed_password,
            )

            created_user = await user_repository.create_one(db, user)

            logger.info(f"Created new user from Auth0: {email}")
            return created_user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user from Auth0 email {email}: {str(e)}")
            raise ServiceException("Failed to create user from Auth0")

    async def get_current_user_from_token(self, db: AsyncSession, token: str) -> User:
        """
        Get current user from JWT token.
        """
        try:
            payload = decode_access_token(token)
            if payload is None:
                logger.warning("Token validation failed: invalid token")
                raise UnauthorizedException("Invalid or expired token")

            user_id: str = payload.get("sub")
            if user_id is None:
                logger.warning("Token validation failed: missing subject")
                raise UnauthorizedException("Token missing user identifier")

            user = await user_repository.get_one(db, int(user_id))
            if not user:
                logger.warning(f"Token validation failed: user {user_id} not found")
                raise UnauthorizedException("User not found")

            logger.debug(f"User authenticated from token: {user.email}")
            return user

        except UnauthorizedException:
            raise
        except ValueError:
            logger.warning("Token validation failed: invalid user_id format")
            raise UnauthorizedException("Invalid token format")
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            raise UnauthorizedException("Token validation failed")


auth_service = AuthService()
