import uuid
from datetime import datetime, timedelta, timezone
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
async def user_a():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="e2e_a@example.com", name="User A",
                 password_hash=hash_password("pass123"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def user_b():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="e2e_b@example.com", name="User B",
                 password_hash=hash_password("pass123"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.fixture
def mock_storage():
    with patch("app.services.storage_service.get_minio_client") as m:
        mc = MagicMock()
        mc.put_object.return_value = None
        resp = MagicMock()
        resp.read.return_value = b"content"
        resp.close.return_value = None
        resp.release_conn.return_value = None
        mc.get_object.return_value = resp
        mc.presigned_get_object.return_value = "https://minio.local/file"
        mc.remove_object.return_value = None
        mc.copy_object.return_value = None
        mc.stat_object.return_value = MagicMock(size=100, content_type="text/plain", etag="x", last_modified=None)
        m.return_value = mc
        yield


@pytest.mark.asyncio
async def test_upload_share_download_flow(client, user_a, user_b, mock_storage):
    ha = auth_headers(user_a.id, user_a.email, user_a.role)
    hb = auth_headers(user_b.id, user_b.email, user_b.role)

    # User A uploads file
    with patch("app.api.files.generate_thumbnail"):
        resp = await client.post("/api/files/upload", headers=ha,
            files={"file": ("shared_doc.txt", b"hello world", "text/plain")})
    assert resp.status_code == 201
    file_id = resp.json()["id"]

    # User B cannot access
    resp = await client.get(f"/api/files/{file_id}", headers=hb)
    assert resp.status_code == 403

    # User A shares with User B (view)
    resp = await client.post("/api/shares", headers=ha, json={
        "file_id": file_id, "shared_with_email": user_b.email, "permission": "view"})
    assert resp.status_code == 201
    share_id = resp.json()["id"]

    # User B can now read
    resp = await client.get(f"/api/files/{file_id}", headers=hb)
    assert resp.status_code == 200

    # User A upgrades to edit
    resp = await client.put(f"/api/shares/{share_id}", headers=ha, json={"permission": "edit"})
    assert resp.status_code == 200

    # User A revokes
    resp = await client.delete(f"/api/shares/{share_id}", headers=ha)
    assert resp.status_code == 204

    # User B can no longer access
    resp = await client.get(f"/api/files/{file_id}", headers=hb)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_share_link_flow(client, user_a, mock_storage):
    ha = auth_headers(user_a.id, user_a.email, user_a.role)

    with patch("app.api.files.generate_thumbnail"):
        resp = await client.post("/api/files/upload", headers=ha,
            files={"file": ("link_doc.txt", b"data", "text/plain")})
    file_id = resp.json()["id"]

    # Create link
    resp = await client.post("/api/shares", headers=ha, json={
        "file_id": file_id, "create_link": True})
    token = resp.json()["share_token"]

    # Access link (no auth)
    resp = await client.get(f"/api/shares/link/{token}")
    assert resp.status_code == 200

    # Password-protected link
    resp = await client.post("/api/shares", headers=ha, json={
        "file_id": file_id, "create_link": True, "password": "secret"})
    pw_token = resp.json()["share_token"]

    resp = await client.get(f"/api/shares/link/{pw_token}?password=wrong")
    assert resp.status_code == 403
    resp = await client.get(f"/api/shares/link/{pw_token}?password=secret")
    assert resp.status_code == 200

    # Expired link
    expired = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    resp = await client.post("/api/shares", headers=ha, json={
        "file_id": file_id, "create_link": True, "expires_at": expired})
    exp_token = resp.json()["share_token"]
    resp = await client.get(f"/api/shares/link/{exp_token}")
    assert resp.status_code == 410
