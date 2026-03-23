import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FolderCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parent_folder_id: uuid.UUID | None = None


class FolderResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    parent_folder_id: uuid.UUID | None = None
    is_folder: bool = True
    is_trashed: bool
    created_at: datetime
    updated_at: datetime
    file_count: int = 0
    folder_count: int = 0
    total_size: int = 0

    model_config = {"from_attributes": True}


class BreadcrumbItem(BaseModel):
    id: uuid.UUID | None = None  # None for root
    name: str


class FolderTreeNode(BaseModel):
    id: uuid.UUID
    name: str
    children: list["FolderTreeNode"] = []

    model_config = {"from_attributes": True}
