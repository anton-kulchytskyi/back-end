import pytest
from httpx import AsyncClient

from app.enums.role import Role
from app.enums.status import Status
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.invitation import Invitation
from app.models.user import User


@pytest.mark.asyncio
async def test_get_my_invitations_empty(client: AsyncClient, test_user_token):
    response = await client.get(
        "/invitations/me",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_accept_invitation_route(
    client: AsyncClient, db_session, test_user, test_user_token
):
    owner = User(email="o@test.com", full_name="Owner", hashed_password="1")
    db_session.add(owner)
    await db_session.flush()

    company = Company(
        name="ICo",
        description="Test description",
        owner_id=owner.id,
    )
    db_session.add(company)
    await db_session.flush()

    owner_member = CompanyMember(
        company_id=company.id, user_id=owner.id, role=Role.OWNER
    )
    db_session.add(owner_member)
    await db_session.commit()

    inv = Invitation(
        company_id=company.id,
        user_id=test_user.id,
        status=Status.PENDING,
    )
    db_session.add(inv)
    await db_session.commit()

    response = await client.post(
        f"/invitations/{inv.id}/accept",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
