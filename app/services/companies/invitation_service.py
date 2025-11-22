from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ServiceException,
)
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.enums.status import Status
from app.models.invitation import Invitation
from app.schemas.invitation import InvitationResponse, InvitationsListResponse
from app.schemas.pagination import PaginationBaseSchema
from app.services.companies.base_membership_service import BaseMembershipService
from app.services.companies.permission_service import PermissionService
from app.utils.pagination import paginate_query


class InvitationService(BaseMembershipService):
    """Service layer for invitation operations."""

    def __init__(self, uow: AbstractUnitOfWork, permission_service: PermissionService):
        super().__init__(uow, permission_service)

    def _get_repository(self):
        return self._uow.invitations

    def _get_entity_name(self) -> str:
        return "Invitation"

    async def send_invitation(
        self, company_id: int, user_email: str, owner_id: int
    ) -> Invitation:
        """
        Owner sends invitation to user by email.
        """
        await self._permission_service.require_owner(company_id, owner_id)

        async with self._uow:
            try:
                company = await self._uow.companies.get_one_by_id(company_id)
                if not company:
                    raise NotFoundException(f"Company with ID {company_id} not found")

                user = await self._uow.users.get_by_email(user_email)
                if not user:
                    raise NotFoundException(f"User with email {user_email} not found")

                existing_member = await self._uow.company_member.get_member_by_ids(
                    company_id, user.id
                )
                if existing_member:
                    raise BadRequestException(
                        "User is already a member of this company"
                    )

                existing_invitation = (
                    await self._uow.invitations.get_pending_by_company_and_user(
                        company_id, user.id
                    )
                )
                if existing_invitation:
                    raise ConflictException(
                        "Pending invitation already exists for this user"
                    )

                invitation = Invitation(
                    company_id=company_id,
                    user_id=user.id,
                    status=Status.PENDING,
                )
                created_invitation = await self._uow.invitations.create_one(invitation)

                await self._uow.commit()

                logger.info(
                    f"Invitation sent: Company {company_id} → "
                    f"User {user.id} (ID: {created_invitation.id})"
                )
                return created_invitation

            except (
                NotFoundException,
                BadRequestException,
                ConflictException,
            ):
                raise
            except Exception as e:
                logger.error(f"Error sending invitation: {str(e)}")
                raise ServiceException("Failed to send invitation")

    async def cancel_invitation(self, invitation_id: int, owner_id: int) -> Invitation:
        """
        Owner cancels pending invitation (changes status to CANCELED).
        """
        async with self._uow:
            try:
                invitation = await self._uow.invitations.get_one_by_id(invitation_id)
                if not invitation:
                    raise NotFoundException(
                        f"Invitation with ID {invitation_id} not found"
                    )

                await self._permission_service.require_owner(
                    invitation.company_id, owner_id
                )

                await self._validate_status_for_action(invitation, "cancel")

                invitation.status = Status.CANCELED
                updated_invitation = await self._uow.invitations.update_one(invitation)

                await self._uow.commit()

                logger.info(f"Invitation cancelled: ID {invitation_id}")
                return updated_invitation

            except (NotFoundException, BadRequestException, PermissionDeniedException):
                raise
            except Exception as e:
                logger.error(f"Error canceling invitation {invitation_id}: {str(e)}")
                raise ServiceException("Failed to cancel invitation")

    async def accept_invitation(self, invitation_id: int, user_id: int) -> Invitation:
        """
        User accepts invitation.
        """
        async with self._uow:
            try:
                invitation = await self._uow.invitations.get_one_by_id(invitation_id)
                if not invitation:
                    raise NotFoundException(
                        f"Invitation with ID {invitation_id} not found"
                    )

                if invitation.user_id != user_id:
                    raise PermissionDeniedException(
                        "You can only accept invitations sent to you"
                    )

                await self._validate_status_for_action(invitation, "accept")
                await self._check_existing_member(invitation.company_id, user_id)

                invitation.status = Status.ACCEPTED
                updated_invitation = await self._uow.invitations.update_one(invitation)

                await self._create_member(invitation.company_id, user_id)

                await self._uow.commit()

                logger.info(
                    f"Invitation accepted: ID {invitation_id}, "
                    f"User {user_id} joined company {invitation.company_id}"
                )
                return updated_invitation

            except (PermissionDeniedException, NotFoundException, BadRequestException):
                raise
            except Exception as e:
                logger.error(f"Error accepting invitation {invitation_id}: {str(e)}")
                raise ServiceException("Failed to accept invitation")

    async def decline_invitation(self, invitation_id: int, user_id: int) -> Invitation:
        """
        User declines invitation. Changes status to DECLINED.
        """
        async with self._uow:
            try:
                invitation = await self._uow.invitations.get_one_by_id(invitation_id)
                if not invitation:
                    raise NotFoundException(
                        f"Invitation with ID {invitation_id} not found"
                    )

                if invitation.user_id != user_id:
                    raise PermissionDeniedException(
                        "You can only decline invitations sent to you"
                    )

                await self._validate_status_for_action(invitation, "decline")

                invitation.status = Status.DECLINED
                updated_invitation = await self._uow.invitations.update_one(invitation)

                await self._uow.commit()

                logger.info(f"Invitation declined: ID {invitation_id}, User {user_id}")
                return updated_invitation

            except (PermissionDeniedException, NotFoundException, BadRequestException):
                raise
            except Exception as e:
                logger.error(f"Error declining invitation {invitation_id}: {str(e)}")
                raise ServiceException("Failed to decline invitation")

    async def get_company_invitations_paginated(
        self,
        company_id: int,
        owner_id: int,
        pagination: PaginationBaseSchema,
        status: Status | None = None,
    ) -> InvitationsListResponse:
        """
        Owner views invitations sent by company (paginated).
        """
        await self._permission_service.require_owner(company_id, owner_id)

        async with self._uow:

            async def db_fetch(skip: int, limit: int):
                return await self._uow.invitations.get_by_company(
                    company_id,
                    skip=skip,
                    limit=limit,
                    status=status,
                )

            return await paginate_query(
                db_fetch_func=db_fetch,
                pagination=pagination,
                response_schema=InvitationsListResponse,
                item_schema=InvitationResponse,
            )

    async def get_user_invitations_paginated(
        self,
        user_id: int,
        pagination: PaginationBaseSchema,
        status: Status | None = None,
    ) -> InvitationsListResponse:
        """
        User views invitations they received (paginated).
        """
        async with self._uow:

            async def db_fetch(skip: int, limit: int):
                return await self._uow.invitations.get_by_user(
                    user_id, skip=skip, limit=limit, status=status
                )

            return await paginate_query(
                db_fetch_func=db_fetch,
                pagination=pagination,
                response_schema=InvitationsListResponse,
                item_schema=InvitationResponse,
            )
