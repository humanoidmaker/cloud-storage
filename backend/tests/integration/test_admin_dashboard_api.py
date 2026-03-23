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
        u = User(id=uuid.uuid4(), email="dash_admin@example.com", name="Admin",
                 password_hash=hash_password("pass"), role="superadmin", storage_used=0, storage_quota=0, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def regular_user():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="dash_user@example.com", name="User",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.mark.asyncio
async def test_dashboard(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/dashboard", headers=h)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "total_storage_used" in data
    assert "total_files" in data


@pytest.mark.asyncio
async def test_dashboard_includes_stats(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/dashboard", headers=h)
    data = resp.json()
    assert "recent_activity" in data
    assert isinstance(data["recent_activity"], list)


@pytest.mark.asyncio
async def test_dashboard_empty_system(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/dashboard", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_non_admin_forbidden(client, regular_user):
    h = auth_headers(regular_user.id, regular_user.email, regular_user.role)
    resp = await client.get("/api/admin/dashboard", headers=h)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_user_count(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/dashboard", headers=h)
    assert resp.json()["total_users"] >= 1
