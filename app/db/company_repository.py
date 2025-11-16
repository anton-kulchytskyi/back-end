from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_repository import BaseRepository
from app.models.company import Company


class CompanyRepository(BaseRepository[Company]):
    """Repository for Company model with custom methods."""

    def __init__(self):
        super().__init__(Company)

    async def get_by_owner(
        self, db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 10
    ) -> tuple[list[Company], int]:
        """
        Get all companies owned by a specific user (paginated).
        """
        count_stmt = select(Company).where(Company.owner_id == owner_id)
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        stmt = (
            select(Company)
            .where(Company.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .order_by(Company.created_at.desc())
        )
        result = await db.execute(stmt)
        companies = result.scalars().all()

        return list(companies), total

    async def get_visible_companies(
        self, db: AsyncSession, skip: int = 0, limit: int = 10
    ) -> tuple[list[Company], int]:
        """
        Get all visible companies (paginated).
        """
        count_stmt = select(Company).where(Company.is_visible == True)  # noqa: E712
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        stmt = (
            select(Company)
            .where(Company.is_visible == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
            .order_by(Company.created_at.desc())
        )
        result = await db.execute(stmt)
        companies = result.scalars().all()

        return list(companies), total


# Create instance
company_repository = CompanyRepository()
