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
async def user():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="preview@example.com", name="Preview",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.fixture
def mock_storage():
    with patch("app.services.storage_service.get_minio_client") as m:
        mc = MagicMock()
        mc.presigned_get_object.return_value = "https://minio.local/thumb"
        m.return_value = mc
        yield


@pytest.mark.asyncio
async def test_thumbnail(client, user, mock_storage):
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="img.jpg", owner_id=user.id, is_folder=False, size=100,
                 storage_key="k", thumbnail_key="thumbnails/x.jpg", mime_type="image/jpeg")
        session.add(f)
        await session.commit()
        fid = f.id
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/files/{fid}/thumbnail", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_no_thumbnail(client, user, mock_storage):
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="doc.txt", owner_id=user.id, is_folder=False, size=100,
                 storage_key="k", mime_type="text/plain")
        session.add(f)
        await session.commit()
        fid = f.id
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/files/{fid}/thumbnail", headers=h)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_preview(client, user, mock_storage):
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="view.pdf", owner_id=user.id, is_folder=False, size=100,
                 storage_key="k", mime_type="application/pdf")
        session.add(f)
        await session.commit()
        fid = f.id
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/files/{fid}/preview", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_preview_respects_permissions(client, user, mock_storage):
    async with TestingSessionLocal() as session:
        other = User(id=uuid.uuid4(), email="other_prev@example.com", name="Other",
                     password_hash=hash_password("p"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(other)
        f = File(id=uuid.uuid4(), name="priv.jpg", owner_id=other.id, is_folder=False, size=100,
                 storage_key="k", mime_type="image/jpeg")
        session.add(f)
        await session.commit()
        fid = f.id
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/files/{fid}/preview", headers=h)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_thumbnail_unsupported(client, user, mock_storage):
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="data.bin", owner_id=user.id, is_folder=False, size=100,
                 storage_key="k", mime_type="application/octet-stream")
        session.add(f)
        await session.commit()
        fid = f.id
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/files/{fid}/thumbnail", headers=h)
    assert resp.status_code == 404
