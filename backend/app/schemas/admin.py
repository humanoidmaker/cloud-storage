import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminDashboardResponse(BaseModel):
    total_users: int
    active_users: int
    total_storage_used: int
    total_files: int
    total_shares: int
    recent_activity: list[dict]
    user_growth: list[dict]
    storage_trend: list[dict]


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str = "user"
    storage_quota: int = 5368709120  # 5GB


class AdminUserUpdateRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    role: str | None = None


class AdminQuotaUpdateRequest(BaseModel):
    storage_quota: int = Field(ge=0)  # 0 = unlimited


class AdminBulkQuotaRequest(BaseModel):
    user_ids: list[uuid.UUID]
    storage_quota: int = Field(ge=0)


class StorageBreakdownItem(BaseModel):
    user_id: uuid.UUID
    user_name: str
    user_email: str
    files_count: int
    folders_count: int
    storage_used: int
    storage_quota: int
    utilization_percent: float


class SystemHealthResponse(BaseModel):
    minio: dict
    postgres: dict
    redis: dict
    celery: dict
    api: dict


class AdminSettingsResponse(BaseModel):
    default_quota_bytes: int
    max_upload_size_bytes: int
    allowed_extensions: str
    registration_enabled: bool
    trash_auto_purge_days: int
    max_file_versions: int


class AdminSettingsUpdateRequest(BaseModel):
    default_quota_bytes: int | None = Field(default=None, ge=0)
    max_upload_size_bytes: int | None = Field(default=None, ge=1048576)  # min 1MB
    allowed_extensions: str | None = None
    registration_enabled: bool | None = None
    trash_auto_purge_days: int | None = Field(default=None, ge=1, le=365)
    max_file_versions: int | None = Field(default=None, ge=1, le=100)
