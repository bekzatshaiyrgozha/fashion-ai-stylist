
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Use a test-specific DB URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# IMPORTANT: configure DB engine/sessionmaker BEFORE importing application
import app.db.db_config as db_config
from app.db.db_config import Base

# create async engine and session factory for tests
engine = create_async_engine(TEST_DATABASE_URL, future=True)
async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# override module-level objects used by the app
db_config.engine = engine
db_config.async_session_maker = async_session_maker

# import app after DB is configured
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(client: AsyncClient):
    # register user via API
    payload = {"first_name": "Test", "last_name": "User", "email": "test@example.com", "password": "secret"}
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    return payload


@pytest_asyncio.fixture
async def test_admin(client: AsyncClient):
    # create admin directly in DB via DAO
    from app.db.repo.user import UserDAO
    from app.auth.auth import get_password_hash
    hashed = get_password_hash("adminpass")
    await UserDAO.create(first_name="Admin", last_name="User", email="admin@example.com", password=hashed, is_admin=True)
    return {"email": "admin@example.com", "password": "adminpass"}


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, test_user):
    # login to receive cookies
    resp = await client.post("/auth/login", json={"email": test_user["email"], "password": test_user["password"]})
    assert resp.status_code == 200
    return resp


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, test_admin):
    resp = await client.post("/auth/login", json={"email": test_admin["email"], "password": test_admin["password"]})
    assert resp.status_code == 200
    return resp


@pytest_asyncio.fixture
async def test_category():
    return {"name": "Tops", "slug": "tops"}


@pytest_asyncio.fixture
async def test_product():
    return {"name": "Demo Shirt", "description": "A demo", "price": 49.9, "category_id": 1, "sizes": ["S","M"], "colors": ["black"], "stock": True}
