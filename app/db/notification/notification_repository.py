from typing import List

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base.base_repository import BaseRepository
from app.enums import NotificationStatus
from app.models import Notification


class NotificationRepository(BaseRepository[Notification]):
    """Repository for Notification model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=Notification, session=session)

    async def get_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False,
    ) -> tuple[List[Notification], int]:
        """Get notifications for a specific user with pagination.

        Args:
            user_id: User ID to filter by
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            unread_only: If True, return only unread notifications

        Returns:
            Tuple of (list of notifications, total count)
        """
        conditions = [Notification.user_id == user_id]

        if unread_only:
            conditions.append(Notification.status == NotificationStatus.UNREAD)

        return await self.get_many_by_filters(
            *conditions,
            skip=skip,
            limit=limit,
            order_by=[Notification.created_at.desc()],
        )

    async def mark_as_read(
        self,
        notification_id: int,
        user_id: int,
    ) -> Notification | None:
        """
        Mark a notification as read.

        Args:
            notification_id: ID of the notification to mark as read

        Returns:
            Updated notification or None if not found
        """
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .values(status=NotificationStatus.READ)
            .returning(Notification)
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        notification = result.scalar_one_or_none()
        if notification:
            await self.session.refresh(notification)

        return notification

    async def mark_all_as_read(self, user_id: int) -> int:
        """
        Mark all unread notifications as read for a user.

        Args:
            user_id: User ID whose notifications to mark as read

        Returns:
            Number of notifications marked as read
        """
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.UNREAD,
            )
            .values(status=NotificationStatus.READ)
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount

    async def get_unread_count(self, user_id: int) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User ID to count unread notifications for

        Returns:
            Number of unread notifications
        """
        return await self.count_by_filters(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD,
        )
