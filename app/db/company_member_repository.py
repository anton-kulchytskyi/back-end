from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_repository import BaseRepository
from app.models.company_member import CompanyMember


class CompanyMemberRepository(BaseRepository[CompanyMember]):
    """Repository for CompanyMember model with custom methods."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=CompanyMember, session=session)

    async def get_members_by_company(
        self, company_id: int, skip: int = 0, limit: int = 10
    ) -> tuple[list[CompanyMember], int]:
        conditions = [CompanyMember.company_id == company_id]
        order = [
            CompanyMember.role.desc(),
            CompanyMember.created_at.asc(),
        ]

        return await self.get_many_by_filters(
            *conditions, skip=skip, limit=limit, order_by=order
        )

    async def get_member_by_ids(
        self, company_id: int, user_id: int
    ) -> CompanyMember | None:
        """
        Get company member by company_id and user_id.
        """
        conditions = [
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user_id,
        ]

        return await self.get_one_by_filters(*conditions)

    async def get_user_role(self, company_id: int, user_id: int) -> str | None:
        """
        Get user's role in the company.
        """
        member = await self.get_member_by_ids(company_id, user_id)
        return member.role if member else None
