from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base.base_repository import BaseRepository
from app.models import Quiz, QuizQuestion


class QuizRepository(BaseRepository[Quiz]):
    """Repository for Quiz model with company-specific operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=Quiz, session=session)

    async def get_by_company(
        self, company_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[Quiz], int]:
        """Retrieve quizzes by company with pagination."""

        return await self.get_many_by_filters(
            Quiz.company_id == company_id,
            skip=skip,
            limit=limit,
            order_by=[Quiz.created_at.desc()],
            options=[selectinload(Quiz.attempts)],
        )

    async def get_with_relations(self, quiz_id: int) -> Optional[Quiz]:
        """Retrieve quiz with all relations eagerly loaded (questions + answers)."""

        return await self.get_one_by_filters(
            Quiz.id == quiz_id,
            options=[
                selectinload(Quiz.questions).selectinload(QuizQuestion.answers),
                selectinload(Quiz.attempts),
            ],
        )

    async def get_by_id_and_company(
        self, quiz_id: int, company_id: int
    ) -> Optional[Quiz]:
        """Retrieve quiz only if it belongs to the specified company."""

        return await self.get_one_by_filters(
            Quiz.id == quiz_id, Quiz.company_id == company_id
        )

    async def count_by_company(self, company_id: int) -> int:
        """Count total quizzes in a company."""

        return await self.count_by_filters(Quiz.company_id == company_id)

    async def refresh_after_create_or_update(self, quiz: Quiz) -> Quiz:
        """Refreshes a persistent Quiz object and ensures full eager loading."""

        await self.session.refresh(quiz)

        return quiz
