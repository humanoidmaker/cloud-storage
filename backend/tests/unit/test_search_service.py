import uuid
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from app.models.file import File
from app.models.user import User
from app.services.search_service import SearchService
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def user(db_session):
    u = User(
        id=uuid.uuid4(), email="search@example.com", name="Search User",
        password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120,
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def files(db_session, user):
    items = []
    for name, mime in [("report.pdf", "application/pdf"), ("photo.jpg", "image/jpeg"),
                       ("notes.txt", "text/plain"), ("budget.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")]:
        f = File(id=uuid.uuid4(), name=name, mime_type=mime, size=1024, owner_id=user.id,
                 is_folder=False, storage_key=f"{user.id}/{name}")
        db_session.add(f)
        items.append(f)
    await db_session.commit()
    return items


@pytest.mark.asyncio
async def test_search_by_filename(db_session, user, files):
    svc = SearchService(db_session)
    results, total = await svc.search_files(user.id, "report")
    assert total >= 1
    assert any("report" in f.name for f in results)


@pytest.mark.asyncio
async def test_search_case_insensitive(db_session, user, files):
    svc = SearchService(db_session)
    results, total = await svc.search_files(user.id, "REPORT")
    assert total >= 1


@pytest.mark.asyncio
async def test_search_with_type_filter(db_session, user, files):
    svc = SearchService(db_session)
    results, total = await svc.search_files(user.id, "photo", file_type="image")
    assert total >= 1
    assert all(f.mime_type.startswith("image/") for f in results)


@pytest.mark.asyncio
async def test_search_with_date_range(db_session, user, files):
    from datetime import datetime, timedelta, timezone
    svc = SearchService(db_session)
    results, total = await svc.search_files(
        user.id, "report",
        date_from=datetime.now(timezone.utc) - timedelta(days=1),
        date_to=datetime.now(timezone.utc) + timedelta(days=1),
    )
    assert total >= 1


@pytest.mark.asyncio
async def test_search_within_folder(db_session, user):
    from app.services.folder_service import FolderService
    fsvc = FolderService(db_session)
    folder = await fsvc.create_folder(user.id, "SearchFolder")
    f = File(id=uuid.uuid4(), name="inside_report.txt", mime_type="text/plain", size=100,
             owner_id=user.id, is_folder=False, parent_folder_id=folder.id, storage_key="test/key")
    db_session.add(f)
    await db_session.commit()

    svc = SearchService(db_session)
    results, total = await svc.search_files(user.id, "inside", folder_id=folder.id)
    assert total >= 1


@pytest.mark.asyncio
async def test_search_no_matches(db_session, user, files):
    svc = SearchService(db_session)
    results, total = await svc.search_files(user.id, "nonexistentxyz")
    assert total == 0


@pytest.mark.asyncio
async def test_search_special_characters(db_session, user, files):
    svc = SearchService(db_session)
    # Should not crash with SQL injection attempts
    results, total = await svc.search_files(user.id, "'; DROP TABLE files;--")
    assert total == 0


@pytest.mark.asyncio
async def test_search_with_tag_filter(db_session, user, files):
    from app.models.tag import Tag
    from app.models.file_tag import FileTag
    tag = Tag(id=uuid.uuid4(), name="important", user_id=user.id, color="#FF0000")
    db_session.add(tag)
    ft = FileTag(id=uuid.uuid4(), file_id=files[0].id, tag_id=tag.id)
    db_session.add(ft)
    await db_session.commit()

    svc = SearchService(db_session)
    results, total = await svc.search_files(user.id, "report", tag_id=tag.id)
    assert total >= 1
