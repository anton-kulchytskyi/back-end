from abc import ABC, abstractmethod

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    PermissionDeniedException,
    ServiceException,
)
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.enums.role import Role
from app.enums.status import Status
from app.models.company_member import CompanyMember
from app.services.permission_service import PermissionService


class BaseMembershipService(ABC):
    """
    Shared logic for invitations/requests:
    - status validation
    - checking membership
    - creating membership
    - generic accept / decline
    """

    def __init__(self, uow: AbstractUnitOfWork, permission_service: PermissionService):
        self._uow = uow
        self._permission_service = permission_service

    # --- Abstract API ---

    @abstractmethod
    def _get_repository(self):
        pass

    @abstractmethod
    def _get_entity_name(self) -> str:
        pass

    # --- Helpers ---

    async def _validate_status_for_action(
        self, entity, action: str, allowed_status: Status = Status.PENDING
    ):
        if entity.status != allowed_status:
            raise BadRequestException(
                f"Cannot {action} {self._get_entity_name().lower()} "
                f"with status: {entity.status.value}"
            )

    async def _check_existing_member(self, company_id: int, user_id: int):
        existing_member = await self._uow.company_member.get_member_by_ids(
            company_id, user_id
        )
        if existing_member:
            raise BadRequestException("User is already a member of this company")

    async def _create_member(self, company_id: int, user_id: int) -> CompanyMember:
        member = CompanyMember(company_id=company_id, user_id=user_id, role=Role.MEMBER)
        return await self._uow.company_member.create_one(member)

    # --- Generic status change (cancel/decline) ---

    async def _change_status(
        self, entity_id: int, new_status: Status, action_verb: str
    ):
        async with self._uow:
            try:
                repo = self._get_repository()
                entity = await repo.get_one_by_id(entity_id)

                if not entity:
                    raise NotFoundException(
                        f"{self._get_entity_name()} with ID {entity_id} not found"
                    )

                await self._validate_status_for_action(entity, action_verb)

                entity.status = new_status
                updated_entity = await repo.update_one(entity)
                await self._uow.commit()

                logger.info(
                    f"{self._get_entity_name()} {action_verb}: "
                    f"ID {entity_id}, Company {entity.company_id}, User {entity.user_id}"
                )

                return updated_entity

            except (NotFoundException, BadRequestException, PermissionDeniedException):
                raise
            except Exception as e:
                logger.error(
                    f"Error {action_verb} {self._get_entity_name().lower()} {entity_id}: {str(e)}"
                )
                raise ServiceException(
                    f"Failed to {action_verb} {self._get_entity_name().lower()}"
                )

    # --- Accept + create member ---

    async def _accept_with_member_creation(
        self, entity_id: int, company_id: int, user_id: int
    ):
        async with self._uow:
            try:
                repo = self._get_repository()
                entity = await repo.get_one_by_id(entity_id)

                if not entity:
                    raise NotFoundException(
                        f"{self._get_entity_name()} with ID {entity_id} not found"
                    )

                if entity.company_id != company_id:
                    raise BadRequestException(
                        f"{self._get_entity_name()} {entity_id} "
                        f"is not for company {company_id}"
                    )

                await self._validate_status_for_action(entity, "accept")
                await self._check_existing_member(company_id, user_id)

                entity.status = Status.ACCEPTED
                updated_entity = await repo.update_one(entity)

                await self._create_member(company_id, user_id)
                await self._uow.commit()

                logger.info(
                    f"{self._get_entity_name()} accepted: "
                    f"ID {entity_id}, User {user_id}, Company {company_id}"
                )

                return updated_entity

            except (PermissionDeniedException, NotFoundException, BadRequestException):
                raise
            except Exception as e:
                logger.error(
                    f"Error accepting {self._get_entity_name().lower()} {entity_id}: {str(e)}"
                )
                raise ServiceException(
                    f"Failed to accept {self._get_entity_name().lower()}"
                )
