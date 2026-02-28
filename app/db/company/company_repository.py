from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base.base_repository import BaseRepository
from app.models import Company


class CompanyRepository(BaseRepository[Company]):
    """Repository for Company model with custom methods."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=Company, session=session)

    async def get_by_owner(
        self, owner_id: int, skip: int = 0, limit: int = 10
    ) -> tuple[list[Company], int]:
        """
        Get all companies owned by a specific user (paginated).
        """
        conditions = [Company.owner_id == owner_id]
        order = [Company.created_at.desc()]

        return await self.get_many_by_filters(
            *conditions, skip=skip, limit=limit, order_by=order
        )

    async def get_visible_companies(
        self, skip: int = 0, limit: int = 10
    ) -> tuple[list[Company], int]:
        """
        Get all visible companies (paginated).
        """
        conditions = [Company.is_visible.is_(True)]
        order = [Company.created_at.desc()]

        return await self.get_many_by_filters(
            *conditions, skip=skip, limit=limit, order_by=order
        )
