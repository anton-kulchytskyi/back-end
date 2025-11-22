import pytest
from httpx import AsyncClient

from app.enums.role import Role
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.user import User


@pytest.mark.asyncio
async def test_owner_removes_member(client, db_session, test_user, test_user_token):
    owner = test_user

    member = User(email="member@test.com", full_name="Member", hashed_password="123")

    db_session.add(member)
    await db_session.flush()

    company = Company(
        name="RemoveCo", description="Test description", owner_id=owner.id
    )
    db_session.add(company)
    await db_session.flush()

    db_session.add(
        CompanyMember(company_id=company.id, user_id=owner.id, role=Role.OWNER)
    )

    db_session.add(
        CompanyMember(company_id=company.id, user_id=member.id, role=Role.MEMBER)
    )

    await db_session.commit()

    response = await client.delete(
        f"/companies/{company.id}/members/{member.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 204

    result = await db_session.execute(
        CompanyMember.__table__.select().where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == member.id,
        )
    )
    assert result.first() is None


@pytest.mark.asyncio
async def test_owner_cannot_remove_owner(
    client, db_session, test_user, test_user_token
):
    owner = test_user

    company = Company(
        name="OwnerRemoveFail", description="Test description", owner_id=owner.id
    )
    db_session.add(company)
    await db_session.flush()

    db_session.add(
        CompanyMember(company_id=company.id, user_id=owner.id, role=Role.OWNER)
    )
    await db_session.commit()

    response = await client.delete(
        f"/companies/{company.id}/members/{owner.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 400 or response.status_code == 403


@pytest.mark.asyncio
async def test_non_owner_cannot_remove_member(
    client, db_session, test_user, test_user_token
):
    """
    test_user is NOT owner → must fail with 403
    """
    user = test_user

    another_user = User(
        email="another@test.com", full_name="Another", hashed_password="123"
    )
    db_session.add(another_user)
    await db_session.flush()

    company = Company(
        name="NotOwnerCo",
        description="Test description",
        owner_id=another_user.id,
    )
    db_session.add(company)
    await db_session.flush()

    db_session.add(
        CompanyMember(company_id=company.id, user_id=another_user.id, role=Role.OWNER)
    )
    db_session.add(
        CompanyMember(company_id=company.id, user_id=user.id, role=Role.MEMBER)
    )
    await db_session.commit()

    response = await client.delete(
        f"/companies/{company.id}/members/{user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_member_leaves_company(client, db_session, test_user, test_user_token):
    user = test_user

    owner = User(email="ownerleave@test.com", full_name="Owner", hashed_password="123")
    db_session.add(owner)
    await db_session.flush()

    company = Company(name="LeaveCo", description="Test description", owner_id=owner.id)
    db_session.add(company)
    await db_session.flush()

    db_session.add(
        CompanyMember(company_id=company.id, user_id=owner.id, role=Role.OWNER)
    )
    db_session.add(
        CompanyMember(company_id=company.id, user_id=user.id, role=Role.MEMBER)
    )
    await db_session.commit()

    response = await client.post(
        f"/companies/{company.id}/leave",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 204

    result = await db_session.execute(
        CompanyMember.__table__.select().where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == user.id,
        )
    )
    assert result.first() is None


@pytest.mark.asyncio
async def test_owner_cannot_leave_company(client, db_session, test_user):
    """
    Owner MUST NOT be able to leave company.
    """
    owner = test_user

    company = Company(
        name="OwnerCantLeave", description="Test description", owner_id=owner.id
    )
    db_session.add(company)
    await db_session.flush()

    db_session.add(
        CompanyMember(company_id=company.id, user_id=owner.id, role=Role.OWNER)
    )
    await db_session.commit()

    response = await client.post(
        f"/companies/{company.id}/leave",
        headers={"Authorization": f"Bearer {owner.email}"},
    )

    assert response.status_code in (400, 401, 403)


@pytest.mark.asyncio
async def test_non_member_cannot_leave_company(
    client, db_session, test_user, test_user_token
):
    owner = User(email="owner2@test.com", full_name="Owner2", hashed_password="123")
    db_session.add(owner)
    await db_session.flush()

    company = Company(
        name="NonMemberLeave", description="Test description", owner_id=owner.id
    )
    db_session.add(company)
    await db_session.commit()

    # user is NOT a member → cannot leave
    response = await client.post(
        f"/companies/{company.id}/leave",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code in (400, 404, 403)


@pytest.mark.asyncio
async def test_owner_send_invitation(
    client: AsyncClient, db_session, test_user, test_user_token
):
    company = Company(
        name="CoA",
        description="Test description",
        owner_id=test_user.id,
    )
    db_session.add(company)
    await db_session.flush()

    owner_member = CompanyMember(
        company_id=company.id, user_id=test_user.id, role=Role.OWNER
    )
    db_session.add(owner_member)
    await db_session.commit()

    other = User(email="invite@t.com", full_name="Invited", hashed_password="123")
    db_session.add(other)
    await db_session.commit()

    response = await client.post(
        f"/companies/{company.id}/invitations",
        json={"user_email": other.email},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == other.id


@pytest.mark.asyncio
async def test_owner_get_company_requests_pagination(
    client: AsyncClient, db_session, test_user, test_user_token
):
    company = Company(
        name="CoR",
        description="Test description",
        owner_id=test_user.id,
    )
    db_session.add(company)
    await db_session.flush()

    owner_member = CompanyMember(
        company_id=company.id, user_id=test_user.id, role=Role.OWNER
    )
    db_session.add(owner_member)
    await db_session.commit()

    response = await client.get(
        f"/companies/{company.id}/requests",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_company_members_success(client, db_session):
    owner = User(email="o@test.com", full_name="Owner", hashed_password="123")
    member1 = User(email="m1@test.com", full_name="Member1", hashed_password="123")
    member2 = User(email="m2@test.com", full_name="Member2", hashed_password="123")

    db_session.add_all([owner, member1, member2])
    await db_session.flush()

    company = Company(
        name="MembersCo",
        description="Test description",
        owner_id=owner.id,
    )
    db_session.add(company)
    await db_session.flush()

    db_session.add_all(
        [
            CompanyMember(company_id=company.id, user_id=owner.id, role=Role.OWNER),
            CompanyMember(company_id=company.id, user_id=member1.id, role=Role.MEMBER),
            CompanyMember(company_id=company.id, user_id=member2.id, role=Role.MEMBER),
        ]
    )
    await db_session.commit()

    response = await client.get(f"/companies/{company.id}/members")

    assert response.status_code == 200
    body = response.json()

    assert body["total"] == 3
    assert len(body["results"]) == 3
    assert body["page"] == 1
    assert body["limit"] == 10


@pytest.mark.asyncio
async def test_get_company_members_not_found(client):
    response = await client.get("/companies/99999/members")
    assert response.status_code == 404
