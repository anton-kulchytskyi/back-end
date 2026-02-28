from datetime import date

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, get_user_analytics_service
from app.models import User
from app.schemas.analytics.user_analytics import (
    UserOverallRatingResponse,
    UserQuizAveragesListResponse,
    UserQuizLastCompletionListResponse,
)
from app.schemas.pagination.pagination import PaginationBaseSchema
from app.services.analytics.user_analytics_service import UserAnalyticsService

router = APIRouter()


@router.get(
    "/overall",
    response_model=UserOverallRatingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my overall quiz rating",
    description="Return average quiz score across all quizzes and companies.",
)
async def get_my_overall_rating(
    current_user: User = Depends(get_current_user),
    analytics_service: UserAnalyticsService = Depends(get_user_analytics_service),
) -> UserOverallRatingResponse:
    """
    Get overall rating for current user.
    """
    return await analytics_service.get_overall_rating(user_id=current_user.id)


@router.get(
    "/quizzes/averages",
    response_model=UserQuizAveragesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my quiz average scores",
    description="Get paginated list of average quiz scores for a user within a time range.",
)
async def get_my_quiz_averages(
    from_date: date = Query(..., description="Start date (inclusive)"),
    to_date: date = Query(..., description="End date (inclusive)"),
    pagination: PaginationBaseSchema = Depends(),
    current_user: User = Depends(get_current_user),
    analytics_service: UserAnalyticsService = Depends(get_user_analytics_service),
) -> UserQuizAveragesListResponse:
    """
    Get average scores per quiz for current user.
    """
    return await analytics_service.get_quiz_averages_paginated(
        user_id=current_user.id,
        from_date=from_date,
        to_date=to_date,
        pagination=pagination,
    )


@router.get(
    "/quizzes/last-completions",
    response_model=UserQuizLastCompletionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my last quiz completions",
    description="Get paginated list of quizzes with last completion timestamps.",
)
async def get_my_last_quiz_completions(
    pagination: PaginationBaseSchema = Depends(),
    current_user: User = Depends(get_current_user),
    analytics_service: UserAnalyticsService = Depends(get_user_analytics_service),
) -> UserQuizLastCompletionListResponse:
    """
    Get last quiz completion timestamps for current user.
    """
    return await analytics_service.get_last_quiz_completions_paginated(
        user_id=current_user.id,
        pagination=pagination,
    )
