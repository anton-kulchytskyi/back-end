from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.user import User


class UserRepository:
    @staticmethod
    async def get_all(
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> tuple[list[User], int]:
        """Get all users with pagination."""
        try:
            count_query = select(func.count(User.id))
            total = (await db.execute(count_query)).scalar_one()

            query = select(User).offset(skip).limit(limit)
            result = await db.execute(query)
            users = result.scalars().all()

            return users, total
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            raise

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user: User) -> User:
        """Insert a new user into DB."""
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update(db: AsyncSession, user: User) -> User:
        """Commit updated user."""
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        """Delete a user."""
        await db.delete(user)
        await db.commit()


user_repository = UserRepository()
