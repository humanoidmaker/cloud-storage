import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_client_ip, get_current_user
from app.models.file import File
from app.services.activity_service import ActivityService
from app.services.share_service import ShareService
from app.services.version_service import VersionService
from app.utils.permissions import can_read

router = APIRouter(prefix="/api/files/{file_id}/versions", tags=["versions"])


@router.get("")
async def list_versions(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check access
    file = await db.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    share_svc = ShareService(db)
    shares = await share_svc.get_user_shares_for_file(file_id, current_user.user_id)
    if not can_read(file.owner_id, current_user.user_id, current_user.role, shares):
        raise HTTPException(status_code=403, detail="Access denied")

    svc = VersionService(db)
    versions = await svc.list_versions(file_id)

    return [
        {
            "id": str(v.id),
            "file_id": str(v.file_id),
            "version_number": v.version_number,
            "size": v.size,
            "content_hash": v.content_hash,
            "created_by": str(v.created_by),
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


@router.get("/{version_number}/download")
async def download_version(
    file_id: uuid.UUID,
    version_number: int,
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

    svc = VersionService(db)
    url = await svc.get_version_download_url(file_id, version_number)
    return RedirectResponse(url=url, status_code=302)


@router.post("/{version_number}/restore")
async def restore_version(
    file_id: uuid.UUID,
    version_number: int,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file = await db.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if file.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only the owner can restore versions")

    svc = VersionService(db)
    updated_file = await svc.restore_version(file_id, version_number, current_user.user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="version_restore",
        file_id=file_id,
        details={"version_number": version_number},
        ip_address=get_client_ip(request),
    )

    return {"message": "Version restored", "file_id": str(updated_file.id)}


@router.delete("/{version_number}", status_code=204)
async def delete_version(
    file_id: uuid.UUID,
    version_number: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file = await db.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if file.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only the owner can delete versions")

    svc = VersionService(db)
    await svc.delete_version(file_id, version_number, current_user.user_id)
    return None
