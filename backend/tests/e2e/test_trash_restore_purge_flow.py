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
        u = User(id=uuid.uuid4(), email="e2e_trash@example.com", name="Trash E2E",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
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
async def test_trash_restore_purge(client, user, mock_storage):
    h = auth_headers(user.id, user.email, user.role)

    # Upload multiple files
    file_ids = []
    for name in ["trash1.txt", "trash2.txt", "trash3.txt"]:
        with patch("app.api.files.generate_thumbnail"):
            r = await client.post("/api/files/upload", headers=h,
                files={"file": (name, b"data", "text/plain")})
        file_ids.append(r.json()["id"])

    # Delete all
    for fid in file_ids:
        resp = await client.delete(f"/api/files/{fid}", headers=h)
        assert resp.status_code == 200

    # Verify in trash
    resp = await client.get("/api/trash", headers=h)
    assert resp.json()["total"] >= 3

    # Restore one
    resp = await client.post(f"/api/trash/{file_ids[0]}/restore", headers=h)
    assert resp.status_code == 200

    # Verify restored
    resp = await client.get(f"/api/files/{file_ids[0]}", headers=h)
    assert resp.status_code == 200

    # Permanently delete another
    resp = await client.delete(f"/api/trash/{file_ids[1]}", headers=h)
    assert resp.status_code == 204

    # Empty remaining trash
    resp = await client.post("/api/trash/empty", headers=h)
    assert resp.status_code == 200

    # Verify trash is empty
    resp = await client.get("/api/trash", headers=h)
    assert resp.json()["total"] == 0
