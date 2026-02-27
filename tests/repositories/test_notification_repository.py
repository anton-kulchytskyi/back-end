from sqlalchemy.ext.asyncio import AsyncSession

from app.db.notification.notification_repository import NotificationRepository
from app.enums import NotificationStatus
from app.models import Notification


async def test_get_by_user_id(
    db_session: AsyncSession, test_notifications: list[Notification]
):
    repo = NotificationRepository(db_session)
    notifications, total = await repo.get_by_user_id(
        user_id=test_notifications[0].user_id, skip=0, limit=10
    )

    assert total == 5
    assert len(notifications) == 5


async def test_get_by_user_id_unread_only(
    db_session: AsyncSession, test_notifications: list[Notification]
):
    repo = NotificationRepository(db_session)

    notifications, total = await repo.get_by_user_id(
        user_id=test_notifications[0].user_id,
        skip=0,
        limit=10,
        unread_only=True,
    )

    assert total == 3
    assert len(notifications) == 3
    assert all(n.status == NotificationStatus.UNREAD for n in notifications)


async def test_mark_as_read(
    db_session: AsyncSession, test_notifications: list[Notification]
):
    repo = NotificationRepository(db_session)
    unread = test_notifications[0]

    updated = await repo.mark_as_read(
        notification_id=unread.id,
        user_id=unread.user_id,
    )
    await db_session.commit()

    assert updated.status == NotificationStatus.READ


async def test_mark_all_as_read(
    db_session: AsyncSession, test_notifications: list[Notification]
):
    repo = NotificationRepository(db_session)
    user_id = test_notifications[0].user_id

    marked_count = await repo.mark_all_as_read(user_id)
    await db_session.commit()

    assert marked_count == 3
    assert await repo.get_unread_count(user_id) == 0
