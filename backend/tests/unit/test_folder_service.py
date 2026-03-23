import uuid

import pytest
import pytest_asyncio

from app.models.file import File
from app.models.user import User
from app.services.folder_service import FolderService
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def user(db_session):
    u = User(
        id=uuid.uuid4(), email="folder@example.com", name="Folder User",
        password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120,
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.mark.asyncio
async def test_create_folder(db_session, user):
    svc = FolderService(db_session)
    folder = await svc.create_folder(user.id, "My Folder")
    assert folder.name == "My Folder"
    assert folder.is_folder is True


@pytest.mark.asyncio
async def test_create_folder_duplicate(db_session, user):
    svc = FolderService(db_session)
    await svc.create_folder(user.id, "Dupe")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.create_folder(user.id, "Dupe")
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_list_folder_contents(db_session, user):
    svc = FolderService(db_session)
    await svc.create_folder(user.id, "Sub1")
    await svc.create_folder(user.id, "Sub2")
    items, total = await svc.get_folder_contents(user.id)
    assert total == 2


@pytest.mark.asyncio
async def test_rename_folder(db_session, user):
    svc = FolderService(db_session)
    folder = await svc.create_folder(user.id, "Old Name")
    renamed = await svc.rename_folder(folder.id, user.id, "New Name")
    assert renamed.name == "New Name"


@pytest.mark.asyncio
async def test_delete_folder_recursive(db_session, user):
    svc = FolderService(db_session)
    parent = await svc.create_folder(user.id, "Parent")
    child = await svc.create_folder(user.id, "Child", parent_folder_id=parent.id)
    await svc.delete_folder(parent.id, user.id)
    await db_session.refresh(parent)
    await db_session.refresh(child)
    assert parent.is_trashed is True
    assert child.is_trashed is True


@pytest.mark.asyncio
async def test_move_folder(db_session, user):
    svc = FolderService(db_session)
    f1 = await svc.create_folder(user.id, "Folder1")
    f2 = await svc.create_folder(user.id, "Folder2")
    moved = await svc.move_folder(f1.id, user.id, f2.id)
    assert moved.parent_folder_id == f2.id


@pytest.mark.asyncio
async def test_move_folder_into_child(db_session, user):
    svc = FolderService(db_session)
    parent = await svc.create_folder(user.id, "Parent")
    child = await svc.create_folder(user.id, "Child", parent_folder_id=parent.id)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.move_folder(parent.id, user.id, child.id)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_breadcrumb(db_session, user):
    svc = FolderService(db_session)
    p = await svc.create_folder(user.id, "Level1")
    c = await svc.create_folder(user.id, "Level2", parent_folder_id=p.id)
    crumbs = await svc.get_breadcrumb(c.id, user.id)
    assert len(crumbs) == 3  # Root + Level1 + Level2
    assert crumbs[0]["name"] == "Root"


@pytest.mark.asyncio
async def test_folder_tree(db_session, user):
    svc = FolderService(db_session)
    await svc.create_folder(user.id, "A")
    await svc.create_folder(user.id, "B")
    tree = await svc.get_folder_tree(user.id)
    assert len(tree) == 2


@pytest.mark.asyncio
async def test_folder_size(db_session, user):
    from app.services.file_service import FileService
    from unittest.mock import MagicMock
    svc = FolderService(db_session)
    folder = await svc.create_folder(user.id, "Sized")
    mock_s = MagicMock()
    mock_s.upload_file.return_value = "key"
    fsvc = FileService(db_session, mock_s)
    await fsvc.create_file(user.id, "a.txt", b"hello", parent_folder_id=folder.id)
    total_size = await svc.calculate_folder_size(folder.id)
    assert total_size == 5


@pytest.mark.asyncio
async def test_root_folder_handling(db_session, user):
    svc = FolderService(db_session)
    await svc.create_folder(user.id, "TopLevel")
    items, total = await svc.get_folder_contents(user.id, folder_id=None)
    assert total >= 1


@pytest.mark.asyncio
async def test_nested_depth(db_session, user):
    svc = FolderService(db_session)
    parent_id = None
    for i in range(5):
        f = await svc.create_folder(user.id, f"depth_{i}", parent_folder_id=parent_id)
        parent_id = f.id
    crumbs = await svc.get_breadcrumb(parent_id, user.id)
    assert len(crumbs) == 6  # Root + 5 levels
