import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.role import Role
from app.enums.status import Status
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.user import User
from app.services.companies.invitation_service import InvitationService
from app.services.companies.permission_service import PermissionService


@pytest.mark.asyncio
async def test_send_invitation_success(db_session: AsyncSession, unit_of_work):
    uow = unit_of_work
    service = InvitationService(uow, PermissionService(uow))

    owner = User(email="own@test.com", full_name="Owner", hashed_password="123")
    user = User(email="user@test.com", full_name="User", hashed_password="123")

    db_session.add_all([owner, user])
    await db_session.flush()

    company = Company(
        name="InvCo",
        description="Test description",
        owner_id=owner.id,
    )
    db_session.add(company)
    await db_session.flush()

    owner_member = CompanyMember(
        company_id=company.id,
        user_id=owner.id,
        role=Role.OWNER,
    )
    db_session.add(owner_member)
    await db_session.commit()

    inv = await service.send_invitation(company.id, user.email, owner.id)

    assert inv.company_id == company.id
    assert inv.user_id == user.id
    assert inv.status == Status.PENDING


@pytest.mark.asyncio
async def test_accept_invitation_user_only(db_session: AsyncSession, unit_of_work):
    uow = unit_of_work
    service = InvitationService(uow, PermissionService(uow))

    owner = User(email="a@test.com", full_name="Owner", hashed_password="1")
    user = User(email="b@test.com", full_name="User", hashed_password="1")

    db_session.add_all([owner, user])
    await db_session.flush()

    company = Company(
        name="AccInv",
        description="Test description",
        owner_id=owner.id,
    )
    db_session.add(company)
    await db_session.flush()

    owner_member = CompanyMember(
        company_id=company.id,
        user_id=owner.id,
        role=Role.OWNER,
    )
    db_session.add(owner_member)
    await db_session.commit()

    inv = await service.send_invitation(company.id, user.email, owner.id)
    accepted = await service.accept_invitation(inv.id, user.id)

    assert accepted.status == Status.ACCEPTED


@pytest.mark.asyncio
async def test_decline_invitation_user_only(db_session: AsyncSession, unit_of_work):
    uow = unit_of_work
    service = InvitationService(uow, PermissionService(uow))

    owner = User(email="xx@test.com", full_name="Owner", hashed_password="1")
    user = User(email="yy@test.com", full_name="User", hashed_password="1")

    db_session.add_all([owner, user])
    await db_session.flush()

    company = Company(
        name="DeclCo",
        description="Test description",
        owner_id=owner.id,
    )
    db_session.add(company)
    await db_session.flush()

    owner_member = CompanyMember(
        company_id=company.id,
        user_id=owner.id,
        role=Role.OWNER,
    )
    db_session.add(owner_member)
    await db_session.commit()

    inv = await service.send_invitation(company.id, user.email, owner.id)
    declined = await service.decline_invitation(inv.id, user.id)

    assert declined.status == Status.DECLINED
