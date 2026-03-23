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
        u = User(id=uuid.uuid4(), email="e2e_folder@example.com", name="Folder E2E",
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
async def test_nested_folder_operations(client, user, mock_storage):
    h = auth_headers(user.id, user.email, user.role)

    # Create 3 levels
    r1 = await client.post("/api/folders", headers=h, json={"name": "Level1"})
    assert r1.status_code == 201
    l1_id = r1.json()["id"]

    r2 = await client.post("/api/folders", headers=h, json={"name": "Level2", "parent_folder_id": l1_id})
    l2_id = r2.json()["id"]

    r3 = await client.post("/api/folders", headers=h, json={"name": "Level3", "parent_folder_id": l2_id})
    l3_id = r3.json()["id"]

    # Upload files at each level
    with patch("app.api.files.generate_thumbnail"):
        for folder_id in [l1_id, l2_id, l3_id]:
            await client.post("/api/files/upload", headers=h,
                files={"file": ("doc.txt", b"data", "text/plain")},
                data={"parent_folder_id": folder_id})

    # Verify contents at level 2
    resp = await client.get(f"/api/folders/{l2_id}/contents", headers=h)
    assert resp.status_code == 200

    # Move Level2 to root
    resp = await client.post(f"/api/folders/{l2_id}/move", headers=h, json={"target_folder_id": None})
    assert resp.status_code == 200

    # Delete Level1 (should be recursive)
    resp = await client.delete(f"/api/folders/{l1_id}", headers=h)
    assert resp.status_code == 200

    # Verify Level2 still accessible (was moved before delete)
    resp = await client.get(f"/api/folders/{l2_id}/contents", headers=h)
    assert resp.status_code == 200

    # Restore Level1
    resp = await client.post(f"/api/trash/{l1_id}/restore", headers=h)
    assert resp.status_code == 200
