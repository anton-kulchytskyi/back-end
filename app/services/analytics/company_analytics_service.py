from datetime import date

from app.core.exceptions import BadRequestException, ServiceException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.schemas.analytics.company_analytics import (
    AverageScoreResponse,
    CompanyUserLastAttemptResponse,
    CompanyUserQuizAveragesListResponse,
    CompanyUsersAveragesListResponse,
    CompanyUsersLastAttemptsListResponse,
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

    async def get_users_averages_paginated(
        self,
        company_id: int,
        current_user_id: int,
        from_date: date,
        to_date: date,
        pagination: PaginationBaseSchema,
    ) -> CompanyUsersAveragesListResponse:
        """
        Get paginated average scores for all users in a company within date range.
        """
        if from_date > to_date:
            raise BadRequestException("from_date must be before or equal to to_date")

        await self._admin_service.verify_admin_access(
            company_id=company_id,
            user_id=current_user_id,
        )

        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.company_analytic.get_company_users_averages_paginated(
                        company_id=company_id,
                        from_date=from_date,
                        to_date=to_date,
                        skip=skip,
                        limit=limit,
                    )

                return await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=CompanyUsersAveragesListResponse,
                    item_schema=AverageScoreResponse,
                )

            except Exception as e:
                logger.error(
                    f"Error getting users averages for company {company_id}: {e}"
                )
                raise ServiceException("Failed to retrieve company users averages")

    async def get_user_quiz_averages_paginated(
        self,
        company_id: int,
        target_user_id: int,
        current_user_id: int,
        from_date: date,
        to_date: date,
        pagination: PaginationBaseSchema,
    ) -> CompanyUserQuizAveragesListResponse:
        """
        Get paginated average scores per quiz for a selected user
        in a company within date range.
        """
        if from_date > to_date:
            raise BadRequestException("from_date must be before or equal to to_date")

        await self._admin_service.verify_admin_access(
            company_id=company_id,
            user_id=current_user_id,
        )

        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.company_analytic.get_company_user_quiz_averages_paginated(
                        company_id=company_id,
                        target_user_id=target_user_id,
                        from_date=from_date,
                        to_date=to_date,
                        skip=skip,
                        limit=limit,
                    )

                return await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=CompanyUserQuizAveragesListResponse,
                    item_schema=AverageScoreResponse,
                )

            except Exception as e:
                logger.error(
                    f"Error getting quiz averages for user {target_user_id} "
                    f"in company {company_id}: {e}"
                )
                raise ServiceException("Failed to retrieve user quiz averages")

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
