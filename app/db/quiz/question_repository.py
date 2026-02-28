from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base.base_repository import BaseRepository
from app.models import QuizQuestion


class QuizQuestionRepository(BaseRepository[QuizQuestion]):
    """Repository for QuizQuestion model with quiz-specific operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=QuizQuestion, session=session)
