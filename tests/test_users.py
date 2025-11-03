import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)


# --- Database connection fixture ---
@pytest_asyncio.fixture(scope="function")
async def db_connection():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        await conn.run_sync(Base.metadata.drop_all)


# --- Session factory ---
def get_session_factory_for_tests(conn):
    return async_sessionmaker(conn, expire_on_commit=False, class_=AsyncSession)


# --- Override get_db dependency ---
@pytest_asyncio.fixture(scope="function")
async def override_get_db_fixture(db_connection):
    TestSessionLocal = get_session_factory_for_tests(db_connection)

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db)


# --- Test client ---
@pytest_asyncio.fixture(scope="function")
async def client(override_get_db_fixture):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- Database session fixture ---
@pytest_asyncio.fixture(scope="function")
async def db_session(db_connection):
    TestSessionLocal = get_session_factory_for_tests(db_connection)
    async with TestSessionLocal() as session:
        yield session


# --- Test user fixture ---
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


# ==================== TESTS ====================


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    user_data = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "password123",
    }

    response = await client.post("/users", json=user_data)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, test_user: User):
    user_data = {
        "email": test_user.email,
        "full_name": "Another User",
        "password": "password123",
    }

    response = await client.post("/users", json=user_data)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, test_user: User):
    response = await client.get(f"/users/{test_user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    response = await client.get("/users/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_all_users(
    client: AsyncClient, test_user: User, db_session: AsyncSession
):
    from app.core.security import hash_password

    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
    await db_session.commit()

    response = await client.get("/users?page=1&page_size=3")

    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 3
    assert data["total"] == 6
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert data["total_pages"] == 2


@pytest.mark.asyncio
async def test_get_all_users_pagination(client: AsyncClient, test_user: User):
    response = await client.get("/users?page=2&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 10


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, test_user: User):
    update_data = {"full_name": "Updated Name"}

    response = await client.put(f"/users/{test_user.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient):
    update_data = {"full_name": "Updated Name"}

    response = await client.put("/users/99999", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, test_user: User):
    response = await client.delete(f"/users/{test_user.id}")

    assert response.status_code == 204

    get_response = await client.get(f"/users/{test_user.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient):
    response = await client.delete("/users/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_user_invalid_email(client: AsyncClient):
    user_data = {
        "email": "invalid-email",
        "full_name": "Test User",
        "password": "password123",
    }

    response = await client.post("/users", json=user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_short_password(client: AsyncClient):
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "short",
    }

    response = await client.post("/users", json=user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_password(
    client: AsyncClient, test_user: User, db_session: AsyncSession
):
    from app.core.security import verify_password

    update_data = {"password": "newpassword123"}

    response = await client.put(f"/users/{test_user.id}", json=update_data)

    assert response.status_code == 200

    await db_session.refresh(test_user)

    assert verify_password("newpassword123", test_user.hashed_password)
    assert not verify_password("testpassword123", test_user.hashed_password)
