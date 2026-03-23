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
        u = User(id=uuid.uuid4(), email="admin_users@example.com", name="Admin",
                 password_hash=hash_password("pass"), role="superadmin", storage_used=0, storage_quota=0, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def target_user():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="managed@example.com", name="Managed",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.mark.asyncio
async def test_list_users(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get("/api/admin/users", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_search_users(client, admin, target_user):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get(f"/api/admin/users?search=managed", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_user(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.post("/api/admin/users", headers=h, json={
        "email": "created@example.com", "name": "Created", "password": "password123"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_update_user(client, admin, target_user):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.put(f"/api/admin/users/{target_user.id}", headers=h, json={"name": "Updated"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_quota(client, admin, target_user):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.put(f"/api/admin/users/{target_user.id}/quota", headers=h, json={"storage_quota": 10737418240})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_deactivate_user(client, admin, target_user):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.post(f"/api/admin/users/{target_user.id}/deactivate", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_activate_user(client, admin, target_user):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.post(f"/api/admin/users/{target_user.id}/activate", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_password(client, admin, target_user):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.post(f"/api/admin/users/{target_user.id}/reset-password", headers=h)
    assert resp.status_code == 200
    assert "temporary_password" in resp.json()


@pytest.mark.asyncio
async def test_delete_user(client, admin, target_user):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.delete(f"/api/admin/users/{target_user.id}", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_cannot_deactivate_self(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.post(f"/api/admin/users/{admin.id}/deactivate", headers=h)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cannot_delete_self(client, admin):
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.delete(f"/api/admin/users/{admin.id}", headers=h)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_requires_admin(client, target_user):
    h = auth_headers(target_user.id, target_user.email, target_user.role)
    resp = await client.get("/api/admin/users", headers=h)
    assert resp.status_code == 403
