import secrets

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ServiceException,
)
from app.core.logger import logger
from app.core.security import hash_password
from app.core.unit_of_work import AbstractUnitOfWork
from app.models.user import User
from app.schemas.pagination import PaginationBaseSchema
from app.schemas.user import (
    SignUpRequest,
    UserDetailResponse,
    UsersListResponse,
    UserUpdateRequest,
)
from app.utils.pagination import paginate_query


class UserService:
    """Service layer for user operations."""

    def __init__(self, uow: AbstractUnitOfWork):
        self._uow = uow

    async def create_user(
        self,
        email: str,
        full_name: str | None = None,
        password: str | None = None,
        is_external: bool = False,
    ) -> User:
        """
        Create a new user (supports both manual and external creation).
        If password is not provided, generates a random one (e.g. for Auth0 users).
        """
        async with self._uow:
            try:
                existing_user = await self._uow.users.get_by_email(email)
                if existing_user:
                    raise ConflictException(f"User with email {email} already exists")

                if not password:
                    password = secrets.token_urlsafe(32)

                hashed_password = hash_password(password)
                user = User(
                    email=email,
                    full_name=full_name or email.split("@")[0].capitalize(),
                    hashed_password=hashed_password,
                )
                created_user = await self._uow.users.create_one(user)

                await self._uow.commit()

                logger.info(
                    f"Created new {'Auth0' if is_external else 'local'} user: {email}"
                )
                return created_user

            except IntegrityError:
                logger.error(f"User with email={email} already exists (IntegrityError)")
                raise ConflictException(f"User with email {email} already exists")
            except ConflictException:
                raise
            except Exception as e:
                logger.error(f"Error creating user {email}: {str(e)}")
                raise ServiceException("Failed to create user")

    async def register_user(self, user_data: SignUpRequest) -> User:
        """Register new user."""
        return await self.create_user(
            user_data.email, user_data.full_name, user_data.password
        )

    async def get_users_paginated(
        self,
        pagination: PaginationBaseSchema,
    ) -> UsersListResponse:
        """
        Повертає пагінований список користувачів у уніфікованому форматі.
        Використовує загальну утиліту paginate_query.
        """
        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.users.get_all(skip, limit)

                paginated_result = await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=UsersListResponse,
                    item_schema=UserDetailResponse,
                )

                return paginated_result

            except Exception as e:
                logger.error(f"Error fetching paginated users: {e}")
                raise ServiceException("Failed to retrieve users")

    async def get_user_by_id(self, user_id: int) -> User:
        """Return user by ID or raise if not found."""
        async with self._uow:
            try:
                user = await self._uow.users.get_one_by_id(user_id)
                if not user:
                    raise NotFoundException(f"User with id={user_id} not found")
                return user
            except NotFoundException:
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error retrieving user by id={user_id}: {str(e)}"
                )
                raise ServiceException("Error fetching user data")

    async def get_user_by_email(self, email: str) -> User | None:
        """Return user by email or None if not found."""
        async with self._uow:
            try:
                return await self._uow.users.get_by_email(email)
            except Exception as e:
                logger.error(f"Error fetching user by email={email}: {str(e)}")
                raise ServiceException("Error fetching user data")

    async def update_user(
        self,
        user: User,
        user_data: UserUpdateRequest,
        current_user_id: int,
    ) -> User:
        """Update user info. User can only update their own profile."""
        async with self._uow:
            try:
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

                updated_user = await self._uow.users.update_one(user)

                await self._uow.commit()

                return updated_user

            except PermissionDeniedException:
                raise
            except Exception as e:
                logger.error(f"Error updating user {user.id}: {str(e)}")
                raise ServiceException("Failed to update user")

    async def delete_user(self, user: User, current_user_id: int):
        """Delete user by ID. Users can only delete their own profile."""
        async with self._uow:
            try:
                if current_user_id != user.id:
                    raise PermissionDeniedException(
                        detail="You can only delete your own profile"
                    )

                await self._uow.users.delete_one(user)

                await self._uow.commit()

            except PermissionDeniedException:
                raise
            except Exception as e:
                logger.error(f"Error deleting user {user.id}: {str(e)}")
                raise ServiceException("Failed to delete user")
