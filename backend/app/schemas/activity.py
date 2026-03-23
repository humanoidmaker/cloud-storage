import uuid
from datetime import datetime

from pydantic import BaseModel


class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str | None = None
    user_email: str | None = None
    action: str
    file_id: uuid.UUID | None = None
    file_name: str | None = None
    details_json: str | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityFilterParams(BaseModel):
    user_id: uuid.UUID | None = None
    action: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    file_id: uuid.UUID | None = None
