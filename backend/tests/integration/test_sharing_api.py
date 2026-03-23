import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.file import File
from app.models.user import User
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal, auth_headers


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def owner():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="share_owner@example.com", name="Owner",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def target():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="share_target@example.com", name="Target",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def test_file(owner):
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="shareable.txt", owner_id=owner.id, is_folder=False, size=100, storage_key="k")
        session.add(f)
        await session.commit()
        await session.refresh(f)
        return f


@pytest.mark.asyncio
async def test_share_with_user(client, owner, target, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    resp = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "shared_with_email": target.email, "permission": "view"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_share_link(client, owner, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    resp = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "create_link": True})
    assert resp.status_code == 201
    assert resp.json()["share_token"] is not None


@pytest.mark.asyncio
async def test_share_password_protected(client, owner, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    resp = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "create_link": True, "password": "secret"})
    assert resp.status_code == 201
    assert resp.json()["has_password"] is True


@pytest.mark.asyncio
async def test_share_with_expiry(client, owner, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "create_link": True, "expires_at": expires})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_shares(client, owner, target, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "shared_with_email": target.email})
    resp = await client.get(f"/api/shares/file/{test_file.id}", headers=h)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_update_permission(client, owner, target, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    r = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "shared_with_email": target.email, "permission": "view"})
    sid = r.json()["id"]
    resp = await client.put(f"/api/shares/{sid}", headers=h, json={"permission": "edit"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_revoke_share(client, owner, target, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    r = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "shared_with_email": target.email})
    sid = r.json()["id"]
    resp = await client.delete(f"/api/shares/{sid}", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_shared_with_me(client, owner, target, test_file):
    oh = auth_headers(owner.id, owner.email, owner.role)
    th = auth_headers(target.id, target.email, target.role)
    await client.post("/api/shares", headers=oh, json={
        "file_id": str(test_file.id), "shared_with_email": target.email})
    resp = await client.get("/api/shares/shared-with-me", headers=th)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_access_share_link(client, owner, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    r = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "create_link": True})
    token = r.json()["share_token"]
    resp = await client.get(f"/api/shares/link/{token}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_expired_link(client, owner, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    expired = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    r = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "create_link": True, "expires_at": expired})
    token = r.json()["share_token"]
    resp = await client.get(f"/api/shares/link/{token}")
    assert resp.status_code == 410


@pytest.mark.asyncio
async def test_wrong_password_link(client, owner, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    r = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "create_link": True, "password": "correct"})
    token = r.json()["share_token"]
    resp = await client.get(f"/api/shares/link/{token}?password=wrong")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_correct_password_link(client, owner, test_file):
    h = auth_headers(owner.id, owner.email, owner.role)
    r = await client.post("/api/shares", headers=h, json={
        "file_id": str(test_file.id), "create_link": True, "password": "correct"})
    token = r.json()["share_token"]
    resp = await client.get(f"/api/shares/link/{token}?password=correct")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_shared_user_can_read(client, owner, target, test_file):
    oh = auth_headers(owner.id, owner.email, owner.role)
    th = auth_headers(target.id, target.email, target.role)
    await client.post("/api/shares", headers=oh, json={
        "file_id": str(test_file.id), "shared_with_email": target.email, "permission": "view"})
    resp = await client.get(f"/api/files/{test_file.id}", headers=th)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_non_shared_cannot_access(client, target, test_file):
    th = auth_headers(target.id, target.email, target.role)
    resp = await client.get(f"/api/files/{test_file.id}", headers=th)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_share_not_owned(client, target, test_file):
    th = auth_headers(target.id, target.email, target.role)
    resp = await client.post("/api/shares", headers=th, json={
        "file_id": str(test_file.id), "create_link": True})
    assert resp.status_code == 403
