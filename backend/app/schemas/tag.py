import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TagCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class TagUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseModel):
    id: uuid.UUID
    name: str
    color: str
    user_id: uuid.UUID
    created_at: datetime
    file_count: int = 0

    model_config = {"from_attributes": True}
