import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    storage_used: int
    storage_quota: int
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class UserStorageBreakdown(BaseModel):
    images: int = 0
    documents: int = 0
    videos: int = 0
    audio: int = 0
    other: int = 0
    total: int = 0
