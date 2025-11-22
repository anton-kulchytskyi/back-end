import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.company import CompanyCreateRequest
from app.services.companies.company_service import CompanyService
from app.services.companies.permission_service import PermissionService


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

    response = await client.get("/companies?page=1&limit=10")
    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["results"]) == 3
    assert data["page"] == 1
    assert data["limit"] == 10


@pytest.mark.asyncio
async def test_get_companies_pagination(client: AsyncClient, test_user_token: str):
    for i in range(5):
        await client.post(
            "/companies",
            json={"name": f"C{i}", "description": "D"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

    response = await client.get("/companies?page=1&limit=2")
    data = response.json()

    assert data["total"] == 5
    assert len(data["results"]) == 2
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

    # Hide second company
    await client.put(
        f"/companies/{hidden_id}",
        json={"is_visible": False},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    response = await client.get("/companies")
    data = response.json()

    assert data["total"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == visible_id


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
    assert response.status_code == 404


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
    client: AsyncClient, test_user_token: str, db_session: AsyncSession, unit_of_work
):
    u2 = User(email="x@x.com", full_name="x", hashed_password="x")
    db_session.add(u2)
    await db_session.commit()
    await db_session.refresh(u2)

    data = CompanyCreateRequest(name="A", description="B")
    permission_service = PermissionService(uow=unit_of_work)
    company_service = CompanyService(
        uow=unit_of_work, permission_service=permission_service
    )

    company = await company_service.create_company(data, u2.id)

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
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_company_not_owner(
    client: AsyncClient, test_user_token: str, db_session: AsyncSession, unit_of_work
):
    u2 = User(email="del@x.com", full_name="x", hashed_password="x")
    db_session.add(u2)
    await db_session.commit()
    await db_session.refresh(u2)

    data = CompanyCreateRequest(name="C", description="D")
    permission_service = PermissionService(uow=unit_of_work)
    company_service = CompanyService(
        uow=unit_of_work, permission_service=permission_service
    )
    company = await company_service.create_company(data, u2.id)

    resp = await client.delete(
        f"/companies/{company.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert resp.status_code == 403
