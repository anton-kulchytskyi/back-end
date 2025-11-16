from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_repository import BaseRepository
from app.models.company_member import CompanyMember


class CompanyMemberRepository(BaseRepository[CompanyMember]):
    """Repository for CompanyMember model with custom methods."""

    def __init__(self):
        super().__init__(CompanyMember)

    async def get_member(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> CompanyMember | None:
        """
        Get company member by company_id and user_id.
        """
        stmt = select(CompanyMember).where(
            CompanyMember.company_id == company_id, CompanyMember.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_role(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> str | None:
        """
        Get user's role in the company.
        """
        member = await self.get_member(db, company_id, user_id)
        return member.role if member else None


# Create instance
company_member_repository = CompanyMemberRepository()
