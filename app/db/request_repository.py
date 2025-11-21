from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_relation_repository import BaseRelationRepository
from app.models.request import Request


class RequestRepository(BaseRelationRepository[Request]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Request, session=session)
