from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.exceptions import NotFoundException, ServiceException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.enums.notification_status import NotificationStatus
from app.models import Notification
from app.schemas import (
    MarkAllAsReadResponse,
    MarkAsReadResponse,
    NotificationResponse,
    NotificationsListResponse,
    NotificationsPaginationRequest,
)
from app.utils.pagination import paginate_query

if TYPE_CHECKING:
    from app.services.notification.websocket_service import WebSocketService


class NotificationService:
    """Service for notification business logic."""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        websocket_service: WebSocketService | None = None,
    ):
        self._uow = uow
        self._websocket_service = websocket_service

    async def create_notification(
        self,
        user_id: int,
        message: str,
    ) -> Notification:
        """
        Create a single notification.

        NOTE:
        - Does NOT commit
        - Must be called inside active UoW
        """
        notification = Notification(
            user_id=user_id,
            message=message,
            status=NotificationStatus.UNREAD,
        )

        return await self._uow.notifications.create_one(notification)

    async def create_notifications_for_company_members(
        self,
        company_id: int,
        quiz_title: str,
        exclude_user_id: int | None = None,
    ) -> list[Notification]:
        """
        Create notifications for all company members about a new quiz.

        Assumes:
        - permissions already checked
        - UoW already opened by caller
        """
        members, _ = await self._uow.company_member.get_many_by_filters(
            self._uow.company_member.model.company_id == company_id
        )

        message = f'New quiz "{quiz_title}" has been created in your company.'
        notifications: list[Notification] = []

        for member in members:
            if exclude_user_id and member.user_id == exclude_user_id:
                continue

            notification = await self.create_notification(
                user_id=member.user_id,
                message=message,
            )
            notifications.append(notification)

        logger.info(
            "Created %s notifications for quiz '%s' in company %s",
            len(notifications),
            quiz_title,
            company_id,
        )

        return notifications

    async def get_user_notifications(
        self,
        user_id: int,
        pagination: NotificationsPaginationRequest,
    ) -> NotificationsListResponse:
        """Get paginated notifications for a user."""
        async with self._uow:
            try:
                unread_count = await self._uow.notifications.get_unread_count(user_id)

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.notifications.get_by_user_id(
                        user_id=user_id,
                        skip=skip,
                        limit=limit,
                        unread_only=pagination.unread_only,
                    )

                response = await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=NotificationsListResponse,
                    item_schema=NotificationResponse,
                )

                response.unread_count = unread_count
                return response

            except Exception as e:
                logger.error(
                    "Error fetching notifications for user %s: %s",
                    user_id,
                    e,
                )
                raise ServiceException("Failed to retrieve notifications")

    async def mark_notification_as_read(
        self,
        notification_id: int,
        user_id: int,
    ) -> MarkAsReadResponse:
        """
        Mark a single notification as read.

        Security:
        - enforced at DB level (notification_id + user_id)
        """
        try:
            notification = await self._uow.notifications.mark_as_read(
                notification_id=notification_id,
                user_id=user_id,
            )

            if not notification:
                raise NotFoundException("Notification not found")

            await self._uow.commit()

            if self._websocket_service:
                await self._websocket_service.broadcast_notification_read(
                    user_id=user_id,
                    notification_id=notification_id,
                )

            return MarkAsReadResponse.model_validate(notification)

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(
                "Error marking notification %s as read for user %s: %s",
                notification_id,
                user_id,
                e,
            )
            raise ServiceException("Failed to mark notification as read")

    async def mark_all_as_read(self, user_id: int) -> MarkAllAsReadResponse:
        """
        Mark all unread notifications as read for a user.
        """
        try:
            marked_count = await self._uow.notifications.mark_all_as_read(user_id)
            await self._uow.commit()

            if self._websocket_service and marked_count > 0:
                await self._websocket_service.broadcast_all_notifications_read(user_id)

            return MarkAllAsReadResponse(
                message=f"{marked_count} notification{'s' if marked_count != 1 else ''} marked as read",
                marked_count=marked_count,
            )

        except Exception as e:
            logger.error(
                "Error marking all notifications as read for user %s: %s",
                user_id,
                e,
            )
            raise ServiceException("Failed to mark all notifications as read")
