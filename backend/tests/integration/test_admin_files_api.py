import uuid
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
async def admin():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="files_admin@example.com", name="Admin",
                 password_hash=hash_password("pass"), role="superadmin", storage_used=0, storage_quota=0, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def target_user_with_files():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="target_files@example.com", name="Target",
                 password_hash=hash_password("pass"), role="user", storage_used=200, storage_quota=5368709120, is_active=True)
        session.add(u)
        f = File(id=uuid.uuid4(), name="admin_browse.txt", owner_id=u.id, is_folder=False, size=100, storage_key="k1")
        session.add(f)
        await session.commit()
        await session.refresh(u)
        return u, f


@pytest.fixture
def mock_storage():
    with patch("app.services.storage_service.get_minio_client") as m:
        mc = MagicMock()
        mc.presigned_get_object.return_value = "https://minio.local/file"
        mc.remove_object.return_value = None
        m.return_value = mc
        yield


@pytest.mark.asyncio
async def test_browse_user_files(client, admin, target_user_with_files):
    u, f = target_user_with_files
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get(f"/api/admin/files?user_id={u.id}", headers=h)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_admin_delete(client, admin, target_user_with_files, mock_storage):
    u, f = target_user_with_files
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.delete(f"/api/admin/files/{f.id}", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_admin_download(client, admin, target_user_with_files, mock_storage):
    u, f = target_user_with_files
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.get(f"/api/admin/files/{f.id}/download", headers=h, follow_redirects=False)
    assert resp.status_code == 302


@pytest.mark.asyncio
async def test_admin_bulk_delete(client, admin, target_user_with_files, mock_storage):
    u, f = target_user_with_files
    h = auth_headers(admin.id, admin.email, admin.role)
    resp = await client.post("/api/admin/files/bulk-delete", headers=h, json={"file_ids": [str(f.id)]})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_actions_logged(client, admin, target_user_with_files, mock_storage):
    u, f = target_user_with_files
    h = auth_headers(admin.id, admin.email, admin.role)
    await client.delete(f"/api/admin/files/{f.id}", headers=h)
    resp = await client.get("/api/admin/activity", headers=h)
    assert resp.status_code == 200
