import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from app.models.file import File
from app.models.user import User
from app.services.share_service import ShareService
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def owner(db_session):
    u = User(
        id=uuid.uuid4(), email="owner@example.com", name="Owner",
        password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120,
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def target_user(db_session):
    u = User(
        id=uuid.uuid4(), email="target@example.com", name="Target",
        password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120,
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def test_file(db_session, owner):
    f = File(id=uuid.uuid4(), name="share.txt", owner_id=owner.id, is_folder=False, size=100, storage_key="test/key")
    db_session.add(f)
    await db_session.commit()
    return f


@pytest.mark.asyncio
async def test_create_share_with_user(db_session, owner, target_user, test_file):
    svc = ShareService(db_session)
    share = await svc.create_share(test_file.id, owner.id, shared_with_email=target_user.email, permission="view")
    assert share.shared_with_user_id == target_user.id
    assert share.permission == "view"


@pytest.mark.asyncio
async def test_create_share_link(db_session, owner, test_file):
    svc = ShareService(db_session)
    share = await svc.create_share(test_file.id, owner.id, create_link=True)
    assert share.share_token is not None


@pytest.mark.asyncio
async def test_create_password_protected_share(db_session, owner, test_file):
    svc = ShareService(db_session)
    share = await svc.create_share(test_file.id, owner.id, create_link=True, password="secret")
    assert share.password_hash is not None


@pytest.mark.asyncio
async def test_create_expiring_share(db_session, owner, test_file):
    svc = ShareService(db_session)
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    share = await svc.create_share(test_file.id, owner.id, create_link=True, expires_at=expires)
    assert share.expires_at is not None


@pytest.mark.asyncio
async def test_validate_share_token(db_session, owner, test_file):
    svc = ShareService(db_session)
    share = await svc.create_share(test_file.id, owner.id, create_link=True)
    validated = await svc.validate_share_token(share.share_token)
    assert validated.id == share.id


@pytest.mark.asyncio
async def test_validate_expired_token(db_session, owner, test_file):
    svc = ShareService(db_session)
    expired = datetime.now(timezone.utc) - timedelta(hours=1)
    share = await svc.create_share(test_file.id, owner.id, create_link=True, expires_at=expired)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.validate_share_token(share.share_token)
    assert exc.value.status_code == 410


@pytest.mark.asyncio
async def test_validate_password_correct(db_session, owner, test_file):
    svc = ShareService(db_session)
    share = await svc.create_share(test_file.id, owner.id, create_link=True, password="secret")
    validated = await svc.validate_share_token(share.share_token, password="secret")
    assert validated.id == share.id


@pytest.mark.asyncio
async def test_validate_password_wrong(db_session, owner, test_file):
    svc = ShareService(db_session)
    share = await svc.create_share(test_file.id, owner.id, create_link=True, password="secret")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.validate_share_token(share.share_token, password="wrong")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_list_shares(db_session, owner, target_user, test_file):
    svc = ShareService(db_session)
    await svc.create_share(test_file.id, owner.id, shared_with_email=target_user.email)
    shares = await svc.list_shares_for_file(test_file.id, owner.id)
    assert len(shares) >= 1


@pytest.mark.asyncio
async def test_update_permission(db_session, owner, target_user, test_file):
    svc = ShareService(db_session)
    share = await svc.create_share(test_file.id, owner.id, shared_with_email=target_user.email, permission="view")
    updated = await svc.update_share_permission(share.id, owner.id, "edit")
    assert updated.permission == "edit"


@pytest.mark.asyncio
async def test_revoke_share(db_session, owner, target_user, test_file):
    svc = ShareService(db_session)
    share = await svc.create_share(test_file.id, owner.id, shared_with_email=target_user.email)
    await svc.revoke_share(share.id, owner.id)
    shares = await svc.list_shares_for_file(test_file.id, owner.id)
    assert len(shares) == 0


@pytest.mark.asyncio
async def test_cannot_share_not_owned(db_session, target_user, test_file):
    svc = ShareService(db_session)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.create_share(test_file.id, target_user.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_share_nonexistent_user(db_session, owner, test_file):
    svc = ShareService(db_session)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.create_share(test_file.id, owner.id, shared_with_email="nobody@example.com")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_share_updates(db_session, owner, target_user, test_file):
    svc = ShareService(db_session)
    s1 = await svc.create_share(test_file.id, owner.id, shared_with_email=target_user.email, permission="view")
    s2 = await svc.create_share(test_file.id, owner.id, shared_with_email=target_user.email, permission="edit")
    assert s2.id == s1.id
    assert s2.permission == "edit"
