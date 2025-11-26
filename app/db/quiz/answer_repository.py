from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base.base_repository import BaseRepository
from app.models import QuizAnswer


class QuizAnswerRepository(BaseRepository[QuizAnswer]):
    """Repository for QuizAnswer model with batch operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=QuizAnswer, session=session)
