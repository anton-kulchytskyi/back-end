from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ServiceException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.core.logger import logger
from app.core.security import hash_password, verify_password
from app.db.user_repository import user_repository
from app.models.user import User
from app.schemas.user import SignUpRequest, UserUpdateRequest


class UserService:
    """Service layer for user operations."""

    async def register_user(self, db: AsyncSession, user_data: SignUpRequest) -> User:
        """Register new user with password hashing and duplicate check."""
        try:
            existing_user = await user_repository.get_by_email(db, user_data.email)
            if existing_user:
                raise UserAlreadyExistsException(user_data.email)

            hashed_password = hash_password(user_data.password)
            user = User(
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
            )
            return await user_repository.create_one(db, user)

        except IntegrityError:
            await db.rollback()
            logger.error(
                f"User with email={user_data.email} already exists (IntegrityError)"
            )
            raise UserAlreadyExistsException(user_data.email)

        except UserAlreadyExistsException:
            raise

        except Exception as e:
            await db.rollback()
            logger.error(f"Error registering user: {str(e)}")
            raise ServiceException("Failed to create user")

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

    async def update_user(
        self, db: AsyncSession, user: User, user_data: UserUpdateRequest
    ) -> User:
        """Update user info and hash password if provided."""
        try:
            update_data = user_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                if field == "password":
                    continue
                setattr(user, field, value)

            if user_data.password:
                user.hashed_password = hash_password(user_data.password)

            return await user_repository.update_one(db, user)

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user {user.id}: {str(e)}")
            raise ServiceException("Failed to update user")

    async def delete_user(self, db: AsyncSession, user: User):
        """Delete user by ID."""
        try:
            await user_repository.delete_one(db, user)
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting user {user.id}: {str(e)}")
            raise ServiceException("Failed to delete user")

    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> User | None:
        try:
            # Get user by email
            user = await UserService.get_user_by_email(db, email)

            if not user:
                logger.debug(
                    f"Authentication failed: user with email {email} not found"
                )
                return None

            # Verify password
            if not verify_password(password, user.hashed_password):
                logger.debug(
                    f"Authentication failed: invalid password for user {email}"
                )
                return None

            logger.info(f"User authenticated successfully: {email}")
            return user

        except Exception as e:
            logger.error(f"Error authenticating user {email}: {str(e)}")
            return None


user_service = UserService()
