import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.company import CompanyCreateRequest
from app.services.company_service import company_service


@pytest.mark.asyncio
async def test_create_company(client: AsyncClient, test_user_token: str):
    payload = {"name": "TestCo", "description": "Some description"}

    response = await client.post(
        "/companies",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "TestCo"
    assert data["description"] == "Some description"
    assert data["is_visible"] is True
    assert "id" in data
    assert "owner_id" in data


@pytest.mark.asyncio
async def test_create_company_unauth(client: AsyncClient):
    response = await client.post("/companies", json={"name": "X", "description": "Y"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_companies_list(
    client: AsyncClient, db_session: AsyncSession, test_user_token: str
):
    for i in range(3):
        await client.post(
            "/companies",
            json={"name": f"C{i}", "description": "D"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

    response = await client.get("/companies?page=1&page_size=10")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 3
    assert len(data["companies"]) == 3
    assert data["page"] == 1
    assert data["page_size"] == 10


@pytest.mark.asyncio
async def test_get_companies_pagination(client: AsyncClient, test_user_token: str):
    for i in range(5):
        await client.post(
            "/companies",
            json={"name": f"C{i}", "description": "D"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

    response = await client.get("/companies?page=1&page_size=2")
    data = response.json()

    assert data["total"] == 5
    assert len(data["companies"]) == 2
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_get_companies_only_visible(
    client: AsyncClient, test_user_token: str, db_session: AsyncSession
):
    resp1 = await client.post(
        "/companies",
        json={"name": "Visible", "description": "D"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    visible_id = resp1.json()["id"]

    resp2 = await client.post(
        "/companies",
        json={"name": "Hidden", "description": "D"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    hidden_id = resp2.json()["id"]

    await client.put(
        f"/companies/{hidden_id}",
        json={"is_visible": False},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    response = await client.get("/companies")
    data = response.json()

    assert data["total"] == 1
    assert len(data["companies"]) == 1
    assert data["companies"][0]["id"] == visible_id


@pytest.mark.asyncio
async def test_get_company_by_id(client: AsyncClient, test_user_token: str):
    create = await client.post(
        "/companies",
        json={"name": "Single", "description": "D"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    company_id = create.json()["id"]

    response = await client.get(f"/companies/{company_id}")
    assert response.status_code == 200
    assert response.json()["id"] == company_id


@pytest.mark.asyncio
async def test_get_company_by_id_not_found(client: AsyncClient):
    response = await client.get("/companies/9999")
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_update_company_owner(client: AsyncClient, test_user_token: str):
    create = await client.post(
        "/companies",
        json={"name": "Before", "description": "D"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    company_id = create.json()["id"]

    response = await client.put(
        f"/companies/{company_id}",
        json={"name": "After"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "After"


@pytest.mark.asyncio
async def test_update_company_visibility(client: AsyncClient, test_user_token: str):
    create = await client.post(
        "/companies",
        json={"name": "Test", "description": "D"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    company_id = create.json()["id"]

    response = await client.put(
        f"/companies/{company_id}",
        json={"is_visible": False},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["is_visible"] is False


@pytest.mark.asyncio
async def test_update_company_not_owner(
    client: AsyncClient, test_user_token: str, db_session: AsyncSession
):
    u2 = User(email="x@x.com", full_name="x", hashed_password="x")
    db_session.add(u2)
    await db_session.commit()
    await db_session.refresh(u2)

    data = CompanyCreateRequest(name="A", description="B")
    company = await company_service.create_company(db_session, data, u2.id)

    resp = await client.put(
        f"/companies/{company.id}",
        json={"name": "Hack"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_company_owner(client: AsyncClient, test_user_token: str):
    create = await client.post(
        "/companies",
        json={"name": "Del", "description": "D"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    company_id = create.json()["id"]

    response = await client.delete(
        f"/companies/{company_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 204

    get_resp = await client.get(f"/companies/{company_id}")
    assert get_resp.status_code == 500  # Company not found


@pytest.mark.asyncio
async def test_delete_company_not_owner(
    client: AsyncClient, test_user_token: str, db_session: AsyncSession
):
    u2 = User(email="del@x.com", full_name="x", hashed_password="x")
    db_session.add(u2)
    await db_session.commit()
    await db_session.refresh(u2)

    data = CompanyCreateRequest(name="C", description="D")
    company = await company_service.create_company(db_session, data, u2.id)

    resp = await client.delete(
        f"/companies/{company.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert resp.status_code == 403
