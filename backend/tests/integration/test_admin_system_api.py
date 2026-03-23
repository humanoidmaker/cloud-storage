import uuid
from unittest.mock import patch, MagicMock
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.models.user import User
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal, auth_headers


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def admin():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="sys_admin@example.com", name="Admin",
                 password_hash=hash_password("pass"), role="superadmin", storage_used=0, storage_quota=0, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.mark.asyncio
async def test_health(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/system/health", headers=h)
    assert resp.status_code == 200
    data = resp.json()
    assert "minio" in data
    assert "postgres" in data
    assert "redis" in data
    assert "celery" in data
    assert "api" in data


@pytest.mark.asyncio
async def test_minio_status(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/system/minio", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_database_status(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/system/database", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_redis_status(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/system/redis", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_celery_status(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/system/celery", headers=h)
    assert resp.status_code == 200
