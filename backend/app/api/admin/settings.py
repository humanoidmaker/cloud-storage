from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, require_admin
from app.schemas.admin import AdminSettingsResponse, AdminSettingsUpdateRequest
from app.config import settings as app_settings

router = APIRouter(prefix="/api/admin/settings", tags=["admin-settings"])

# In-memory settings store (in production, use a DB key-value table + Redis cache)
_settings_store: dict[str, str | int | bool] = {
    "default_quota_bytes": app_settings.DEFAULT_STORAGE_QUOTA_BYTES,
    "max_upload_size_bytes": app_settings.MAX_UPLOAD_SIZE_BYTES,
    "allowed_extensions": app_settings.ALLOWED_EXTENSIONS,
    "registration_enabled": app_settings.REGISTRATION_ENABLED,
    "trash_auto_purge_days": app_settings.TRASH_AUTO_PURGE_DAYS,
    "max_file_versions": app_settings.MAX_FILE_VERSIONS,
}


@router.get("")
async def get_settings(
    current_user: CurrentUser = Depends(require_admin),
):
    return {
        "default_quota_bytes": _settings_store.get("default_quota_bytes", app_settings.DEFAULT_STORAGE_QUOTA_BYTES),
        "max_upload_size_bytes": _settings_store.get("max_upload_size_bytes", app_settings.MAX_UPLOAD_SIZE_BYTES),
        "allowed_extensions": _settings_store.get("allowed_extensions", app_settings.ALLOWED_EXTENSIONS),
        "registration_enabled": _settings_store.get("registration_enabled", app_settings.REGISTRATION_ENABLED),
        "trash_auto_purge_days": _settings_store.get("trash_auto_purge_days", app_settings.TRASH_AUTO_PURGE_DAYS),
        "max_file_versions": _settings_store.get("max_file_versions", app_settings.MAX_FILE_VERSIONS),
    }


@router.put("")
async def update_settings(
    body: AdminSettingsUpdateRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    if body.default_quota_bytes is not None:
        _settings_store["default_quota_bytes"] = body.default_quota_bytes
        app_settings.DEFAULT_STORAGE_QUOTA_BYTES = body.default_quota_bytes

    if body.max_upload_size_bytes is not None:
        _settings_store["max_upload_size_bytes"] = body.max_upload_size_bytes
        app_settings.MAX_UPLOAD_SIZE_BYTES = body.max_upload_size_bytes

    if body.allowed_extensions is not None:
        _settings_store["allowed_extensions"] = body.allowed_extensions
        app_settings.ALLOWED_EXTENSIONS = body.allowed_extensions

    if body.registration_enabled is not None:
        _settings_store["registration_enabled"] = body.registration_enabled
        app_settings.REGISTRATION_ENABLED = body.registration_enabled

    if body.trash_auto_purge_days is not None:
        _settings_store["trash_auto_purge_days"] = body.trash_auto_purge_days
        app_settings.TRASH_AUTO_PURGE_DAYS = body.trash_auto_purge_days

    if body.max_file_versions is not None:
        _settings_store["max_file_versions"] = body.max_file_versions
        app_settings.MAX_FILE_VERSIONS = body.max_file_versions

    # Try to update Redis cache
    try:
        import json
        import redis
        r = redis.from_url(app_settings.REDIS_URL)
        r.set("cloud_storage:settings", json.dumps({k: str(v) for k, v in _settings_store.items()}), ex=3600)
    except Exception:
        pass  # Redis might not be available

    return {
        "message": "Settings updated",
        "settings": dict(_settings_store),
    }
