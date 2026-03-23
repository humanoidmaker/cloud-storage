import uuid
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from app.models.file import File
from app.models.user import User
from app.services.file_service import FileService
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def user(db_session):
    u = User(
        id=uuid.uuid4(),
        email="filetest@example.com",
        name="File Test User",
        password_hash=hash_password("pass123"),
        role="user",
        storage_used=0,
        storage_quota=5368709120,
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.fixture
def mock_storage():
    s = MagicMock()
    s.upload_file.return_value = "test/key"
    s.copy_object.return_value = "test/copy/key"
    s.get_presigned_download_url.return_value = "https://minio.local/file"
    s.delete_file.return_value = None
    return s


@pytest.mark.asyncio
async def test_create_file(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    f = await svc.create_file(user.id, "test.txt", b"hello world")
    assert f.name == "test.txt"
    assert f.size == 11
    assert f.owner_id == user.id


@pytest.mark.asyncio
async def test_get_file(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    f = await svc.create_file(user.id, "test.txt", b"hello")
    retrieved = await svc.get_file(f.id)
    assert retrieved.id == f.id


@pytest.mark.asyncio
async def test_get_file_not_found(db_session, mock_storage):
    svc = FileService(db_session, mock_storage)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.get_file(uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_file_name(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    f = await svc.create_file(user.id, "old.txt", b"content")
    updated = await svc.update_file(f.id, user.id, name="new.txt")
    assert updated.name == "new.txt"


@pytest.mark.asyncio
async def test_update_file_duplicate_name(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    await svc.create_file(user.id, "existing.txt", b"a")
    f2 = await svc.create_file(user.id, "other.txt", b"b")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.update_file(f2.id, user.id, name="existing.txt")
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_move_file(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    from app.services.folder_service import FolderService
    folder_svc = FolderService(db_session)
    folder = await folder_svc.create_folder(user.id, "target")
    f = await svc.create_file(user.id, "test.txt", b"content")
    moved = await svc.move_file(f.id, user.id, folder.id)
    assert moved.parent_folder_id == folder.id


@pytest.mark.asyncio
async def test_move_folder_into_self(db_session, user, mock_storage):
    from app.services.folder_service import FolderService
    folder_svc = FolderService(db_session)
    folder = await folder_svc.create_folder(user.id, "folder1")
    svc = FileService(db_session, mock_storage)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.move_file(folder.id, user.id, folder.id)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_copy_file(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    f = await svc.create_file(user.id, "orig.txt", b"content")
    copy = await svc.copy_file(f.id, user.id)
    assert copy.id != f.id
    assert copy.name == "orig.txt"


@pytest.mark.asyncio
async def test_soft_delete(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    f = await svc.create_file(user.id, "delete.txt", b"content")
    deleted = await svc.soft_delete(f.id, user.id)
    assert deleted.is_trashed is True
    assert deleted.trashed_at is not None


@pytest.mark.asyncio
async def test_list_files(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    await svc.create_file(user.id, "a.txt", b"a")
    await svc.create_file(user.id, "b.txt", b"b")
    files, total = await svc.list_files(user.id)
    assert total == 2


@pytest.mark.asyncio
async def test_list_files_sorted(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    await svc.create_file(user.id, "b.txt", b"bb")
    await svc.create_file(user.id, "a.txt", b"a")
    files, _ = await svc.list_files(user.id, sort_by="name", sort_order="asc")
    assert files[0].name == "a.txt"


@pytest.mark.asyncio
async def test_upload_exceeds_quota(db_session, mock_storage):
    u = User(
        id=uuid.uuid4(),
        email="quota@example.com",
        name="Quota User",
        password_hash=hash_password("pass"),
        role="user",
        storage_used=5368709100,
        storage_quota=5368709120,
    )
    db_session.add(u)
    await db_session.commit()
    svc = FileService(db_session, mock_storage)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.create_file(u.id, "big.txt", b"x" * 100)
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_content_hash_dedup(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    f1 = await svc.create_file(user.id, "test.txt", b"same content")
    existing = await svc.check_deduplication(f1.content_hash, user.id)
    assert existing is not None


@pytest.mark.asyncio
async def test_bulk_delete(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    f1 = await svc.create_file(user.id, "a.txt", b"a")
    f2 = await svc.create_file(user.id, "b.txt", b"b")
    count = await svc.bulk_delete([f1.id, f2.id], user.id)
    assert count == 2


@pytest.mark.asyncio
async def test_get_file_permission_denied(db_session, user, mock_storage):
    svc = FileService(db_session, mock_storage)
    f = await svc.create_file(user.id, "test.txt", b"data")
    other_user_id = uuid.uuid4()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.update_file(f.id, other_user_id, name="hacked.txt")
    assert exc.value.status_code == 403
