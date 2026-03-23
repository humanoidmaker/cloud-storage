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
async def user():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="folders@example.com", name="Folders",
                 password_hash=hash_password("pass"), role="user",
                 storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.fixture
def headers(user):
    return auth_headers(user.id, user.email, user.role)


@pytest.mark.asyncio
async def test_create_folder(client, headers):
    resp = await client.post("/api/folders", headers=headers, json={"name": "New Folder"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_folder_duplicate(client, headers):
    await client.post("/api/folders", headers=headers, json={"name": "Dupe"})
    resp = await client.post("/api/folders", headers=headers, json={"name": "Dupe"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_folder_contents(client, headers):
    await client.post("/api/folders", headers=headers, json={"name": "Sub1"})
    resp = await client.get("/api/folders/contents", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_get_folder_contents_sorted(client, headers):
    await client.post("/api/folders", headers=headers, json={"name": "AAA"})
    await client.post("/api/folders", headers=headers, json={"name": "ZZZ"})
    resp = await client.get("/api/folders/contents?sort_by=name&sort_order=asc", headers=headers)
    items = resp.json()["items"]
    assert items[0]["name"] <= items[-1]["name"]


@pytest.mark.asyncio
async def test_get_breadcrumb(client, headers):
    r1 = await client.post("/api/folders", headers=headers, json={"name": "Level1"})
    fid = r1.json()["id"]
    r2 = await client.post("/api/folders", headers=headers, json={"name": "Level2", "parent_folder_id": fid})
    fid2 = r2.json()["id"]
    resp = await client.get(f"/api/folders/{fid2}/breadcrumb", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_rename_folder(client, headers):
    r = await client.post("/api/folders", headers=headers, json={"name": "OldName"})
    fid = r.json()["id"]
    resp = await client.put(f"/api/folders/{fid}", headers=headers, json={"name": "NewName"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_move_folder(client, headers):
    r1 = await client.post("/api/folders", headers=headers, json={"name": "Src"})
    r2 = await client.post("/api/folders", headers=headers, json={"name": "Dst"})
    resp = await client.post(f"/api/folders/{r1.json()['id']}/move", headers=headers,
        json={"target_folder_id": r2.json()["id"]})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_move_into_child(client, headers):
    r1 = await client.post("/api/folders", headers=headers, json={"name": "Parent"})
    r2 = await client.post("/api/folders", headers=headers,
        json={"name": "Child", "parent_folder_id": r1.json()["id"]})
    resp = await client.post(f"/api/folders/{r1.json()['id']}/move", headers=headers,
        json={"target_folder_id": r2.json()["id"]})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_folder(client, headers):
    r = await client.post("/api/folders", headers=headers, json={"name": "DelMe"})
    resp = await client.delete(f"/api/folders/{r.json()['id']}", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_folder_tree(client, headers):
    await client.post("/api/folders", headers=headers, json={"name": "TreeA"})
    await client.post("/api/folders", headers=headers, json={"name": "TreeB"})
    resp = await client.get("/api/folders/tree", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_root_contents(client, headers):
    resp = await client.get("/api/folders/contents", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_nested_creation(client, headers):
    r1 = await client.post("/api/folders", headers=headers, json={"name": "N1"})
    r2 = await client.post("/api/folders", headers=headers,
        json={"name": "N2", "parent_folder_id": r1.json()["id"]})
    r3 = await client.post("/api/folders", headers=headers,
        json={"name": "N3", "parent_folder_id": r2.json()["id"]})
    assert r3.status_code == 201
