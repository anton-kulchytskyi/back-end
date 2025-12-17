from datetime import date

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.dependencies import get_company_analytics_service, get_current_user
from app.models import User
from app.schemas.analytics.company_analytics import (
    CompanyUserQuizAveragesListResponse,
    CompanyUsersAveragesListResponse,
    CompanyUsersLastAttemptsListResponse,
)
from app.schemas.pagination.pagination import PaginationBaseSchema
from app.services.analytics.company_analytics_service import CompanyAnalyticsService

router = APIRouter()


@router.get(
    "/{company_id}/users/averages",
    response_model=CompanyUsersAveragesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get company users average scores",
    description="Get average quiz scores for all users in a company within a date range.",
)
async def get_company_users_averages(
    company_id: int = Path(..., ge=1),
    from_date: date = Query(..., description="Start date (inclusive)"),
    to_date: date = Query(..., description="End date (inclusive)"),
    pagination: PaginationBaseSchema = Depends(),
    current_user: User = Depends(get_current_user),
    analytics_service: CompanyAnalyticsService = Depends(get_company_analytics_service),
) -> CompanyUsersAveragesListResponse:
    """
    Owner/admin: get average scores for all users in a company.
    """
    return await analytics_service.get_users_averages_paginated(
        company_id=company_id,
        current_user_id=current_user.id,
        from_date=from_date,
        to_date=to_date,
        pagination=pagination,
    )


@router.get(
    "/{company_id}/users/{user_id}/quizzes/averages",
    response_model=CompanyUserQuizAveragesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user quiz average scores in company",
    description="Get average quiz scores per quiz for a selected user in a company within a date range.",
)
async def get_company_user_quiz_averages(
    company_id: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1),
    from_date: date = Query(..., description="Start date (inclusive)"),
    to_date: date = Query(..., description="End date (inclusive)"),
    pagination: PaginationBaseSchema = Depends(),
    current_user: User = Depends(get_current_user),
    analytics_service: CompanyAnalyticsService = Depends(get_company_analytics_service),
) -> CompanyUserQuizAveragesListResponse:
    """
    Owner/admin: get average quiz scores for a user in a company.
    """
    return await analytics_service.get_user_quiz_averages_paginated(
        company_id=company_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
        from_date=from_date,
        to_date=to_date,
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
