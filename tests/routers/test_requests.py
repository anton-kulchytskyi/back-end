from httpx import AsyncClient

from app.models import Company


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


async def test_cancel_request_route(
    client: AsyncClient, db_session, test_user, test_user_token
):
    company = Company(
        name="CancelCo",
        description="Test description",
        owner_id=test_user.id + 1,
    )
    db_session.add(company)
    await db_session.commit()

    create_response = await client.post(
        "/requests",
        json={"company_id": company.id},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/requests/{request_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert delete_response.status_code == 204


async def test_get_my_requests_unauthorized(client: AsyncClient):
    response = await client.get("/requests/me")
    assert response.status_code in (401, 403)


async def test_get_my_requests_route(client: AsyncClient, test_user_token):
    response = await client.get(
        "/requests/me",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200

    data = response.json()

    assert "results" in data
    assert isinstance(data["results"], list)
