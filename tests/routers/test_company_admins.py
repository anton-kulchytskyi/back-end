import pytest
from httpx import AsyncClient

from app.models.company_member import Role


@pytest.mark.asyncio
async def test_owner_can_appoint_admin(
    client: AsyncClient,
    test_user,
    another_user,
    auth_header,
    company_factory,
    membership_factory,
):
    company = await company_factory(owner_id=test_user.id)
    await membership_factory(company.id, another_user.id, Role.MEMBER)

    response = await client.post(
        f"/companies/{company.id}/admins/{another_user.id}", headers=auth_header
    )

    assert response.status_code == 200
    assert response.json()["role"] == Role.ADMIN


@pytest.mark.asyncio
async def test_member_cannot_appoint_admin(
    client,
    test_user,
    another_user,
    third_user,
    company_factory,
    membership_factory,
    get_auth_header,
):
    company = await company_factory(owner_id=test_user.id)

    # another_user = MEMBER (tries to appoint)
    await membership_factory(company.id, another_user.id, Role.MEMBER)

    # third_user = MEMBER (target)
    await membership_factory(company.id, third_user.id, Role.MEMBER)

    member_header = await get_auth_header(another_user)

    response = await client.post(
        f"/companies/{company.id}/admins/{third_user.id}",
        headers=member_header,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_cannot_appoint_admin(
    client,
    test_user,
    another_user,
    third_user,
    company_factory,
    membership_factory,
    get_auth_header,
):
    company = await company_factory(owner_id=test_user.id)

    await membership_factory(company.id, another_user.id, Role.ADMIN)
    await membership_factory(company.id, third_user.id, Role.MEMBER)

    admin_header = await get_auth_header(another_user)

    response = await client.post(
        f"/companies/{company.id}/admins/{third_user.id}",
        headers=admin_header,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cannot_appoint_non_member(
    client,
    test_user,
    another_user,
    auth_header,
    company_factory,
):
    company = await company_factory(owner_id=test_user.id)

    # another_user is NOT a member
    response = await client.post(
        f"/companies/{company.id}/admins/{another_user.id}",
        headers=auth_header,
    )

    # Depending on implementation, this may be 400 or 404
    assert response.status_code in (400, 404)


@pytest.mark.asyncio
async def test_owner_can_remove_admin(
    client,
    test_user,
    another_user,
    auth_header,
    company_factory,
    membership_factory,
):
    company = await company_factory(owner_id=test_user.id)

    await membership_factory(company.id, another_user.id, Role.ADMIN)

    response = await client.delete(
        f"/companies/{company.id}/admins/{another_user.id}",
        headers=auth_header,
    )

    assert response.status_code == 200
    assert response.json()["role"] == Role.MEMBER


@pytest.mark.asyncio
async def test_cannot_remove_owner(
    client,
    test_user,
    auth_header,
    company_factory,
):
    company = await company_factory(owner_id=test_user.id)

    response = await client.delete(
        f"/companies/{company.id}/admins/{test_user.id}",
        headers=auth_header,
    )

    assert response.status_code in (400, 403)


@pytest.mark.asyncio
async def test_get_admins_list(
    client,
    test_user,
    another_user,
    auth_header,
    company_factory,
    membership_factory,
):
    company = await company_factory(owner_id=test_user.id)
    await membership_factory(company.id, another_user.id, Role.ADMIN)

    response = await client.get(
        f"/companies/{company.id}/admins?page=1&page_size=10",
        headers=auth_header,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(m["role"] == Role.ADMIN for m in data["members"])


@pytest.mark.asyncio
async def test_non_member_cannot_view_admins(
    client,
    test_user,
    another_user,
    get_auth_header,
    company_factory,
):
    company = await company_factory(owner_id=test_user.id)

    another_header = await get_auth_header(another_user)

    response = await client.get(
        f"/companies/{company.id}/admins",
        headers=another_header,
    )

    assert response.status_code == 403
