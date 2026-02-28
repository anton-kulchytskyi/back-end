from datetime import date
from typing import Any

from sqlalchemy import func, select

from app.db.analytics.base_analytics_repository import BaseAnalyticsRepository
from app.models import Quiz, QuizAttempt, QuizUserAnswer


class UserAnalyticsRepository(BaseAnalyticsRepository):
    """
    Analytics queries related to a single user.
    """

    async def get_user_overall_rating(
        self,
        user_id: int,
    ) -> tuple[int, int]:
        """
        Return (correct_answers, total_answers) for a user.
        """
        stmt = (
            select(
                func.count()
                .filter(QuizUserAnswer.is_correct.is_(True))
                .label("correct"),
                func.count().label("total"),
            )
            .join(
                QuizAttempt,
                QuizAttempt.id == QuizUserAnswer.attempt_id,
            )
            .where(QuizAttempt.user_id == user_id)
        )

        result = await self.session.execute(stmt)
        row = result.one()

        return row.correct or 0, row.total or 0

    async def get_user_quiz_averages_paginated(
        self,
        user_id: int,
        from_date: date,
        to_date: date,
        skip: int,
        limit: int,
    ) -> tuple[list[Any], int]:
        """
        Paginated average score per quiz for a user.
        """
        base_query = (
            select(
                Quiz.id.label("quiz_id"),
                Quiz.title.label("quiz_title"),
                self.avg_correct_case(QuizUserAnswer.is_correct).label("average_score"),
            )
            .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
            .join(
                QuizUserAnswer,
                QuizUserAnswer.attempt_id == QuizAttempt.id,
            )
            .where(
                QuizAttempt.user_id == user_id,
                QuizUserAnswer.answered_at.between(from_date, to_date),
            )
            .group_by(Quiz.id, Quiz.title)
            .order_by(Quiz.title)
        )

        total = await self.count_from_subquery(base_query)

        stmt = base_query.offset(skip).limit(limit)
        items = (await self.session.execute(stmt)).all()

        return items, total

    async def get_user_last_quiz_completions_paginated(
        self,
        user_id: int,
        skip: int,
        limit: int,
    ) -> tuple[list[Any], int]:
        """
        Paginated last completion timestamp per quiz for a user.
        """
        base_query = (
            select(
                Quiz.id.label("quiz_id"),
                Quiz.title.label("quiz_title"),
                func.max(QuizAttempt.completed_at).label("last_completed_at"),
            )
            .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
            .where(QuizAttempt.user_id == user_id)
            .group_by(Quiz.id, Quiz.title)
            .order_by(func.max(QuizAttempt.completed_at).desc())
        )

        total = await self.count_from_subquery(base_query)

        stmt = base_query.offset(skip).limit(limit)
        items = (await self.session.execute(stmt)).all()

        return items, total
