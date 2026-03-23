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
        u = User(id=uuid.uuid4(), email="e2e_version@example.com", name="Version E2E",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.fixture
def mock_storage():
    with patch("app.services.storage_service.get_minio_client") as m:
        mc = MagicMock()
        mc.presigned_get_object.return_value = "https://minio.local/v"
        mc.remove_object.return_value = None
        m.return_value = mc
        yield


@pytest.mark.asyncio
async def test_version_lifecycle(client, user, mock_storage):
    h = auth_headers(user.id, user.email, user.role)

    # Create a file with 3 versions
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="versioned.txt", owner_id=user.id, is_folder=False,
                 size=100, storage_key="current/key", content_hash="v3_hash")
        session.add(f)
        for i in range(1, 4):
            v = FileVersion(id=uuid.uuid4(), file_id=f.id, version_number=i,
                            storage_key=f"v{i}/key", size=100*i, content_hash=f"v{i}_hash", created_by=user.id)
            session.add(v)
        await session.commit()
        file_id = str(f.id)

    # List versions (should be 3)
    resp = await client.get(f"/api/files/{file_id}/versions", headers=h)
    assert resp.status_code == 200
    assert len(resp.json()) == 3

    # Restore v1
    resp = await client.post(f"/api/files/{file_id}/versions/1/restore", headers=h)
    assert resp.status_code == 200

    # Download v2
    resp = await client.get(f"/api/files/{file_id}/versions/2/download", headers=h, follow_redirects=False)
    assert resp.status_code == 302

    # Delete v2
    resp = await client.delete(f"/api/files/{file_id}/versions/2", headers=h)
    assert resp.status_code == 204

    # Verify remaining versions
    resp = await client.get(f"/api/files/{file_id}/versions", headers=h)
    versions = resp.json()
    version_numbers = [v["version_number"] for v in versions]
    assert 2 not in version_numbers
