import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from app.models.file import File
from app.models.user import User
from app.services.trash_service import TrashService
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def user(db_session):
    u = User(id=uuid.uuid4(), email="trash@example.com", name="Trash User",
             password_hash=hash_password("pass"), role="user", storage_used=1024, storage_quota=5368709120)
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.fixture
def mock_storage():
    s = MagicMock()
    s.delete_file.return_value = None
    return s


@pytest.mark.asyncio
async def test_trash_file(db_session, user, mock_storage):
    f = File(id=uuid.uuid4(), name="trash_me.txt", owner_id=user.id, is_folder=False, size=512, storage_key="key")
    db_session.add(f)
    await db_session.commit()
    svc = TrashService(db_session, mock_storage)
    trashed = await svc.trash_file(f.id, user.id)
    assert trashed.is_trashed is True
    assert trashed.trashed_at is not None


@pytest.mark.asyncio
async def test_trash_folder_recursive(db_session, user, mock_storage):
    folder = File(id=uuid.uuid4(), name="folder", owner_id=user.id, is_folder=True, size=0)
    db_session.add(folder)
    child = File(id=uuid.uuid4(), name="child.txt", owner_id=user.id, is_folder=False, size=100,
                 parent_folder_id=folder.id, storage_key="child/key")
    db_session.add(child)
    await db_session.commit()

    svc = TrashService(db_session, mock_storage)
    await svc.trash_file(folder.id, user.id)
    await db_session.refresh(child)
    assert child.is_trashed is True


@pytest.mark.asyncio
async def test_restore_file(db_session, user, mock_storage):
    f = File(id=uuid.uuid4(), name="restore.txt", owner_id=user.id, is_folder=False, size=100,
             storage_key="key", is_trashed=True, trashed_at=datetime.now(timezone.utc))
    db_session.add(f)
    await db_session.commit()
    svc = TrashService(db_session, mock_storage)
    restored = await svc.restore_file(f.id, user.id)
    assert restored.is_trashed is False


@pytest.mark.asyncio
async def test_restore_when_parent_deleted(db_session, user, mock_storage):
    folder = File(id=uuid.uuid4(), name="deleted_folder", owner_id=user.id, is_folder=True,
                  size=0, is_trashed=True, trashed_at=datetime.now(timezone.utc))
    db_session.add(folder)
    f = File(id=uuid.uuid4(), name="orphan.txt", owner_id=user.id, is_folder=False, size=100,
             storage_key="key", parent_folder_id=folder.id, is_trashed=True, trashed_at=datetime.now(timezone.utc))
    db_session.add(f)
    await db_session.commit()
    svc = TrashService(db_session, mock_storage)
    restored = await svc.restore_file(f.id, user.id)
    assert restored.parent_folder_id is None  # Moved to root


@pytest.mark.asyncio
async def test_permanent_delete(db_session, user, mock_storage):
    f = File(id=uuid.uuid4(), name="perm.txt", owner_id=user.id, is_folder=False, size=512,
             storage_key="key", is_trashed=True, trashed_at=datetime.now(timezone.utc))
    db_session.add(f)
    await db_session.commit()
    svc = TrashService(db_session, mock_storage)
    freed = await svc.permanent_delete(f.id, user.id)
    assert freed == 512


@pytest.mark.asyncio
async def test_empty_trash(db_session, user, mock_storage):
    for i in range(3):
        f = File(id=uuid.uuid4(), name=f"trash_{i}.txt", owner_id=user.id, is_folder=False, size=100,
                 storage_key=f"key_{i}", is_trashed=True, trashed_at=datetime.now(timezone.utc))
        db_session.add(f)
    await db_session.commit()
    svc = TrashService(db_session, mock_storage)
    freed = await svc.empty_trash(user.id)
    assert freed == 300


@pytest.mark.asyncio
async def test_auto_purge_old(db_session, user, mock_storage):
    old_date = datetime.now(timezone.utc) - timedelta(days=31)
    f = File(id=uuid.uuid4(), name="old.txt", owner_id=user.id, is_folder=False, size=200,
             storage_key="old/key", is_trashed=True, trashed_at=old_date)
    db_session.add(f)
    await db_session.commit()
    svc = TrashService(db_session, mock_storage)
    freed = await svc.auto_purge_old_trash(days=30)
    assert freed == 200


@pytest.mark.asyncio
async def test_trashed_excluded_from_listing(db_session, user, mock_storage):
    f = File(id=uuid.uuid4(), name="hidden.txt", owner_id=user.id, is_folder=False, size=100,
             storage_key="key", is_trashed=True, trashed_at=datetime.now(timezone.utc))
    db_session.add(f)
    f2 = File(id=uuid.uuid4(), name="visible.txt", owner_id=user.id, is_folder=False, size=100, storage_key="key2")
    db_session.add(f2)
    await db_session.commit()

    from app.services.file_service import FileService
    fsvc = FileService(db_session, mock_storage)
    files, total = await fsvc.list_files(user.id)
    assert total == 1
    assert files[0].name == "visible.txt"
