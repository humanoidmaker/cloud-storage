import uuid
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.file import File
from app.models.file_version import FileVersion
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
        u = User(id=uuid.uuid4(), email="vers@example.com", name="Vers",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def file_with_versions(user):
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="v.txt", owner_id=user.id, is_folder=False, size=100, storage_key="current/key", content_hash="curr")
        session.add(f)
        for i in range(1, 4):
            v = FileVersion(id=uuid.uuid4(), file_id=f.id, version_number=i, storage_key=f"v{i}/key", size=100*i, content_hash=f"h{i}", created_by=user.id)
            session.add(v)
        await session.commit()
        await session.refresh(f)
        return f


@pytest.fixture
def mock_storage_patch():
    with patch("app.services.storage_service.get_minio_client") as m:
        mc = MagicMock()
        mc.presigned_get_object.return_value = "https://minio.local/version"
        mc.remove_object.return_value = None
        m.return_value = mc
        yield


@pytest.mark.asyncio
async def test_list_versions(client, user, file_with_versions):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/files/{file_with_versions.id}/versions", headers=h)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_download_version(client, user, file_with_versions, mock_storage_patch):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/files/{file_with_versions.id}/versions/1/download", headers=h, follow_redirects=False)
    assert resp.status_code == 302


@pytest.mark.asyncio
async def test_restore_version(client, user, file_with_versions, mock_storage_patch):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.post(f"/api/files/{file_with_versions.id}/versions/1/restore", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_version(client, user, file_with_versions, mock_storage_patch):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.delete(f"/api/files/{file_with_versions.id}/versions/1", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_version_not_found(client, user, file_with_versions, mock_storage_patch):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/files/{file_with_versions.id}/versions/99/download", headers=h, follow_redirects=False)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_version_numbering(client, user, file_with_versions):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/files/{file_with_versions.id}/versions", headers=h)
    versions = resp.json()
    numbers = [v["version_number"] for v in versions]
    assert sorted(numbers, reverse=True) == numbers


@pytest.mark.asyncio
async def test_restore_creates_new(client, user, file_with_versions, mock_storage_patch):
    h = auth_headers(user.id, user.email, user.role)
    await client.post(f"/api/files/{file_with_versions.id}/versions/1/restore", headers=h)
    resp = await client.get(f"/api/files/{file_with_versions.id}/versions", headers=h)
    assert len(resp.json()) >= 3


@pytest.mark.asyncio
async def test_versions_access_check(client, user, file_with_versions):
    async with TestingSessionLocal() as session:
        other = User(id=uuid.uuid4(), email="other_v@example.com", name="Other",
                     password_hash=hash_password("p"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(other)
        await session.commit()
        oh = auth_headers(other.id, other.email, other.role)
    resp = await client.get(f"/api/files/{file_with_versions.id}/versions", headers=oh)
    assert resp.status_code == 403
