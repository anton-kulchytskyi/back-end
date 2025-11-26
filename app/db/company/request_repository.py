from sqlalchemy.ext.asyncio import AsyncSession

from app.db.company.base_relation_repository import BaseRelationRepository
from app.models import Request


class RequestRepository(BaseRelationRepository[Request]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Request, session=session)
