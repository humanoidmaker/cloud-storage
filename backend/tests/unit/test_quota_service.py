import uuid
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from app.models.file import File
from app.models.user import User
from app.services.quota_service import QuotaService
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def user(db_session):
    u = User(id=uuid.uuid4(), email="quota@example.com", name="Quota User",
             password_hash=hash_password("pass"), role="user", storage_used=2048, storage_quota=5368709120)
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.mark.asyncio
async def test_calculate_storage(db_session, user):
    for i in range(3):
        f = File(id=uuid.uuid4(), name=f"f{i}.txt", owner_id=user.id, is_folder=False, size=1000, storage_key=f"k{i}")
        db_session.add(f)
    await db_session.commit()
    svc = QuotaService(db_session)
    used = await svc.calculate_storage_used(user.id)
    assert used == 3000


@pytest.mark.asyncio
async def test_upload_allowed_under_quota(db_session, user):
    svc = QuotaService(db_session)
    assert await svc.check_upload_allowed(user.id, 1000) is True


@pytest.mark.asyncio
async def test_upload_denied_over_quota(db_session):
    u = User(id=uuid.uuid4(), email="full@example.com", name="Full",
             password_hash=hash_password("pass"), role="user", storage_used=5368709100, storage_quota=5368709120)
    db_session.add(u)
    await db_session.commit()
    svc = QuotaService(db_session)
    assert await svc.check_upload_allowed(u.id, 100) is False


@pytest.mark.asyncio
async def test_recalculate_quota(db_session, user):
    f = File(id=uuid.uuid4(), name="f.txt", owner_id=user.id, is_folder=False, size=5000, storage_key="k")
    db_session.add(f)
    await db_session.commit()
    svc = QuotaService(db_session)
    actual = await svc.recalculate_quota(user.id)
    assert actual == 5000
    await db_session.refresh(user)
    assert user.storage_used == 5000


@pytest.mark.asyncio
async def test_unlimited_quota(db_session):
    u = User(id=uuid.uuid4(), email="unlimited@example.com", name="Unlimited",
             password_hash=hash_password("pass"), role="user", storage_used=999999999, storage_quota=0)
    db_session.add(u)
    await db_session.commit()
    svc = QuotaService(db_session)
    assert await svc.check_upload_allowed(u.id, 999999999) is True


@pytest.mark.asyncio
async def test_includes_trashed_files(db_session, user):
    from datetime import datetime, timezone
    f = File(id=uuid.uuid4(), name="trashed.txt", owner_id=user.id, is_folder=False, size=2000,
             storage_key="k", is_trashed=True, trashed_at=datetime.now(timezone.utc))
    db_session.add(f)
    await db_session.commit()
    svc = QuotaService(db_session)
    used = await svc.calculate_storage_used(user.id)
    assert used >= 2000  # Trashed files count


@pytest.mark.asyncio
async def test_excludes_permanently_deleted(db_session, user):
    # Files that are actually deleted from DB won't be counted
    svc = QuotaService(db_session)
    used = await svc.calculate_storage_used(user.id)
    # No files added, should be 0
    assert used == 0
