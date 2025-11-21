from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_repository import BaseRepository
from app.enums.status import Status

T = TypeVar("T")


class BaseRelationRepository(BaseRepository[T]):
    def __init__(self, model: type[T], session: AsyncSession):
        super().__init__(model=model, session=session)

    async def get_by_company(
        self,
        company_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Status | None = None,
    ) -> tuple[list[T], int]:
        conditions = [self.model.company_id == company_id]

        if status:
            conditions.append(self.model.status == status)

        order = [self.model.created_at.desc()]

        return await self.get_many_by_filters(
            *conditions,
            skip=skip,
            limit=limit,
            order_by=order,
        )

    async def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Status | None = None,
    ) -> tuple[list[T], int]:
        conditions = [self.model.user_id == user_id]

        if status:
            conditions.append(self.model.status == status)

        order = [self.model.created_at.desc()]

        return await self.get_many_by_filters(
            *conditions,
            skip=skip,
            limit=limit,
            order_by=order,
        )

    async def get_pending_by_company_and_user(
        self, company_id: int, user_id: int
    ) -> T | None:
        conditions = [
            self.model.company_id == company_id,
            self.model.user_id == user_id,
            self.model.status == Status.PENDING,
        ]

        return await self.get_one_by_filters(*conditions)
