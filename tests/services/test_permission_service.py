import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedException
from app.enums.role import Role
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.user import User
from app.services.permission_service import PermissionService


@pytest_asyncio.fixture
async def test_company(db_session: AsyncSession):
    company = Company(
        name="Test Company", description="Test", owner_id=1, is_visible=True
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture
async def owner_user(db_session: AsyncSession):
    user = User(email="owner@test.com", full_name="Owner", hashed_password="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession):
    user = User(email="user@test.com", full_name="User", hashed_password="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def owner_membership(
    db_session: AsyncSession, test_company: Company, owner_user: User
):
    member = CompanyMember(
        company_id=test_company.id, user_id=owner_user.id, role=Role.OWNER
    )
    db_session.add(member)
    await db_session.commit()
    return member


@pytest.mark.asyncio
async def test_get_role_owner(
    db_session: AsyncSession,
    test_company: Company,
    owner_user: User,
    unit_of_work,
    owner_membership: CompanyMember,
):
    permission_service = PermissionService(uow=unit_of_work)
    role = await permission_service.get_role(test_company.id, owner_user.id)
    assert role == "owner"


@pytest.mark.asyncio
async def test_get_role_no_membership(
    test_company: Company, regular_user: User, unit_of_work
):
    permission_service = PermissionService(uow=unit_of_work)
    role = await permission_service.get_role(test_company.id, regular_user.id)
    assert role is None


@pytest.mark.asyncio
async def test_require_owner_success(
    db_session: AsyncSession,
    test_company: Company,
    owner_user: User,
    unit_of_work,
    owner_membership: CompanyMember,
):
    permission_service = PermissionService(uow=unit_of_work)
    await permission_service.require_owner(test_company.id, owner_user.id)


@pytest.mark.asyncio
async def test_require_owner_fails_for_non_owner(
    test_company: Company, regular_user: User, unit_of_work
):
    with pytest.raises(
        PermissionDeniedException,
        match="Only the company owner can perform this action",
    ):
        permission_service = PermissionService(uow=unit_of_work)
        await permission_service.require_owner(test_company.id, regular_user.id)


@pytest.mark.asyncio
async def test_require_admin_success_for_owner(
    db_session: AsyncSession,
    test_company: Company,
    owner_user: User,
    unit_of_work,
    owner_membership: CompanyMember,
):
    permission_service = PermissionService(uow=unit_of_work)
    await permission_service.require_admin(test_company.id, owner_user.id)


@pytest.mark.asyncio
async def test_require_admin_fails_for_regular_user(
    test_company: Company, regular_user: User, unit_of_work
):
    with pytest.raises(
        PermissionDeniedException,
        match="Only company admin or owner can perform this action",
    ):
        permission_service = PermissionService(uow=unit_of_work)
        await permission_service.require_admin(test_company.id, regular_user.id)


@pytest.mark.asyncio
async def test_require_member_fails_for_non_member(
    test_company: Company, regular_user: User, unit_of_work
):
    with pytest.raises(
        PermissionDeniedException,
        match="You must be a company member to perform this action",
    ):
        permission_service = PermissionService(uow=unit_of_work)
        await permission_service.require_member(test_company.id, regular_user.id)


@pytest.mark.asyncio
async def test_require_member_success_for_owner(
    test_company: Company,
    owner_user: User,
    unit_of_work,
    owner_membership: CompanyMember,
):
    permission_service = PermissionService(uow=unit_of_work)
    await permission_service.require_member(test_company.id, owner_user.id)
