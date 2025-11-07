from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger

T = TypeVar("T")  # Generic type for model classes


class BaseRepository(Generic[T]):
    """Generic base repository for CRUD operations."""

    def __init__(self, model: Type[T]):
        self.model = model

    async def get_one(self, db: AsyncSession, id_: int) -> Optional[T]:
        """Retrieve one record by ID."""
        try:
            result = await db.execute(select(self.model).where(self.model.id == id_))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by id: {e}")
            raise

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> tuple[list[T], int]:
        """Retrieve paginated records and total count."""
        try:
            total_query = await db.execute(select(func.count(self.model.id)))
            total = total_query.scalar_one()

            result = await db.execute(select(self.model).offset(skip).limit(limit))
            items = result.scalars().all()

            return items, total
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} list: {e}")
            raise

    async def create_one(self, db: AsyncSession, obj: T) -> T:
        """Create a new record."""
        try:
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise

    async def update_one(self, db: AsyncSession, obj: T) -> T:
        """Update an existing record."""
        try:
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise

    async def delete_one(self, db: AsyncSession, obj: T) -> None:
        """Delete a record."""
        try:
            await db.delete(obj)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            raise
