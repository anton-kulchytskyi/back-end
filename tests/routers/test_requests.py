import pytest
from httpx import AsyncClient

from app.models.company import Company


@pytest.mark.asyncio
async def test_create_request_route(
    client: AsyncClient, db_session, test_user, test_user_token
):
    company = Company(
        name="RoutCo",
        description="Test description",
        owner_id=test_user.id + 1,
    )
    db_session.add(company)
    await db_session.commit()

    response = await client.post(
        "/requests",
        json={"company_id": company.id},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["company_id"] == company.id
    assert body["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_get_my_requests_route(client: AsyncClient, test_user_token):
    response = await client.get(
        "/requests/me",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200
    assert "requests" in response.json()
