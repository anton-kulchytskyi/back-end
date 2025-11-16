import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedException, ServiceException
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreateRequest, CompanyUpdateRequest
from app.services.company_service import company_service


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession):
    user = User(
        email="owner@example.com",
        full_name="Owner User",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def member(db_session: AsyncSession):
    user = User(
        email="member@example.com",
        full_name="Member User",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def created_company(db_session: AsyncSession, owner: User):
    data = CompanyCreateRequest(name="TestCo", description="Test Description")
    company = await company_service.create_company(db_session, data, owner.id)
    return company


@pytest.mark.asyncio
async def test_create_company(db_session: AsyncSession, owner: User):
    data = CompanyCreateRequest(name="NewCo", description="Some description")
    company = await company_service.create_company(db_session, data, owner.id)

    assert company.id is not None
    assert company.name == "NewCo"
    assert company.description == "Some description"
    assert company.owner_id == owner.id
    assert company.is_visible is True

    from app.db.company_member_repository import company_member_repository

    member = await company_member_repository.get_member(
        db_session, company.id, owner.id
    )
    assert member is not None
    assert member.role == "owner"


@pytest.mark.asyncio
async def test_get_company_by_id(db_session: AsyncSession, created_company: Company):
    company = await company_service.get_company_by_id(db_session, created_company.id)
    assert company.id == created_company.id
    assert company.name == created_company.name


@pytest.mark.asyncio
async def test_get_company_by_id_not_found(db_session: AsyncSession):
    with pytest.raises(ServiceException, match="not found"):
        await company_service.get_company_by_id(db_session, 999)


@pytest.mark.asyncio
async def test_get_all_visible_companies(db_session: AsyncSession, owner: User):
    await company_service.create_company(
        db_session, CompanyCreateRequest(name="C1", description="D1"), owner.id
    )
    await company_service.create_company(
        db_session, CompanyCreateRequest(name="C2", description="D2"), owner.id
    )

    hidden = await company_service.create_company(
        db_session, CompanyCreateRequest(name="C3", description="D3"), owner.id
    )
    hidden.is_visible = False
    await db_session.commit()

    companies, total = await company_service.get_all_companies(db_session, 0, 10)

    assert total == 2
    assert len(companies) == 2
    assert all(c.is_visible for c in companies)


@pytest.mark.asyncio
async def test_get_user_companies(db_session: AsyncSession, owner: User):
    data1 = CompanyCreateRequest(name="O1", description="D1")
    data2 = CompanyCreateRequest(name="O2", description="D2")
    await company_service.create_company(db_session, data1, owner.id)
    await company_service.create_company(db_session, data2, owner.id)

    companies, total = await company_service.get_user_companies(
        db_session, owner.id, 0, 10
    )

    assert total == 2
    assert len(companies) == 2
    assert all(c.owner_id == owner.id for c in companies)


@pytest.mark.asyncio
async def test_update_company_owner(
    db_session: AsyncSession, created_company: Company, owner: User
):
    update_data = CompanyUpdateRequest(
        name="Updated", description="New Description", is_visible=False
    )

    updated = await company_service.update_company(
        db_session, created_company, update_data, owner.id
    )

    assert updated.name == "Updated"
    assert updated.description == "New Description"
    assert updated.is_visible is False


@pytest.mark.asyncio
async def test_update_company_partial(
    db_session: AsyncSession, created_company: Company, owner: User
):
    update_data = CompanyUpdateRequest(name="Only Name")

    updated = await company_service.update_company(
        db_session, created_company, update_data, owner.id
    )

    assert updated.name == "Only Name"
    assert updated.description == created_company.description


@pytest.mark.asyncio
async def test_update_company_not_owner(
    db_session: AsyncSession, created_company: Company, member: User
):
    update_data = CompanyUpdateRequest(name="Fail", description="Fail")

    with pytest.raises(
        PermissionDeniedException,
        match="Only the company owner can perform this action",
    ):
        await company_service.update_company(
            db_session, created_company, update_data, member.id
        )


@pytest.mark.asyncio
async def test_delete_company_owner(
    db_session: AsyncSession, created_company: Company, owner: User
):
    await company_service.delete_company(db_session, created_company, owner.id)

    deleted = await db_session.get(Company, created_company.id)
    assert deleted is None

    from app.db.company_member_repository import company_member_repository

    member = await company_member_repository.get_member(
        db_session, created_company.id, owner.id
    )
    assert member is None


@pytest.mark.asyncio
async def test_delete_company_not_owner(
    db_session: AsyncSession, created_company: Company, member: User
):
    with pytest.raises(
        PermissionDeniedException,
        match="Only the company owner can perform this action",
    ):
        await company_service.delete_company(db_session, created_company, member.id)
