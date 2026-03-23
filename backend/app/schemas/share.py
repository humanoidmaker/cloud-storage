import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class ShareCreateRequest(BaseModel):
    file_id: uuid.UUID
    shared_with_email: EmailStr | None = None
    permission: str = "view"  # view, edit, admin
    create_link: bool = False
    password: str | None = None
    expires_at: datetime | None = None


class ShareResponse(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    shared_by: uuid.UUID
    shared_with_user_id: uuid.UUID | None = None
    shared_with_email: str | None = None
    share_token: str | None = None
    permission: str
    has_password: bool = False
    expires_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ShareUpdateRequest(BaseModel):
    permission: str | None = None  # view, edit, admin


class ShareLinkAccessRequest(BaseModel):
    password: str | None = None


class SharedFileResponse(BaseModel):
    file: dict
    permission: str
    shared_by_name: str
    shared_at: datetime
