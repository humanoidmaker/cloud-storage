import uuid
from datetime import datetime, timedelta, timezone

from app.utils.permissions import can_admin, can_read, can_write, is_owner


def test_owner_can_read():
    uid = uuid.uuid4()
    assert can_read(uid, uid, "user") is True


def test_owner_can_write():
    uid = uuid.uuid4()
    assert can_write(uid, uid, "user") is True


def test_owner_can_delete():
    uid = uuid.uuid4()
    assert can_admin(uid, uid, "user") is True


def test_shared_user_view_can_read():
    owner = uuid.uuid4()
    user = uuid.uuid4()
    shares = [{"shared_with_user_id": str(user), "permission": "view", "expires_at": None}]
    assert can_read(owner, user, "user", shares) is True


def test_shared_user_view_cannot_write():
    owner = uuid.uuid4()
    user = uuid.uuid4()
    shares = [{"shared_with_user_id": str(user), "permission": "view", "expires_at": None}]
    assert can_write(owner, user, "user", shares) is False


def test_shared_user_edit_can_write():
    owner = uuid.uuid4()
    user = uuid.uuid4()
    shares = [{"shared_with_user_id": str(user), "permission": "edit", "expires_at": None}]
    assert can_write(owner, user, "user", shares) is True


def test_shared_user_edit_cannot_delete():
    owner = uuid.uuid4()
    user = uuid.uuid4()
    shares = [{"shared_with_user_id": str(user), "permission": "edit", "expires_at": None}]
    assert can_admin(owner, user, "user", shares) is False


def test_shared_user_admin_can_delete():
    owner = uuid.uuid4()
    user = uuid.uuid4()
    shares = [{"shared_with_user_id": str(user), "permission": "admin", "expires_at": None}]
    assert can_admin(owner, user, "user", shares) is True


def test_non_shared_cannot_read():
    owner = uuid.uuid4()
    user = uuid.uuid4()
    assert can_read(owner, user, "user") is False


def test_superadmin_can_access():
    owner = uuid.uuid4()
    admin = uuid.uuid4()
    assert can_read(owner, admin, "superadmin") is True
    assert can_write(owner, admin, "superadmin") is True
    assert can_admin(owner, admin, "superadmin") is True


def test_expired_share_denies():
    owner = uuid.uuid4()
    user = uuid.uuid4()
    expired = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    shares = [{"shared_with_user_id": str(user), "permission": "view", "expires_at": expired}]
    assert can_read(owner, user, "user", shares) is False


def test_deactivated_share_denies():
    owner = uuid.uuid4()
    user = uuid.uuid4()
    # Share with different user = no access
    other = uuid.uuid4()
    shares = [{"shared_with_user_id": str(other), "permission": "view", "expires_at": None}]
    assert can_read(owner, user, "user", shares) is False
