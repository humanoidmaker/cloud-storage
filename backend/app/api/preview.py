import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user
from app.models.file import File
from app.services.share_service import ShareService
from app.services.storage_service import StorageService
from app.utils.permissions import can_read

router = APIRouter(prefix="/api/files", tags=["preview"])


@router.get("/{file_id}/thumbnail")
async def get_thumbnail(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file = await db.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    share_svc = ShareService(db)
    shares = await share_svc.get_user_shares_for_file(file_id, current_user.user_id)
    if not can_read(file.owner_id, current_user.user_id, current_user.role, shares):
        raise HTTPException(status_code=403, detail="Access denied")

    if not file.thumbnail_key:
        raise HTTPException(status_code=404, detail="No thumbnail available")

    try:
        storage = StorageService()
        url = storage.get_thumbnail_url(file.thumbnail_key)
        return {"thumbnail_url": url}
    except Exception:
        raise HTTPException(status_code=404, detail="Thumbnail not found")


@router.get("/{file_id}/preview")
async def get_preview(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file = await db.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    share_svc = ShareService(db)
    shares = await share_svc.get_user_shares_for_file(file_id, current_user.user_id)
    if not can_read(file.owner_id, current_user.user_id, current_user.role, shares):
        raise HTTPException(status_code=403, detail="Access denied")

    if not file.storage_key:
        raise HTTPException(status_code=400, detail="File has no storage key")

    try:
        storage = StorageService()
        url = storage.get_presigned_download_url(file.storage_key)
        return {
            "preview_url": url,
            "mime_type": file.mime_type,
            "name": file.name,
            "size": file.size,
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate preview URL")
