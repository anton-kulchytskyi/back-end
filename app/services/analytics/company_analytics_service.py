from app.core.exceptions import ServiceException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.schemas.analytics.company_analytics import (
    CompanyUserLastAttemptResponse,
    CompanyUserQuizWeeklyAveragesListResponse,
    CompanyUsersLastAttemptsListResponse,
    CompanyUsersWeeklyAveragesListResponse,
    WeeklyAverageResponse,
)
from app.schemas.pagination.pagination import PaginationBaseSchema
from app.services.companies.admin_service import AdminService
from app.utils.pagination import paginate_query


class CompanyAnalyticsService:
    """
    Service for company-level analytics (owners/admins only).
    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        admin_service: AdminService,
    ):
        self._uow = uow
        self._admin_service = admin_service

    async def get_users_weekly_averages_paginated(
        self,
        company_id: int,
        current_user_id: int,
        pagination: PaginationBaseSchema,
    ) -> CompanyUsersWeeklyAveragesListResponse:
        """
        Get paginated weekly average scores for all users of company quizzes.
        """

        await self._admin_service.verify_admin_access(
            company_id=company_id,
            user_id=current_user_id,
        )

        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.company_analytic.get_company_users_weekly_averages_paginated(
                        company_id=company_id,
                        skip=skip,
                        limit=limit,
                    )

                return await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=CompanyUsersWeeklyAveragesListResponse,
                    item_schema=WeeklyAverageResponse,
                )

            except Exception as e:
                logger.error(
                    f"Error getting weekly averages for company {company_id}: {e}"
                )
                raise ServiceException(
                    "Failed to retrieve company users weekly averages"
                )

    async def get_user_quiz_weekly_averages_paginated(
        self,
        company_id: int,
        target_user_id: int,
        current_user_id: int,
        pagination: PaginationBaseSchema,
    ) -> CompanyUserQuizWeeklyAveragesListResponse:
        """
        Get paginated weekly quiz averages for a selected user.
        """

        await self._admin_service.verify_admin_access(
            company_id=company_id,
            user_id=current_user_id,
        )

        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.company_analytic.get_company_user_quiz_weekly_averages_paginated(
                        company_id=company_id,
                        target_user_id=target_user_id,
                        skip=skip,
                        limit=limit,
                    )

                return await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=CompanyUserQuizWeeklyAveragesListResponse,
                    item_schema=WeeklyAverageResponse,
                )

            except Exception as e:
                logger.error(
                    f"Error getting quiz weekly averages for user {target_user_id} "
                    f"in company {company_id}: {e}"
                )
                raise ServiceException("Failed to retrieve user quiz weekly averages")

    async def get_users_last_attempts_paginated(
        self,
        company_id: int,
        current_user_id: int,
        pagination: PaginationBaseSchema,
    ) -> CompanyUsersLastAttemptsListResponse:
        """
        Get paginated list of users and their last quiz attempt timestamps.
        """
        await self._admin_service.verify_admin_access(
            company_id=company_id,
            user_id=current_user_id,
        )

        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.company_analytic.get_company_users_last_attempts_paginated(
                        company_id=company_id,
                        skip=skip,
                        limit=limit,
                    )

                return await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=CompanyUsersLastAttemptsListResponse,
                    item_schema=CompanyUserLastAttemptResponse,
                )

            except Exception as e:
                logger.error(
                    f"Error getting last attempts for company {company_id}: {e}"
                )
                raise ServiceException("Failed to retrieve company users last attempts")
