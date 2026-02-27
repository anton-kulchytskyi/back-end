from httpx import AsyncClient

from app.db.notification.notification_repository import NotificationRepository
from app.enums import NotificationStatus
from app.models import Company, User


async def test_get_notifications_success(
    client: AsyncClient,
    test_user_token: str,
):
    response = await client.get(
        "/notifications?page=1&limit=10",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert "results" in response.json()


async def test_mark_as_read_success(
    client: AsyncClient,
    test_user_token: str,
    test_notifications,
):
    notif = test_notifications[0]

    response = await client.put(
        f"/notifications/{notif.id}/read",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "read"


async def test_get_notifications_unauthorized(client: AsyncClient):
    response = await client.get("/notifications")
    assert response.status_code in (401, 403)


async def test_quiz_creation_triggers_notifications(
    db_session,
    client: AsyncClient,
    test_user_token: str,
    test_company: Company,
    test_members: list[User],
):
    quiz_data = {
        "title": "Integration Test Quiz",
        "description": "Test",
        "questions": [
            {
                "title": "Q1?",
                "answers": [
                    {"text": "A1", "is_correct": True},
                    {"text": "A2", "is_correct": False},
                ],
            },
            {
                "title": "Q2?",
                "answers": [
                    {"text": "B1", "is_correct": True},
                    {"text": "B2", "is_correct": False},
                ],
            },
        ],
    }

    response = await client.post(
        f"/companies/{test_company.id}/quizzes",
        json=quiz_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 201

    repo = NotificationRepository(db_session)

    for member in test_members:
        notifications, _ = await repo.get_by_user_id(
            user_id=member.id, skip=0, limit=10
        )

        assert len(notifications) == 1
        assert notifications[0].status == NotificationStatus.UNREAD
