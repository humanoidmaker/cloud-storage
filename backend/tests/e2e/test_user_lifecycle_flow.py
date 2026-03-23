import uuid
from unittest.mock import MagicMock, patch

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
        u = User(id=uuid.uuid4(), email="e2e_admin@example.com", name="Admin",
                 password_hash=hash_password("admin123"), role="superadmin", storage_used=0, storage_quota=0, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.fixture
def mock_storage():
    with patch("app.services.storage_service.get_minio_client") as m:
        mc = MagicMock()
        mc.put_object.return_value = None
        mc.remove_object.return_value = None
        m.return_value = mc
        yield


@pytest.mark.asyncio
async def test_user_lifecycle(client, admin, mock_storage):
    ah = auth_headers(admin.id, admin.email, admin.role)

    # Register new user
    resp = await client.post("/api/auth/register", json={
        "email": "lifecycle@example.com", "name": "Lifecycle User", "password": "password123"})
    assert resp.status_code == 201

    # Login
    resp = await client.post("/api/auth/login", json={
        "email": "lifecycle@example.com", "password": "password123"})
    assert resp.status_code == 200
    tokens = resp.json()
    uh = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Upload a file
    with patch("app.api.files.generate_thumbnail"):
        resp = await client.post("/api/files/upload", headers=uh,
            files={"file": ("lifecycle.txt", b"lifecycle data", "text/plain")})
    assert resp.status_code == 201

    # Admin changes quota to tiny amount
    me = await client.get("/api/auth/me", headers=uh)
    user_id = me.json()["id"]

    resp = await client.put(f"/api/admin/users/{user_id}/quota", headers=ah,
        json={"storage_quota": 100})
    assert resp.status_code == 200

    # Admin deactivates user
    resp = await client.post(f"/api/admin/users/{user_id}/deactivate", headers=ah)
    assert resp.status_code == 200

    # User cannot login
    resp = await client.post("/api/auth/login", json={
        "email": "lifecycle@example.com", "password": "password123"})
    assert resp.status_code == 403

    # Admin reactivates
    resp = await client.post(f"/api/admin/users/{user_id}/activate", headers=ah)
    assert resp.status_code == 200

    # User can login again
    resp = await client.post("/api/auth/login", json={
        "email": "lifecycle@example.com", "password": "password123"})
    assert resp.status_code == 200

    # Admin creates another user to transfer files to
    resp = await client.post("/api/admin/users", headers=ah, json={
        "email": "receiver@example.com", "name": "Receiver", "password": "password123"})
    receiver_id = resp.json()["id"]

    # Admin deletes lifecycle user with file transfer
    resp = await client.delete(f"/api/admin/users/{user_id}?transfer_to={receiver_id}", headers=ah)
    assert resp.status_code == 200
