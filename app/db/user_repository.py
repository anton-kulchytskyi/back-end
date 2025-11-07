from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_repository import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Find a user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


user_repository = UserRepository()
