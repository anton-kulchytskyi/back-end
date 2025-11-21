from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_relation_repository import BaseRelationRepository
from app.models.invitation import Invitation


class InvitationRepository(BaseRelationRepository[Invitation]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Invitation, session=session)
