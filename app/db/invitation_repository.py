from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_repository import BaseRepository
from app.enums.status import Status
from app.models.invitation import Invitation


class InvitationRepository(BaseRepository[Invitation]):
    """Repository for Invitation model with custom methods."""

    def __init__(self):
        super().__init__(Invitation)

    async def get_by_company(
        self,
        db: AsyncSession,
        company_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Status | None = None,
    ) -> tuple[list[Invitation], int]:
        """
        Get all invitations sent by company (paginated).
        """
        base_query = select(Invitation).where(Invitation.company_id == company_id)
        if status:
            base_query = base_query.where(Invitation.status == status)

        total = await self._count(db, base_query)

        stmt = (
            base_query.order_by(Invitation.created_at.desc()).offset(skip).limit(limit)
        )
        result = await db.execute(stmt)
        invitations = list(result.scalars().all())

        return invitations, total

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Status | None = None,
    ) -> tuple[list[Invitation], int]:
        """
        Get all invitations received by user (paginated).
        """

        base_query = select(Invitation).where(Invitation.user_id == user_id)
        if status:
            base_query = base_query.where(Invitation.status == status)

        total = await self._count(db, base_query)

        stmt = (
            base_query.order_by(Invitation.created_at.desc()).offset(skip).limit(limit)
        )
        result = await db.execute(stmt)
        invitations = list(result.scalars().all())

        return invitations, total

    async def get_pending_by_company_and_user(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> Invitation | None:
        """
        Get pending invitation for specific company and user.
        """
        stmt = select(Invitation).where(
            Invitation.company_id == company_id,
            Invitation.user_id == user_id,
            Invitation.status == Status.PENDING,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# Create instance
invitation_repository = InvitationRepository()
