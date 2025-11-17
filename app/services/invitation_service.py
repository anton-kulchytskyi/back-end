"""Invitation service layer for business logic."""

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
from app.db.invitation_repository import invitation_repository
from app.db.user_repository import user_repository
from app.enums.role import Role
from app.enums.status import Status
from app.models.company_member import CompanyMember
from app.models.invitation import Invitation
from app.services.permission_service import permission_service


class InvitationService:
    """Service layer for invitation operations."""

    async def send_invitation(
        self, db: AsyncSession, company_id: int, user_email: str, owner_id: int
    ) -> Invitation:
        """
        Owner sends invitation to user.
        """
        try:
            await permission_service.require_owner(db, company_id, owner_id)

            company = await company_repository.get_one(db, company_id)
            if not company:
                raise NotFoundException(f"Company with ID {company_id} not found")

            user = await user_repository.get_by_email(db, user_email)
            if not user:
                raise NotFoundException(f"User with email {user_email} not found")

            existing_member = await company_member_repository.get_member(
                db, company_id, user.id
            )
            if existing_member:
                raise BadRequestException("User is already a member of this company")

            existing_invitation = (
                await invitation_repository.get_pending_by_company_and_user(
                    db, company_id, user.id
                )
            )
            if existing_invitation:
                raise ConflictException("Invitation already sent to this user")

            invitation = Invitation(
                company_id=company_id, user_id=user.id, status=Status.PENDING
            )
            created_invitation = await invitation_repository.create_one(db, invitation)

            logger.info(
                f"Invitation sent: Company {company_id} → User {user.id} (ID: {created_invitation.id})"
            )
            return created_invitation

        except (
            PermissionDeniedException,
            NotFoundException,
            BadRequestException,
            ConflictException,
        ):
            raise
        except Exception as e:
            logger.error(f"Error sending invitation: {str(e)}")
            raise ServiceException("Failed to send invitation")

    async def cancel_invitation(
        self, db: AsyncSession, invitation_id: int, owner_id: int
    ) -> None:
        """
        Owner cancels pending invitation.
        """
        try:
            invitation = await invitation_repository.get_one(db, invitation_id)
            if not invitation:
                raise NotFoundException(f"Invitation with ID {invitation_id} not found")

            await permission_service.require_owner(db, invitation.company_id, owner_id)

            if invitation.status != Status.PENDING:
                raise BadRequestException(
                    f"Cannot cancel invitation with status: {invitation.status.value}"
                )

            await invitation_repository.delete_one(db, invitation)
            logger.info(f"Invitation cancelled: ID {invitation_id}")

        except (PermissionDeniedException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error canceling invitation {invitation_id}: {str(e)}")
            raise ServiceException("Failed to cancel invitation")

    async def get_company_invitations(
        self,
        db: AsyncSession,
        company_id: int,
        owner_id: int,
        skip: int,
        limit: int,
        status: Status | None = None,
    ) -> tuple[list[Invitation], int]:
        """
        Owner views sent invitations.
        """
        try:
            await permission_service.require_owner(db, company_id, owner_id)

            return await invitation_repository.get_by_company(
                db, company_id, skip, limit, status
            )

        except PermissionDeniedException:
            raise
        except Exception as e:
            logger.error(
                f"Error fetching invitations for company {company_id}: {str(e)}"
            )
            raise ServiceException("Failed to retrieve invitations")

    async def get_user_invitations(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int,
        limit: int,
        status: Status | None = None,
    ) -> tuple[list[Invitation], int]:
        """
        User views received invitations.
        """
        try:
            return await invitation_repository.get_by_user(
                db, user_id, skip, limit, status
            )

        except Exception as e:
            logger.error(f"Error fetching invitations for user {user_id}: {str(e)}")
            raise ServiceException("Failed to retrieve invitations")

    async def accept_invitation(
        self, db: AsyncSession, invitation_id: int, user_id: int
    ) -> Invitation:
        """
        User accepts invitation.
        """
        try:
            # Get invitation
            invitation = await invitation_repository.get_one(db, invitation_id)
            if not invitation:
                raise NotFoundException(f"Invitation with ID {invitation_id} not found")

            # Permission check: only invited user can accept
            if invitation.user_id != user_id:
                raise PermissionDeniedException(
                    "You can only accept invitations sent to you"
                )

            # Check status
            if invitation.status != Status.PENDING:
                raise BadRequestException(
                    f"Cannot accept invitation with status: {invitation.status.value}"
                )

            # Check if user is already a member (shouldn't happen, but just in case)
            existing_member = await company_member_repository.get_member(
                db, invitation.company_id, user_id
            )
            if existing_member:
                raise BadRequestException("You are already a member of this company")

            # Update invitation status
            invitation.status = Status.ACCEPTED
            updated_invitation = await invitation_repository.update_one(db, invitation)

            # Create CompanyMember
            member = CompanyMember(
                company_id=invitation.company_id, user_id=user_id, role=Role.MEMBER
            )
            await company_member_repository.create_one(db, member)

            logger.info(
                f"Invitation accepted: ID {invitation_id}, User {user_id} joined company {invitation.company_id}"
            )
            return updated_invitation

        except (PermissionDeniedException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error accepting invitation {invitation_id}: {str(e)}")
            raise ServiceException("Failed to accept invitation")

    async def decline_invitation(
        self, db: AsyncSession, invitation_id: int, user_id: int
    ) -> Invitation:
        """
        User declines invitation.

        Changes status to DECLINED.
        """
        try:
            # Get invitation
            invitation = await invitation_repository.get_one(db, invitation_id)
            if not invitation:
                raise NotFoundException(f"Invitation with ID {invitation_id} not found")

            # Permission check: only invited user can decline
            if invitation.user_id != user_id:
                raise PermissionDeniedException(
                    "You can only decline invitations sent to you"
                )

            # Check status
            if invitation.status != Status.PENDING:
                raise BadRequestException(
                    f"Cannot decline invitation with status: {invitation.status.value}"
                )

            # Update invitation status
            invitation.status = Status.DECLINED
            updated_invitation = await invitation_repository.update_one(db, invitation)

            logger.info(f"Invitation declined: ID {invitation_id}, User {user_id}")
            return updated_invitation

        except (PermissionDeniedException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error declining invitation {invitation_id}: {str(e)}")
            raise ServiceException("Failed to decline invitation")


# Create instance
invitation_service = InvitationService()
