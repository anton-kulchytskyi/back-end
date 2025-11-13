import secrets

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    PermissionDeniedException,
    ServiceException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.core.logger import logger
from app.core.security import hash_password
from app.db.user_repository import user_repository
from app.models.user import User
from app.schemas.user import SignUpRequest, UserUpdateRequest


class UserService:
    """Service layer for user operations."""

    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        full_name: str | None = None,
        password: str | None = None,
        is_external: bool = False,
    ) -> User:
        """
        Create a new user (supports both manual and external creation).
        If password is not provided, generates a random one (e.g. for Auth0 users).
        """
        try:
            existing_user = await user_repository.get_by_email(db, email)
            if existing_user:
                raise UserAlreadyExistsException(email)

            if not password:
                password = secrets.token_urlsafe(32)

            hashed_password = hash_password(password)
            user = User(
                email=email,
                full_name=full_name or email.split("@")[0].capitalize(),
                hashed_password=hashed_password,
            )
            created_user = await user_repository.create_one(db, user)

            logger.info(
                f"Created new {'Auth0' if is_external else 'local'} user: {email}"
            )
            return created_user

        except IntegrityError:
            logger.error(f"User with email={email} already exists (IntegrityError)")
            raise UserAlreadyExistsException(email)
        except UserAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"Error creating user {email}: {str(e)}")
            raise ServiceException("Failed to create user")

    async def register_user(self, db: AsyncSession, user_data: SignUpRequest) -> User:
        """Register new user."""
        return await self.create_user(
            db, user_data.email, user_data.full_name, user_data.password
        )

    async def get_all_users(self, db: AsyncSession, skip: int, limit: int):
        """Return paginated list of users."""
        try:
            return await user_repository.get_all(db, skip, limit)
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            raise ServiceException("Failed to retrieve users")

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> User:
        """Return user by ID or raise if not found."""
        try:
            user = await user_repository.get_one(db, user_id)
            if not user:
                raise UserNotFoundException(user_id)
            return user
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving user by id={user_id}: {str(e)}")
            raise ServiceException("Error fetching user data")

    async def get_user_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Return user by email or None if not found."""
        try:
            return await user_repository.get_by_email(db, email)
        except Exception as e:
            logger.error(f"Error fetching user by email={email}: {str(e)}")
            raise ServiceException("Error fetching user data")

    async def update_user(
        self,
        db: AsyncSession,
        user: User,
        user_data: UserUpdateRequest,
        current_user_id: int,
    ) -> User:
        """Update user info and hash password if provided. Users can only update their own profile."""
        try:
            # Permission check: user can only update their own profile
            if current_user_id != user.id:
                raise PermissionDeniedException(
                    detail="You can only edit your own profile"
                )

            update_data = user_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                if field == "password":
                    continue
                setattr(user, field, value)

            if user_data.password:
                user.hashed_password = hash_password(user_data.password)

            return await user_repository.update_one(db, user)

        except PermissionDeniedException:
            raise

        except Exception as e:
            logger.error(f"Error updating user {user.id}: {str(e)}")
            raise ServiceException("Failed to update user")

    async def delete_user(self, db: AsyncSession, user: User, current_user_id: int):
        """Delete user by ID. Users can only delete their own profile."""
        try:
            # Permission check: user can only delete their own profile
            if current_user_id != user.id:
                raise PermissionDeniedException(
                    detail="You can only delete your own profile"
                )

            await user_repository.delete_one(db, user)

        except PermissionDeniedException:
            raise

        except Exception as e:
            logger.error(f"Error deleting user {user.id}: {str(e)}")
            raise ServiceException("Failed to delete user")


user_service = UserService()
