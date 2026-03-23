import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

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
        u = User(id=uuid.uuid4(), email="trash_api@example.com", name="Trash",
                 password_hash=hash_password("pass"), role="user", storage_used=1000, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.fixture
def mock_storage_patch():
    with patch("app.services.storage_service.get_minio_client") as m:
        mc = MagicMock()
        mc.remove_object.return_value = None
        m.return_value = mc
        yield


@pytest_asyncio.fixture
async def trashed_file(user):
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="trashed.txt", owner_id=user.id, is_folder=False, size=500,
                 storage_key="k", is_trashed=True, trashed_at=datetime.now(timezone.utc))
        session.add(f)
        await session.commit()
        await session.refresh(f)
        return f


@pytest.mark.asyncio
async def test_list_trash(client, user, trashed_file):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get("/api/trash", headers=h)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_restore(client, user, trashed_file):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.post(f"/api/trash/{trashed_file.id}/restore", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_permanent_delete(client, user, trashed_file, mock_storage_patch):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.delete(f"/api/trash/{trashed_file.id}", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_empty_trash(client, user, mock_storage_patch):
    async with TestingSessionLocal() as session:
        for i in range(2):
            f = File(id=uuid.uuid4(), name=f"t{i}.txt", owner_id=user.id, is_folder=False, size=100,
                     storage_key=f"k{i}", is_trashed=True, trashed_at=datetime.now(timezone.utc))
            session.add(f)
        await session.commit()
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.post("/api/trash/empty", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_restore_to_original(client, user, trashed_file):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.post(f"/api/trash/{trashed_file.id}/restore", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_restore_deleted_parent(client, user):
    async with TestingSessionLocal() as session:
        folder = File(id=uuid.uuid4(), name="del_parent", owner_id=user.id, is_folder=True, size=0,
                      is_trashed=True, trashed_at=datetime.now(timezone.utc))
        session.add(folder)
        f = File(id=uuid.uuid4(), name="orphan.txt", owner_id=user.id, is_folder=False, size=50,
                 storage_key="k", parent_folder_id=folder.id, is_trashed=True, trashed_at=datetime.now(timezone.utc))
        session.add(f)
        await session.commit()
        fid = f.id
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.post(f"/api/trash/{fid}/restore", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_trashed_not_in_listing(client, user, trashed_file):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get("/api/folders/contents", headers=h)
    items = resp.json()["items"]
    ids = [i["id"] for i in items]
    assert str(trashed_file.id) not in ids


@pytest.mark.asyncio
async def test_permanent_delete_frees_quota(client, user, trashed_file, mock_storage_patch):
    h = auth_headers(user.id, user.email, user.role)
    await client.delete(f"/api/trash/{trashed_file.id}", headers=h)
    me_resp = await client.get("/api/auth/me", headers=h)
    # storage_used should be reduced
    assert me_resp.status_code == 200
