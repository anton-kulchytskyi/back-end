import pytest

from app.core.exceptions import NotFoundException
from app.enums import NotificationStatus
from app.models import Company, Notification, User
from app.schemas.notification.notification import NotificationsPaginationRequest
from app.services.notification.notification_service import NotificationService


async def test_create_notifications_for_company_members(
    unit_of_work,
    test_company: Company,
    test_members: list[User],
    test_user: User,
):
    uow = unit_of_work
    notification_service = NotificationService(uow)
    notifications = await notification_service.create_notifications_for_company_members(
        company_id=test_company.id,
        quiz_title="Python Basics",
        exclude_user_id=test_user.id,
    )

    assert len(notifications) == len(test_members)
    assert all(n.status == NotificationStatus.UNREAD for n in notifications)


async def test_get_user_notifications(
    unit_of_work,
    test_notifications: list[Notification],
):
    uow = unit_of_work
    notification_service = NotificationService(uow)
    pagination = NotificationsPaginationRequest(page=1, limit=10)

    response = await notification_service.get_user_notifications(
        user_id=test_notifications[0].user_id,
        pagination=pagination,
    )

    assert response.total == 5
    assert response.unread_count == 3


async def test_mark_notification_as_read_success(
    unit_of_work,
    test_notifications: list[Notification],
):
    uow = unit_of_work
    notification_service = NotificationService(uow)
    notif = test_notifications[0]

    response = await notification_service.mark_notification_as_read(
        notification_id=notif.id,
        user_id=notif.user_id,
    )

    assert response.status == NotificationStatus.READ


async def test_mark_notification_as_read_not_found(
    unit_of_work,
):
    uow = unit_of_work
    notification_service = NotificationService(uow)
    with pytest.raises(NotFoundException):
        await notification_service.mark_notification_as_read(
            notification_id=99999,
            user_id=1,
        )
