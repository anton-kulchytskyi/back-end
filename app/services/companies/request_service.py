from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ServiceException,
)
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.enums import Status
from app.models import Request
from app.schemas import PaginationBaseSchema, RequestResponse, RequestsListResponse
from app.services.companies.base_membership_service import BaseMembershipService
from app.services.companies.permission_service import PermissionService
from app.utils.pagination import paginate_query


class RequestService(BaseMembershipService):
    """Service layer for membership request operations."""

    def __init__(self, uow: AbstractUnitOfWork, permission_service: PermissionService):
        super().__init__(uow, permission_service)

    # --- Base class hooks --- #

    def _get_repository(self):
        return self._uow.requests

    def _get_entity_name(self) -> str:
        return "Request"

    # --- Public API --- #

    async def create_request(self, company_id: int, user_id: int) -> Request:
        """
        User creates request to join company.
        """
        async with self._uow:
            try:
                company = await self._uow.companies.get_one_by_id(company_id)
                if not company:
                    raise NotFoundException(f"Company with id={company_id} not found")

                existing_member = await self._uow.company_member.get_member_by_ids(
                    company_id, user_id
                )
                if existing_member:
                    raise BadRequestException(
                        "You are already a member of this company"
                    )

                existing_request = (
                    await self._uow.requests.get_pending_by_company_and_user(
                        company_id, user_id
                    )
                )
                if existing_request:
                    raise ConflictException(
                        f"You already have a pending request to company {company_id}"
                    )

                request = Request(
                    company_id=company_id,
                    user_id=user_id,
                    status=Status.PENDING,
                )
                created_request = await self._uow.requests.create_one(request)

                await self._uow.commit()

                logger.info(
                    f"Request created: User {user_id} → Company {company_id} "
                    f"(ID: {created_request.id})"
                )
                return created_request

            except (NotFoundException, BadRequestException, ConflictException):
                raise
            except Exception as e:
                logger.error(f"Error creating request: {str(e)}")
                raise ServiceException("Failed to create request")

    async def cancel_request(self, request_id: int, user_id: int) -> Request:
        """
        User cancels own pending request (changes status to CANCELED).
        """
        async with self._uow:
            try:
                request = await self._uow.requests.get_one_by_id(request_id)
                if not request:
                    raise NotFoundException(f"Request with id={request_id} not found")

                if request.user_id != user_id:
                    raise PermissionDeniedException(
                        "You can only cancel your own requests"
                    )

                await self._validate_status_for_action(request, "cancel")

                request.status = Status.CANCELED
                updated_request = await self._uow.requests.update_one(request)

                await self._uow.commit()

                logger.info(f"Request cancelled: ID {request_id}, User {user_id}")
                return updated_request

            except (PermissionDeniedException, NotFoundException, BadRequestException):
                raise
            except Exception as e:
                logger.error(f"Error canceling request {request_id}: {str(e)}")
                raise ServiceException("Failed to cancel request")

    async def accept_request(
        self, request_id: int, company_id: int, owner_id: int
    ) -> Request:
        """
        Owner accepts membership request.
        """
        await self._permission_service.require_owner(company_id, owner_id)

        async with self._uow:
            try:
                request = await self._uow.requests.get_one_by_id(request_id)
                if not request:
                    raise NotFoundException(f"Request with id={request_id} not found")

                if request.company_id != company_id:
                    raise BadRequestException(
                        f"Request {request_id} is not for company {company_id}"
                    )

                await self._validate_status_for_action(request, "accept")
                await self._check_existing_member(company_id, request.user_id)

                request.status = Status.ACCEPTED
                updated_request = await self._uow.requests.update_one(request)

                await self._create_member(company_id, request.user_id)

                await self._uow.commit()

                logger.info(
                    f"Request accepted: ID {request_id}, "
                    f"User {request.user_id} joined company {company_id}"
                )
                return updated_request

            except (PermissionDeniedException, NotFoundException, BadRequestException):
                raise
            except Exception as e:
                logger.error(f"Error accepting request {request_id}: {str(e)}")
                raise ServiceException("Failed to accept request")

    async def decline_request(
        self, request_id: int, company_id: int, owner_id: int
    ) -> Request:
        """
        Owner declines membership request. Changes status to DECLINED.
        """
        await self._permission_service.require_owner(company_id, owner_id)

        async with self._uow:
            try:
                request = await self._uow.requests.get_one_by_id(request_id)
                if not request:
                    raise NotFoundException(f"Request with id={request_id} not found")

                if request.company_id != company_id:
                    raise BadRequestException(
                        f"Request {request_id} is not for company {company_id}"
                    )

                await self._validate_status_for_action(request, "decline")

                request.status = Status.DECLINED
                updated_request = await self._uow.requests.update_one(request)

                await self._uow.commit()

                logger.info(
                    f"Request declined: ID {request_id}, "
                    f"User {request.user_id}, Company {company_id}"
                )
                return updated_request

            except (PermissionDeniedException, NotFoundException, BadRequestException):
                raise
            except Exception as e:
                logger.error(f"Error declining request {request_id}: {str(e)}")
                raise ServiceException("Failed to decline request")

    async def get_user_requests_paginated(
        self,
        user_id: int,
        pagination: PaginationBaseSchema,
        status: Status | None = None,
    ) -> RequestsListResponse:
        """User views the requests they created."""
        async with self._uow:

            async def db_fetch(skip: int, limit: int):
                return await self._uow.requests.get_by_user(
                    user_id, skip=skip, limit=limit, status=status
                )

            return await paginate_query(
                db_fetch_func=db_fetch,
                pagination=pagination,
                response_schema=RequestsListResponse,
                item_schema=RequestResponse,
            )

    async def get_company_requests_paginated(
        self,
        company_id: int,
        owner_id: int,
        pagination: PaginationBaseSchema,
        status: Status | None = None,
    ) -> RequestsListResponse:
        """Owner views membership requests to their company."""
        await self._permission_service.require_owner(company_id, owner_id)

        async with self._uow:

            async def db_fetch(skip: int, limit: int):
                return await self._uow.requests.get_by_company(
                    company_id, skip=skip, limit=limit, status=status
                )

            return await paginate_query(
                db_fetch_func=db_fetch,
                pagination=pagination,
                response_schema=RequestsListResponse,
                item_schema=RequestResponse,
            )
