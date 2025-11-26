import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import Role, Status
from app.models import Company, CompanyMember, User
from app.services.companies.permission_service import PermissionService
from app.services.companies.request_service import RequestService


@pytest.mark.asyncio
async def test_create_request_success(db_session: AsyncSession, unit_of_work):
    uow = unit_of_work
    service = RequestService(uow, PermissionService(uow))

    user = User(email="u@test.com", full_name="User", hashed_password="123")

    db_session.add(user)
    await db_session.flush()

    company = Company(
        name="CompX",
        description="Test description",
        owner_id=999,
    )
    db_session.add(company)
    await db_session.commit()

    req = await service.create_request(company.id, user.id)

    assert req.company_id == company.id
    assert req.user_id == user.id
    assert req.status == Status.PENDING


@pytest.mark.asyncio
async def test_cancel_request_success(db_session: AsyncSession, unit_of_work):
    uow = unit_of_work
    service = RequestService(uow, PermissionService(uow))

    user = User(email="c@test.com", full_name="Cancel", hashed_password="123")
    db_session.add(user)
    await db_session.flush()

    company = Company(
        name="CancelCo",
        description="Test description",
        owner_id=999,
    )
    db_session.add(company)
    await db_session.commit()

    req = await service.create_request(company.id, user.id)
    updated = await service.cancel_request(req.id, user.id)

    assert updated.status == Status.CANCELED


@pytest.mark.asyncio
async def test_accept_request_owner_only(db_session: AsyncSession, unit_of_work):
    uow = unit_of_work
    service = RequestService(uow, PermissionService(uow))

    owner = User(email="o@test.com", full_name="Owner", hashed_password="123")
    user = User(email="u@test.com", full_name="User", hashed_password="123")

    db_session.add_all([owner, user])
    await db_session.flush()

    company = Company(
        name="AccCo",
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

    req = await service.create_request(company.id, user.id)
    accepted = await service.accept_request(req.id, company.id, owner.id)

    assert accepted.status == Status.ACCEPTED

    new_member = await uow.company_member.get_member_by_ids(company.id, user.id)
    assert new_member is not None
