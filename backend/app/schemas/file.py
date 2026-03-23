import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    id: uuid.UUID
    name: str
    mime_type: str | None = None
    size: int
    storage_key: str | None = None
    owner_id: uuid.UUID
    parent_folder_id: uuid.UUID | None = None
    is_folder: bool
    content_hash: str | None = None
    thumbnail_key: str | None = None
    is_trashed: bool
    trashed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    is_starred: bool = False
    share_count: int = 0
    version_count: int = 0
    tags: list[dict] = []

    model_config = {"from_attributes": True}


class FileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=500)


class FileMoveRequest(BaseModel):
    target_folder_id: uuid.UUID | None = None  # None = root


class FileCopyRequest(BaseModel):
    target_folder_id: uuid.UUID | None = None  # None = root
    new_name: str | None = None


class BulkOperationRequest(BaseModel):
    file_ids: list[uuid.UUID] = Field(min_length=1)


class BulkMoveRequest(BulkOperationRequest):
    target_folder_id: uuid.UUID | None = None


class FileUploadResponse(BaseModel):
    id: uuid.UUID
    name: str
    mime_type: str | None = None
    size: int
    storage_key: str
    owner_id: uuid.UUID
    parent_folder_id: uuid.UUID | None = None
    content_hash: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
