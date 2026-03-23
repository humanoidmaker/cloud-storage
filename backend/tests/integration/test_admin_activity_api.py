import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.models.activity_log import ActivityLog
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
        u = User(id=uuid.uuid4(), email="act_admin@example.com", name="Admin",
                 password_hash=hash_password("pass"), role="superadmin", storage_used=0, storage_quota=0, is_active=True)
        session.add(u)
        for action in ["upload", "download", "login"]:
            log = ActivityLog(id=uuid.uuid4(), user_id=u.id, action=action, ip_address="127.0.0.1")
            session.add(log)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.mark.asyncio
async def test_global_activity(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/activity", headers=h)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_filter_by_user(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get(f"/api/admin/activity?user_id={admin.id}", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_filter_by_action(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/activity?action=upload", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_filter_by_date(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/activity?date_from=2020-01-01T00:00:00Z&date_to=2030-01-01T00:00:00Z", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_export_csv(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/activity/export", headers=h)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_non_admin(client):
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="nonadmin_act@example.com", name="User",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        h = auth_headers(u.id, u.email, u.role)
    resp = await client.get("/api/admin/activity", headers=h)
    assert resp.status_code == 403
