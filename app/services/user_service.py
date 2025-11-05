from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.security import hash_password
from app.db.user_repository import user_repository
from app.models.user import User
from app.schemas.user import SignUpRequest, UserUpdateRequest


class UserService:
    @staticmethod
    async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100):
        """Fetch users via repository."""
        return await user_repository.get_all(db, skip, limit)

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        user = await user_repository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    @staticmethod
    async def register_user(db: AsyncSession, user_data: SignUpRequest) -> User:
        """Register a new user."""
        existing = await user_repository.get_by_email(db, user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {user_data.email} already exists",
            )

        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
        )

        try:
            created_user = await user_repository.create(db, user)
            logger.info(f"Created user: {created_user.email}")
            return created_user
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User already exists"
            )

    @staticmethod
    async def update_user(
        db: AsyncSession, user: User, user_data: UserUpdateRequest
    ) -> User:
        """Update existing user fields."""
        if user_data.password:
            user.hashed_password = hash_password(user_data.password)

        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key != "password":
                setattr(user, key, value)

        await user_repository.update(db, user)
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user: User):
        await user_repository.delete(db, user)
        return True


user_service = UserService()
