import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User

# ==================== TEST DATABASE SETUP ====================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)


# ==================== FIXTURES ====================


@pytest_asyncio.fixture(scope="function")
async def db_connection():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        await conn.run_sync(Base.metadata.drop_all)


def get_session_factory_for_tests(conn):
    return async_sessionmaker(conn, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(scope="function")
async def override_get_db_fixture(db_connection):
    TestSessionLocal = get_session_factory_for_tests(db_connection)

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db)


@pytest_asyncio.fixture(scope="function")
async def client(override_get_db_fixture):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def db_session(db_connection):
    TestSessionLocal = get_session_factory_for_tests(db_connection)
    async with TestSessionLocal() as session:
        yield session


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


# ==================== PYTEST CONFIGURATION ====================


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as async")
