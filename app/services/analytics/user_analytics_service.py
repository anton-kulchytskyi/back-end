from datetime import date

from app.core.exceptions import BadRequestException, ServiceException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.schemas.analytics.user_analytics import (
    UserOverallRatingResponse,
    UserQuizAverageResponse,
    UserQuizAveragesListResponse,
    UserQuizLastCompletionListResponse,
    UserQuizLastCompletionResponse,
)
from app.schemas.pagination.pagination import PaginationBaseSchema
from app.utils.pagination import paginate_query


class UserAnalyticsService:
    """
    Service for user-specific analytics.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self._uow = uow

    async def get_overall_rating(
        self,
        user_id: int,
    ) -> UserOverallRatingResponse:
        """
        Get overall average score for a user across all quizzes.
        """
        async with self._uow:
            try:
                correct, total = await self._uow.user_analytic.get_user_overall_rating(
                    user_id=user_id
                )
            except Exception as e:
                logger.error(f"Error getting overall rating for user {user_id}: {e}")
                raise ServiceException("Failed to retrieve user overall rating")

        average = correct / total if total > 0 else 0.0

        return UserOverallRatingResponse(
            average_score=round(average, 4),
            total_answers=total,
            correct_answers=correct,
        )

    async def get_quiz_averages_paginated(
        self,
        user_id: int,
        from_date: date,
        to_date: date,
        pagination: PaginationBaseSchema,
    ) -> UserQuizAveragesListResponse:
        """
        Get paginated average scores per quiz for a user.
        """
        if from_date > to_date:
            raise BadRequestException("from_date must be before or equal to to_date")
        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return (
                        await self._uow.user_analytic.get_user_quiz_averages_paginated(
                            user_id=user_id,
                            from_date=from_date,
                            to_date=to_date,
                            skip=skip,
                            limit=limit,
                        )
                    )

                return await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=UserQuizAveragesListResponse,
                    item_schema=UserQuizAverageResponse,
                )

            except Exception as e:
                logger.error(f"Error getting quiz averages for user {user_id}: {e}")
                raise ServiceException("Failed to retrieve user quiz averages")

    async def get_last_quiz_completions_paginated(
        self,
        user_id: int,
        pagination: PaginationBaseSchema,
    ) -> UserQuizLastCompletionListResponse:
        """
        Get paginated list of last quiz completion timestamps for a user.
        """
        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.user_analytic.get_user_last_quiz_completions_paginated(
                        user_id=user_id,
                        skip=skip,
                        limit=limit,
                    )

                return await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=UserQuizLastCompletionListResponse,
                    item_schema=UserQuizLastCompletionResponse,
                )

            except Exception as e:
                logger.error(
                    f"Error getting last quiz completions for user {user_id}: {e}"
                )
                raise ServiceException("Failed to retrieve user quiz completions")
