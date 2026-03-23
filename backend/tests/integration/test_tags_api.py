import uuid

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
async def user():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="tags@example.com", name="Tags",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def test_file(user):
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="tag.txt", owner_id=user.id, is_folder=False, size=100, storage_key="k")
        session.add(f)
        await session.commit()
        await session.refresh(f)
        return f


@pytest.mark.asyncio
async def test_create_tag(client, user):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.post("/api/tags", headers=h, json={"name": "Work", "color": "#FF0000"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_tags(client, user):
    h = auth_headers(user.id, user.email, user.role)
    await client.post("/api/tags", headers=h, json={"name": "T1"})
    resp = await client.get("/api/tags", headers=h)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_update_tag(client, user):
    h = auth_headers(user.id, user.email, user.role)
    r = await client.post("/api/tags", headers=h, json={"name": "Old"})
    tid = r.json()["id"]
    resp = await client.put(f"/api/tags/{tid}", headers=h, json={"name": "New", "color": "#00FF00"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_tag(client, user):
    h = auth_headers(user.id, user.email, user.role)
    r = await client.post("/api/tags", headers=h, json={"name": "DelTag"})
    tid = r.json()["id"]
    resp = await client.delete(f"/api/tags/{tid}", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_tag_file(client, user, test_file):
    h = auth_headers(user.id, user.email, user.role)
    r = await client.post("/api/tags", headers=h, json={"name": "Assign"})
    tid = r.json()["id"]
    resp = await client.post(f"/api/tags/files/{test_file.id}/tags/{tid}", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_untag_file(client, user, test_file):
    h = auth_headers(user.id, user.email, user.role)
    r = await client.post("/api/tags", headers=h, json={"name": "Remove"})
    tid = r.json()["id"]
    await client.post(f"/api/tags/files/{test_file.id}/tags/{tid}", headers=h)
    resp = await client.delete(f"/api/tags/files/{test_file.id}/tags/{tid}", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_files_by_tag(client, user, test_file):
    h = auth_headers(user.id, user.email, user.role)
    r = await client.post("/api/tags", headers=h, json={"name": "Filter"})
    tid = r.json()["id"]
    await client.post(f"/api/tags/files/{test_file.id}/tags/{tid}", headers=h)
    resp = await client.get(f"/api/tags/{tid}/files", headers=h)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_duplicate_tag_name(client, user):
    h = auth_headers(user.id, user.email, user.role)
    await client.post("/api/tags", headers=h, json={"name": "Unique"})
    resp = await client.post("/api/tags", headers=h, json={"name": "Unique"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_tag_other_user_file(client, user):
    async with TestingSessionLocal() as session:
        other = User(id=uuid.uuid4(), email="other_tag@example.com", name="Other",
                     password_hash=hash_password("p"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(other)
        f = File(id=uuid.uuid4(), name="priv.txt", owner_id=other.id, is_folder=False, size=10, storage_key="k")
        session.add(f)
        await session.commit()
        fid = f.id
    h = auth_headers(user.id, user.email, user.role)
    r = await client.post("/api/tags", headers=h, json={"name": "MyTag"})
    tid = r.json()["id"]
    resp = await client.post(f"/api/tags/files/{fid}/tags/{tid}", headers=h)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_tag_removes_from_files(client, user, test_file):
    h = auth_headers(user.id, user.email, user.role)
    r = await client.post("/api/tags", headers=h, json={"name": "Gone"})
    tid = r.json()["id"]
    await client.post(f"/api/tags/files/{test_file.id}/tags/{tid}", headers=h)
    await client.delete(f"/api/tags/{tid}", headers=h)
    # Tag no longer exists
    resp = await client.get(f"/api/tags/{tid}/files", headers=h)
    assert resp.status_code == 404
