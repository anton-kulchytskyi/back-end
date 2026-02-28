from httpx import AsyncClient

from app.enums import Role, Status
from app.models import Company, CompanyMember, Invitation, User


async def test_get_my_invitations_empty(client: AsyncClient, test_user_token):
    response = await client.get(
        "/invitations/me",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


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


async def test_decline_invitation_route(
    client: AsyncClient, db_session, test_user, test_user_token
):
    owner = User(email="owner_d@test.com", full_name="Owner", hashed_password="1")
    db_session.add(owner)
    await db_session.flush()

    company = Company(
        name="DeclineCo",
        description="Test description",
        owner_id=owner.id,
    )
    db_session.add(company)
    await db_session.flush()

    db_session.add(
        CompanyMember(company_id=company.id, user_id=owner.id, role=Role.OWNER)
    )
    await db_session.commit()

    inv = Invitation(company_id=company.id, user_id=test_user.id, status=Status.PENDING)
    db_session.add(inv)
    await db_session.commit()

    response = await client.post(
        f"/invitations/{inv.id}/decline",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "declined"


async def test_get_my_invitations_empty_unauthorized(client: AsyncClient):
    response = await client.get("/invitations/me")
    assert response.status_code in (401, 403)


async def test_get_my_invitations_pagination(
    client: AsyncClient,
    db_session,
    test_user,
    test_user_token,
):
    """Ensure invitation pagination works correctly."""

    # Create a company + owner
    owner = User(email="owner@test.com", full_name="Owner", hashed_password="1")
    db_session.add(owner)
    await db_session.flush()

    company = Company(
        name="InvCo",
        description="Test description",
        owner_id=owner.id,
    )
    db_session.add(company)
    await db_session.flush()

    # Owner must be a member
    owner_member = CompanyMember(
        company_id=company.id, user_id=owner.id, role=Role.OWNER
    )
    db_session.add(owner_member)
    await db_session.commit()

    # Create multiple invitations for test_user
    for i in range(5):
        inv = Invitation(
            company_id=company.id,
            user_id=test_user.id,
            status=Status.PENDING,
        )
        db_session.add(inv)
    await db_session.commit()

    # Request: first page, 2 items
    response = await client.get(
        "/invitations/me?page=1&limit=2",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Unified pagination fields
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total_pages"] == 3

    # Results
    assert "results" in data
    assert len(data["results"]) == 2
    assert all(inv["user_id"] == test_user.id for inv in data["results"])
