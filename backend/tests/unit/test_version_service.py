import uuid
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from app.models.file import File
from app.models.file_version import FileVersion
from app.models.user import User
from app.services.version_service import VersionService
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def user(db_session):
    u = User(id=uuid.uuid4(), email="version@example.com", name="V User",
             password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120)
    db_session.add(u)
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def test_file(db_session, user):
    f = File(id=uuid.uuid4(), name="versioned.txt", owner_id=user.id, is_folder=False,
             size=100, storage_key="test/versioned", content_hash="abc123")
    db_session.add(f)
    await db_session.commit()
    return f


@pytest.fixture
def mock_storage():
    s = MagicMock()
    s.delete_file.return_value = None
    s.get_presigned_download_url.return_value = "https://minio.local/version"
    return s


@pytest.mark.asyncio
async def test_create_version(db_session, test_file, user, mock_storage):
    svc = VersionService(db_session, mock_storage)
    v = await svc.create_version(test_file.id, "v1/key", 100, "hash1", user.id)
    assert v.version_number == 1


@pytest.mark.asyncio
async def test_list_versions(db_session, test_file, user, mock_storage):
    svc = VersionService(db_session, mock_storage)
    await svc.create_version(test_file.id, "v1/key", 100, "h1", user.id)
    await svc.create_version(test_file.id, "v2/key", 200, "h2", user.id)
    versions = await svc.list_versions(test_file.id)
    assert len(versions) == 2
    assert versions[0].version_number > versions[1].version_number


@pytest.mark.asyncio
async def test_download_version(db_session, test_file, user, mock_storage):
    svc = VersionService(db_session, mock_storage)
    await svc.create_version(test_file.id, "v1/key", 100, "h1", user.id)
    url = await svc.get_version_download_url(test_file.id, 1)
    assert "minio" in url


@pytest.mark.asyncio
async def test_restore_version(db_session, test_file, user, mock_storage):
    svc = VersionService(db_session, mock_storage)
    await svc.create_version(test_file.id, "v1/key", 50, "old_hash", user.id)
    restored = await svc.restore_version(test_file.id, 1, user.id)
    assert restored.storage_key == "v1/key"


@pytest.mark.asyncio
async def test_delete_version(db_session, test_file, user, mock_storage):
    svc = VersionService(db_session, mock_storage)
    await svc.create_version(test_file.id, "v1/key", 100, "h1", user.id)
    await svc.delete_version(test_file.id, 1, user.id)
    versions = await svc.list_versions(test_file.id)
    assert len(versions) == 0


@pytest.mark.asyncio
async def test_auto_cleanup_beyond_limit(db_session, test_file, user, mock_storage):
    from unittest.mock import patch
    svc = VersionService(db_session, mock_storage)
    with patch("app.services.version_service.settings") as mock_settings:
        mock_settings.MAX_FILE_VERSIONS = 2
        for i in range(5):
            await svc.create_version(test_file.id, f"v{i}/key", 100, f"h{i}", user.id)
        versions = await svc.list_versions(test_file.id)
        assert len(versions) <= 2


@pytest.mark.asyncio
async def test_version_not_found(db_session, test_file, mock_storage):
    svc = VersionService(db_session, mock_storage)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.get_version(test_file.id, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_version_numbering_continues(db_session, test_file, user, mock_storage):
    svc = VersionService(db_session, mock_storage)
    await svc.create_version(test_file.id, "v1/key", 100, "h1", user.id)
    await svc.create_version(test_file.id, "v2/key", 100, "h2", user.id)
    await svc.delete_version(test_file.id, 1, user.id)
    v3 = await svc.create_version(test_file.id, "v3/key", 100, "h3", user.id)
    assert v3.version_number == 3  # Continues from max, doesn't reuse
