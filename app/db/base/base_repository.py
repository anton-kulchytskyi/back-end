"""Base repository with generic CRUD operations."""

from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Load

from app.core.logger import logger

T = TypeVar("T")  # Generic type for model classes


class BaseRepository(Generic[T]):
    """Generic base repository for CRUD operations."""

    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_one_by_id(self, id_: int) -> Optional[T]:
        """Retrieve one record by Primary Key (ID)."""
        try:
            result = await self.session.get(self.model, id_)
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by id: {e}")
            raise

    async def get_one_by_filters(
        self, *conditions, options: list[Load] | None = None
    ) -> Optional[T]:
        """
        Retrieve a single record by conditions with optional eager-loading.

        """
        try:
            stmt = select(self.model).where(*conditions).limit(1)

            if options:
                stmt = stmt.options(*options)

            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            logger.error(
                f"Error getting single {self.model.__name__} by conditions: {e}"
            )
            raise

    async def create_one(self, obj: T) -> T:
        """Create a new record."""
        try:
            self.session.add(obj)
            await self.session.flush()
            await self.session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise

    async def update_one(self, obj: T) -> T:
        """Update an existing record."""
        try:
            self.session.add(obj)
            await self.session.flush()
            return obj
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise

    async def delete_one(self, obj: T) -> None:
        """Delete a record."""
        try:
            await self.session.delete(obj)  # ← Sync method, no await
            await self.session.flush()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[list[T], int]:
        """Retrieve paginated records and total count."""
        try:
            total_query = await self.session.execute(select(func.count(self.model.id)))
            total = total_query.scalar_one()

            result = await self.session.execute(
                select(self.model).offset(skip).limit(limit)
            )
            items = result.scalars().all()

            return list(items), total
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} list: {e}")
            raise

    async def get_many_by_filters(
        self,
        *conditions,
        skip: int = 0,
        limit: int = 100,
        order_by: list | None = None,
        options: list[Load] | None = None,
    ) -> tuple[list[T], int]:
        """
        Retrieve many records with filtering, ordering, pagination,
        and optional eager-loading options.

        """
        try:
            total = await self.count_by_filters(*conditions)

            stmt = select(self.model).where(*conditions)

            if options:
                stmt = stmt.options(*options)

            if order_by:
                stmt = stmt.order_by(*order_by)

            stmt = stmt.offset(skip).limit(limit)

            rows = await self.session.execute(stmt)
            items = rows.scalars().all()

            return list(items), total
        except SQLAlchemyError as e:
            condition_info = [str(c) for c in conditions]
            logger.error(
                f"Error retrieving {self.model.__name__} items "
                f"(Conditions: {condition_info}, Skip: {skip}, Limit: {limit}): {e}"
            )
            raise

    async def delete_by_filters(self, *conditions) -> int:
        """
        Delete records matching conditions (bulk delete).

        """
        try:
            stmt = delete(self.model).where(*conditions)
            result = await self.session.execute(stmt)
            await self.session.flush()

            return result.rowcount

        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__} by filters: {e}")
            raise

    async def count_by_filters(self, *conditions) -> int:
        """
        Count records matching given conditions.

        """
        try:
            stmt = select(func.count()).select_from(self.model).where(*conditions)
            result = await self.session.execute(stmt)
            return result.scalar_one()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__} by conditions: {e}")
            raise
