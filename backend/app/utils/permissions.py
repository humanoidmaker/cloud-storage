import uuid
from datetime import datetime, timezone
from typing import Any


def is_owner(file_owner_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Check if the user is the owner of the file."""
    return file_owner_id == user_id


def is_superadmin(role: str) -> bool:
    """Check if user has superadmin role."""
    return role == "superadmin"


def is_admin_or_superadmin(role: str) -> bool:
    """Check if user has admin or superadmin role."""
    return role in ("admin", "superadmin")


def can_read(
    file_owner_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
    shares: list[dict[str, Any]] | None = None,
) -> bool:
    """Check if user can read a file.
    Owner, superadmin, or users with any share permission can read.
    """
    if is_owner(file_owner_id, user_id):
        return True
    if is_superadmin(user_role):
        return True
    if shares:
        for share in shares:
            if _is_valid_share(share, user_id):
                return True
    return False


def can_write(
    file_owner_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
    shares: list[dict[str, Any]] | None = None,
) -> bool:
    """Check if user can write (edit/rename/upload to folder).
    Owner, superadmin, or users with edit/admin share permission can write.
    """
    if is_owner(file_owner_id, user_id):
        return True
    if is_superadmin(user_role):
        return True
    if shares:
        for share in shares:
            if _is_valid_share(share, user_id) and share.get("permission") in ("edit", "admin"):
                return True
    return False


def can_admin(
    file_owner_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
    shares: list[dict[str, Any]] | None = None,
) -> bool:
    """Check if user can perform admin actions (reshare, delete).
    Owner, superadmin, or users with admin share permission.
    """
    if is_owner(file_owner_id, user_id):
        return True
    if is_superadmin(user_role):
        return True
    if shares:
        for share in shares:
            if _is_valid_share(share, user_id) and share.get("permission") == "admin":
                return True
    return False


def is_owner_or_shared(
    file_owner_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
    shares: list[dict[str, Any]] | None = None,
) -> bool:
    """Check if user is the owner or has any valid share access."""
    return can_read(file_owner_id, user_id, user_role, shares)


def _is_valid_share(share: dict[str, Any], user_id: uuid.UUID) -> bool:
    """Check if a share entry is valid for the given user.
    A share is valid if:
    - shared_with_user_id matches user_id
    - share is not expired
    """
    shared_with = share.get("shared_with_user_id")
    if shared_with is None:
        return False
    if uuid.UUID(str(shared_with)) != user_id:
        return False
    expires_at = share.get("expires_at")
    if expires_at is not None:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return False
    return True
