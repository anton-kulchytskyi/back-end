from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base.base_repository import BaseRepository
from app.models import QuizAttempt

MAX_EXPORT_LIMIT = 1_000_000


class QuizAttemptRepository(BaseRepository[QuizAttempt]):
    """Repository for QuizAttempt model with analytics operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=QuizAttempt, session=session)

    async def create_attempt(
        self,
        user_id: int,
        quiz_id: int,
        company_id: int,
        total_questions: int,
    ) -> QuizAttempt:
        """Create a new quiz attempt."""
        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=quiz_id,
            company_id=company_id,
            total_questions=total_questions,
            score=0,  # Will be calculated after answers
        )
        return await self.create_one(attempt)

    async def get_user_attempts_paginated(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        company_id: Optional[int] = None,
        quiz_id: Optional[int] = None,
    ) -> tuple[list[QuizAttempt], int]:
        """Get user's quiz attempts with optional filters and pagination."""
        filters = [
            QuizAttempt.user_id == user_id,
            QuizAttempt.completed_at.isnot(None),  # Only completed attempts
        ]

        if company_id is not None:
            filters.append(QuizAttempt.company_id == company_id)

        if quiz_id is not None:
            filters.append(QuizAttempt.quiz_id == quiz_id)

        return await self.get_many_by_filters(
            *filters,
            skip=skip,
            limit=limit,
            order_by=[QuizAttempt.completed_at.desc()],
            options=[
                selectinload(QuizAttempt.quiz),
                selectinload(QuizAttempt.company),
            ],
        )

    async def calculate_user_global_average(self, user_id: int) -> Optional[float]:
        """
        Calculate user's global average across all completed quizzes.
        Formula: SUM(score) / SUM(total_questions) * 100
        """
        stmt = select(
            func.sum(QuizAttempt.score).label("total_score"),
            func.sum(QuizAttempt.total_questions).label("total_questions"),
        ).where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.completed_at.isnot(None),
        )

        result = await self.session.execute(stmt)
        row = result.one_or_none()

        if not row or row.total_score is None or row.total_questions == 0:
            return None

        return (row.total_score / row.total_questions) * 100.0

    async def calculate_user_company_average(
        self, user_id: int, company_id: int
    ) -> Optional[float]:
        """
        Calculate user's average for a specific company.
        Formula: SUM(score) / SUM(total_questions) * 100
        """
        stmt = select(
            func.sum(QuizAttempt.score).label("total_score"),
            func.sum(QuizAttempt.total_questions).label("total_questions"),
        ).where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.company_id == company_id,
            QuizAttempt.completed_at.isnot(None),
        )

        result = await self.session.execute(stmt)
        row = result.one_or_none()

        if not row or row.total_score is None or row.total_questions == 0:
            return None

        return (row.total_score / row.total_questions) * 100.0

    async def count_user_completed_attempts(
        self,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> int:
        """Count total completed quiz attempts for a user."""
        filters = [
            QuizAttempt.user_id == user_id,
            QuizAttempt.completed_at.isnot(None),
        ]

        if company_id is not None:
            filters.append(QuizAttempt.company_id == company_id)

        return await self.count_by_filters(*filters)

    async def get_user_last_attempt(self, user_id: int) -> Optional[datetime]:
        """Get the timestamp of user's last completed attempt (any quiz)."""
        stmt = (
            select(QuizAttempt.completed_at)
            .where(
                QuizAttempt.user_id == user_id,
                QuizAttempt.completed_at.isnot(None),
            )
            .order_by(QuizAttempt.completed_at.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_details(self, attempt_id: int) -> Optional[QuizAttempt]:
        """Get attempt with all related data (quiz, company, user_answers)."""
        return await self.get_one_by_filters(
            QuizAttempt.id == attempt_id,
            options=[
                selectinload(QuizAttempt.quiz),
                selectinload(QuizAttempt.company),
                selectinload(QuizAttempt.user_answers),
            ],
        )

    async def get_answers_for_export(
        self,
        user_id: int | None = None,
        company_id: int | None = None,
        quiz_id: int | None = None,
    ) -> list[QuizAttempt]:
        filters = [QuizAttempt.completed_at.isnot(None)]

        if user_id is not None:
            filters.append(QuizAttempt.user_id == user_id)

        if company_id is not None:
            filters.append(QuizAttempt.company_id == company_id)

        if quiz_id is not None:
            filters.append(QuizAttempt.quiz_id == quiz_id)

        attempts, _ = await self.get_many_by_filters(
            *filters,
            skip=0,
            limit=MAX_EXPORT_LIMIT,
            order_by=[QuizAttempt.completed_at.desc()],
            options=[
                selectinload(QuizAttempt.user_answers),
                selectinload(QuizAttempt.quiz),
                selectinload(QuizAttempt.company),
            ],
        )

        return attempts
