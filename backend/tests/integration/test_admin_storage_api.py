import uuid
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
        u = User(id=uuid.uuid4(), email="stor_admin@example.com", name="Admin",
                 password_hash=hash_password("pass"), role="superadmin", storage_used=0, storage_quota=0, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def regular():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="stor_user@example.com", name="User",
                 password_hash=hash_password("pass"), role="user", storage_used=1000, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.mark.asyncio
async def test_breakdown(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/storage/breakdown", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_top_consumers(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/storage/top-consumers", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_trends(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/storage/trends", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_bulk_quota(client, admin, regular):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.post("/api/admin/storage/bulk-quota", headers=h,
        json={"user_ids": [str(regular.id)], "storage_quota": 10737418240})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_non_admin(client, regular):
    h = auth_headers(regular.id, regular.email, regular.role)
    resp = await client.get("/api/admin/storage/breakdown", headers=h)
    assert resp.status_code == 403
