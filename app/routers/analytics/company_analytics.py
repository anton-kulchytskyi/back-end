from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import get_company_analytics_service, get_current_user
from app.models import User
from app.schemas.analytics.company_analytics import (
    CompanyUserQuizWeeklyAveragesListResponse,
    CompanyUsersLastAttemptsListResponse,
    CompanyUsersWeeklyAveragesListResponse,
)
from app.schemas.pagination.pagination import PaginationBaseSchema
from app.services.analytics.company_analytics_service import CompanyAnalyticsService

router = APIRouter()


@router.get(
    "/{company_id}/users/weekly-averages",
    response_model=CompanyUsersWeeklyAveragesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get company users weekly averages",
    description="Get weekly average quiz scores for all users who passed company quizzes.",
)
async def get_company_users_weekly_averages(
    company_id: int = Path(..., ge=1),
    pagination: PaginationBaseSchema = Depends(),
    current_user: User = Depends(get_current_user),
    analytics_service: CompanyAnalyticsService = Depends(get_company_analytics_service),
) -> CompanyUsersWeeklyAveragesListResponse:
    """
    Owner/admin: get weekly averages for all users.
    """
    return await analytics_service.get_users_weekly_averages_paginated(
        company_id=company_id,
        current_user_id=current_user.id,
        pagination=pagination,
    )


@router.get(
    "/{company_id}/users/{user_id}/quizzes/weekly-averages",
    response_model=CompanyUserQuizWeeklyAveragesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user quiz weekly averages in company",
    description="Get weekly average quiz scores for a selected user in a company.",
)
async def get_company_user_quiz_weekly_averages(
    company_id: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1),
    pagination: PaginationBaseSchema = Depends(),
    current_user: User = Depends(get_current_user),
    analytics_service: CompanyAnalyticsService = Depends(get_company_analytics_service),
) -> CompanyUserQuizWeeklyAveragesListResponse:
    """
    Owner/admin: get weekly quiz averages for a user.
    """
    return await analytics_service.get_user_quiz_weekly_averages_paginated(
        company_id=company_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
        pagination=pagination,
    )


@router.get(
    "/{company_id}/users/last-attempts",
    response_model=CompanyUsersLastAttemptsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get company users last quiz attempts",
    description="Get list of users with their last quiz attempt timestamps.",
)
async def get_company_users_last_attempts(
    company_id: int = Path(..., ge=1),
    pagination: PaginationBaseSchema = Depends(),
    current_user: User = Depends(get_current_user),
    analytics_service: CompanyAnalyticsService = Depends(get_company_analytics_service),
) -> CompanyUsersLastAttemptsListResponse:
    """
    Owner/admin: get last quiz attempts for users.
    """
    return await analytics_service.get_users_last_attempts_paginated(
        company_id=company_id,
        current_user_id=current_user.id,
        pagination=pagination,
    )
