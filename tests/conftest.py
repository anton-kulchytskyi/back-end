import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.core.dependencies import get_auth_service, get_uow, get_user_service
from app.core.unit_of_work import AbstractUnitOfWork
from app.enums.role import Role
from app.main import app
from app.models.company_member import CompanyMember
from app.models.user import User
from app.services.users.user_service import UserService

# ==================== TEST DATABASE SETUP ====================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(expire_on_commit=False, class_=AsyncSession)


class TestSQLAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        from app.db import (
            CompanyMemberRepository,
            CompanyRepository,
            InvitationRepository,
            RequestRepository,
            UserRepository,
        )

        self.company_member = CompanyMemberRepository(self.session)
        self.companies = CompanyRepository(self.session)
        self.invitations = InvitationRepository(self.session)
        self.requests = RequestRepository(self.session)
        self.users = UserRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def commit(self):
        await self.session.flush()

    async def rollback(self):
        pass


# ==================== FIXTURES ====================


@pytest_asyncio.fixture(scope="session")
async def db_connection():
    connection = await test_engine.connect()

    await connection.run_sync(Base.metadata.create_all)

    yield connection

    await connection.close()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_connection: AsyncConnection):
    transaction = await db_connection.begin_nested()

    async with TestSessionLocal(
        bind=db_connection, join_transaction_mode="create_savepoint"
    ) as session:
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def unit_of_work(db_session: AsyncSession):
    uow = TestSQLAlchemyUnitOfWork(session=db_session)
    return uow


@pytest_asyncio.fixture(scope="function")
async def override_dependencies_fixture(db_session: AsyncSession):
    test_uow = TestSQLAlchemyUnitOfWork(db_session)

    def override_get_uow():
        return test_uow

    def override_get_user_service():
        from app.services.users.user_service import UserService

        return UserService(test_uow)

    def override_get_auth_service():
        from app.services.users.auth_service import AuthService

        return AuthService(uow=test_uow, user_service=UserService(test_uow))

    app.dependency_overrides[get_uow] = override_get_uow
    app.dependency_overrides[get_user_service] = override_get_user_service
    app.dependency_overrides[get_auth_service] = override_get_auth_service

    yield

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(override_dependencies_fixture):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    from app.core.security import hash_password

    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_token(client: AsyncClient, test_user: User):
    login_data = {
        "username": "test@example.com",
        "password": "testpassword123",
    }
    response = await client.post("/auth/login", data=login_data)
    token_data = response.json()
    return token_data["access_token"]


# ==========================================
# Additional factories for company tests
# ==========================================


@pytest_asyncio.fixture
async def another_user(db_session: AsyncSession):
    from app.core.security import hash_password

    user = User(
        email="another@example.com",
        full_name="Another User",
        hashed_password=hash_password("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def third_user(db_session: AsyncSession):
    from app.core.security import hash_password

    user = User(
        email="third@example.com",
        full_name="Third User",
        hashed_password=hash_password("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_header(client: AsyncClient):
    async def _get_auth_header(user):
        login_data = {
            "username": user.email,
            "password": "password123",
        }
        response = await client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _get_auth_header


@pytest_asyncio.fixture
async def company_factory(
    db_session: AsyncSession, unit_of_work: TestSQLAlchemyUnitOfWork
):
    async def _create_company(owner_id: int, name: str = "Test Company"):
        from app.models.company import Company

        company = Company(
            name=name,
            description="desc",
            is_visible=True,
            owner_id=owner_id,
        )
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)

        # owner must also be a CompanyMember
        owner_member = CompanyMember(
            company_id=company.id,
            user_id=owner_id,
            role=Role.OWNER,
        )
        db_session.add(owner_member)
        await db_session.commit()

        return company

    return _create_company


@pytest_asyncio.fixture
async def membership_factory(db_session: AsyncSession):
    async def _create_member(company_id: int, user_id: int, role: Role):
        member = CompanyMember(
            company_id=company_id,
            user_id=user_id,
            role=role,
        )
        db_session.add(member)
        await db_session.commit()
        await db_session.refresh(member)
        return member

    return _create_member


# ==================== PYTEST CONFIGURATION ====================


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as async")
