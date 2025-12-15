from typing import Any

from sqlalchemy import func, select

from app.db.analytics.base_analytics_repository import BaseAnalyticsRepository
from app.models import Quiz, QuizAttempt, QuizUserAnswer, User


class CompanyAnalyticsRepository(BaseAnalyticsRepository):
    """
    Analytics queries related to company quizzes.
    """

    async def get_company_users_weekly_averages_paginated(
        self,
        company_id: int,
        skip: int,
        limit: int,
    ) -> tuple[list[Any], int]:
        """
        Paginated weekly average scores for all users in a company.
        """
        week = self.week_trunc(QuizAttempt.completed_at)

        base_query = (
            select(
                QuizAttempt.user_id,
                week.label("week_start"),
                self.avg_correct_case(QuizUserAnswer.is_correct).label("average_score"),
            )
            .join(
                QuizUserAnswer,
                QuizUserAnswer.attempt_id == QuizAttempt.id,
            )
            .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
            .where(Quiz.company_id == company_id)
            .group_by(QuizAttempt.user_id, week)
            .order_by(week.desc())
        )

        total = await self.count_from_subquery(base_query)

        stmt = base_query.offset(skip).limit(limit)
        items = (await self.session.execute(stmt)).all()

        return items, total

    async def get_company_user_quiz_weekly_averages_paginated(
        self,
        company_id: int,
        target_user_id: int,
        skip: int,
        limit: int,
    ) -> tuple[list[Any], int]:
        """
        Paginated weekly average scores per quiz for a selected user.
        """
        week = self.week_trunc(QuizAttempt.completed_at)

        base_query = (
            select(
                Quiz.id.label("quiz_id"),
                Quiz.title.label("quiz_title"),
                week.label("week_start"),
                self.avg_correct_case(QuizUserAnswer.is_correct).label("average_score"),
            )
            .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
            .join(
                QuizUserAnswer,
                QuizUserAnswer.attempt_id == QuizAttempt.id,
            )
            .where(
                Quiz.company_id == company_id,
                QuizAttempt.user_id == target_user_id,
            )
            .group_by(Quiz.id, Quiz.title, week)
            .order_by(week.desc())
        )

        total = await self.count_from_subquery(base_query)

        stmt = base_query.offset(skip).limit(limit)
        items = (await self.session.execute(stmt)).all()

        return items, total

    async def get_company_users_last_attempts_paginated(
        self,
        company_id: int,
        skip: int,
        limit: int,
    ) -> tuple[list[Any], int]:
        """
        Paginated last quiz attempt timestamps for users
        who passed quizzes of a company.
        """
        base_query = (
            select(
                QuizAttempt.user_id,
                User.email.label("user_email"),
                func.max(QuizAttempt.completed_at).label("last_attempt_at"),
            )
            .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
            .join(User, User.id == QuizAttempt.user_id)
            .where(Quiz.company_id == company_id)
            .group_by(QuizAttempt.user_id, User.email)
            .order_by(func.max(QuizAttempt.completed_at).desc())
        )

        total = await self.count_from_subquery(base_query)

        stmt = base_query.offset(skip).limit(limit)
        items = (await self.session.execute(stmt)).all()

        return items, total
