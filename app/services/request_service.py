"""Request service layer for business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ServiceException,
)
from app.core.logger import logger
from app.db.company_member_repository import company_member_repository
from app.db.company_repository import company_repository
from app.db.request_repository import request_repository
from app.enums.role import Role
from app.enums.status import Status
from app.models.company_member import CompanyMember
from app.models.request import Request
from app.services.permission_service import permission_service


class RequestService:
    """Service layer for membership request operations."""

    async def create_request(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> Request:
        """
        User creates request to join company.
        """
        try:
            company = await company_repository.get_one(db, company_id)
            if not company:
                raise NotFoundException(f"Company with id={company_id} not found")

            existing_member = await company_member_repository.get_member(
                db, company_id, user_id
            )
            if existing_member:
                raise BadRequestException("You are already a member of this company")

            existing_request = await request_repository.get_pending_by_company_and_user(
                db, company_id, user_id
            )
            if existing_request:
                raise ConflictException(
                    f"You already have a pending request to company {company_id}"
                )

            request = Request(
                company_id=company_id, user_id=user_id, status=Status.PENDING
            )
            created_request = await request_repository.create_one(db, request)

            logger.info(
                f"Request created: User {user_id} → Company {company_id} (ID: {created_request.id})"
            )
            return created_request

        except (NotFoundException, BadRequestException, ConflictException):
            raise
        except Exception as e:
            logger.error(f"Error creating request: {str(e)}")
            raise ServiceException("Failed to create request")

    async def cancel_request(
        self, db: AsyncSession, request_id: int, user_id: int
    ) -> None:
        """
        User cancels own pending request.
        """
        try:
            request = await request_repository.get_one(db, request_id)
            if not request:
                raise NotFoundException(f"Request with id={request_id} not found")

            if request.user_id != user_id:
                raise PermissionDeniedException("You can only cancel your own requests")

            if request.status != Status.PENDING:
                raise BadRequestException(
                    f"Cannot cancel request with status: {request.status.value}"
                )

            await request_repository.delete_one(db, request)
            logger.info(f"Request cancelled: ID {request_id}, User {user_id}")

        except (PermissionDeniedException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error canceling request {request_id}: {str(e)}")
            raise ServiceException("Failed to cancel request")

    async def get_user_requests(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int,
        limit: int,
        status: Status | None = None,
    ) -> tuple[list[Request], int]:
        """
        User views sent requests.
        """
        try:
            return await request_repository.get_by_user(
                db, user_id, skip, limit, status
            )

        except Exception as e:
            logger.error(f"Error fetching requests for user {user_id}: {str(e)}")
            raise ServiceException("Failed to retrieve requests")

    async def get_company_requests(
        self,
        db: AsyncSession,
        company_id: int,
        owner_id: int,
        skip: int,
        limit: int,
        status: Status | None = None,
    ) -> tuple[list[Request], int]:
        """
        Owner views pending requests to company.
        """
        try:
            await permission_service.require_owner(db, company_id, owner_id)

            return await request_repository.get_by_company(
                db, company_id, skip, limit, status
            )

        except PermissionDeniedException:
            raise
        except Exception as e:
            logger.error(f"Error fetching requests for company {company_id}: {str(e)}")
            raise ServiceException("Failed to retrieve requests")

    async def accept_request(
        self, db: AsyncSession, request_id: int, company_id: int, owner_id: int
    ) -> Request:
        """
        Owner accepts membership request.
        """
        try:
            request = await request_repository.get_one(db, request_id)
            if not request:
                raise NotFoundException(f"Request with id={request_id} not found")

            if request.company_id != company_id:
                raise BadRequestException(
                    f"Request {request_id} is not for company {company_id}"
                )

            await permission_service.require_owner(db, company_id, owner_id)

            if request.status != Status.PENDING:
                raise BadRequestException(
                    f"Cannot accept request with status: {request.status.value}"
                )

            existing_member = await company_member_repository.get_member(
                db, company_id, request.user_id
            )
            if existing_member:
                raise BadRequestException("User is already a member of this company")

            request.status = Status.ACCEPTED
            updated_request = await request_repository.update_one(db, request)

            member = CompanyMember(
                company_id=company_id, user_id=request.user_id, role=Role.MEMBER
            )
            await company_member_repository.create_one(db, member)

            logger.info(
                f"Request accepted: ID {request_id}, User {request.user_id} joined company {company_id}"
            )
            return updated_request

        except (PermissionDeniedException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error accepting request {request_id}: {str(e)}")
            raise ServiceException("Failed to accept request")

    async def decline_request(
        self, db: AsyncSession, request_id: int, company_id: int, owner_id: int
    ) -> Request:
        """
        Owner declines membership request.

        Changes status to DECLINED.
        """
        try:
            request = await request_repository.get_one(db, request_id)
            if not request:
                raise NotFoundException(f"Request with id={request_id} not found")

            if request.company_id != company_id:
                raise BadRequestException(
                    f"Request {request_id} is not for company {company_id}"
                )

            await permission_service.require_owner(db, company_id, owner_id)

            if request.status != Status.PENDING:
                raise BadRequestException(
                    f"Cannot decline request with status: {request.status.value}"
                )

            request.status = Status.DECLINED
            updated_request = await request_repository.update_one(db, request)

            logger.info(
                f"Request declined: ID {request_id}, User {request.user_id}, Company {company_id}"
            )
            return updated_request

        except (PermissionDeniedException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error declining request {request_id}: {str(e)}")
            raise ServiceException("Failed to decline request")


# Create instance
request_service = RequestService()
