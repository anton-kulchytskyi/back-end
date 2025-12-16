import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_get_notifications_unauthorized(client: AsyncClient):
    response = await client.get("/notifications")
    assert response.status_code in (401, 403)
