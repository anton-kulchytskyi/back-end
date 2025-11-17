from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_repository import BaseRepository
from app.enums.status import Status
from app.models.request import Request


class RequestRepository(BaseRepository[Request]):
    """Repository for Request model with custom methods."""

    def __init__(self):
        super().__init__(Request)

    async def get_by_company(
        self,
        db: AsyncSession,
        company_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Status | None = None,
    ) -> tuple[list[Request], int]:
        """
        Get all membership requests to company (paginated).
        """
        base_query = select(Request).where(Request.company_id == company_id)
        if status:
            base_query = base_query.where(Request.status == status)

        total = await self._count(db, base_query)

        stmt = base_query.order_by(Request.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        requests = list(result.scalars().all())

        return requests, total

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Status | None = None,
    ) -> tuple[list[Request], int]:
        """
        Get all membership requests sent by user (paginated).
        """
        base_query = select(Request).where(Request.user_id == user_id)
        if status:
            base_query = base_query.where(Request.status == status)

        total = await self._count(db, base_query)

        stmt = base_query.order_by(Request.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        requests = list(result.scalars().all())

        return requests, total

    async def get_pending_by_company_and_user(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> Request | None:
        """
        Get pending request for specific company and user.

        Used to check if request already exists before creating new one.
        """
        stmt = select(Request).where(
            Request.company_id == company_id,
            Request.user_id == user_id,
            Request.status == Status.PENDING,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# Create instance
request_repository = RequestRepository()
