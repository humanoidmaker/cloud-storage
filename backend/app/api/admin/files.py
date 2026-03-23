import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_client_ip, require_admin
from app.models.file import File
from app.schemas.file import BulkOperationRequest
from app.services.activity_service import ActivityService
from app.services.storage_service import StorageService
from app.services.trash_service import TrashService

router = APIRouter(prefix="/api/admin/files", tags=["admin-files"])


@router.get("")
async def browse_user_files(
    user_id: uuid.UUID = Query(...),
    folder_id: uuid.UUID | None = Query(default=None),
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(File).where(
            and_(
                File.owner_id == user_id,
                File.parent_folder_id == folder_id,
                File.is_trashed == False,
            )
        ).order_by(File.is_folder.desc(), File.name.asc())
    )
    files = list(result.scalars().all())

    return [
        {
            "id": str(f.id),
            "name": f.name,
            "mime_type": f.mime_type,
            "size": f.size,
            "is_folder": f.is_folder,
            "parent_folder_id": str(f.parent_folder_id) if f.parent_folder_id else None,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]


@router.get("/{file_id}/download")
async def admin_download_file(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    file = await db.get(File, file_id)
    if not file or not file.storage_key:
        raise HTTPException(status_code=404, detail="File not found")

    storage = StorageService()
    url = storage.get_presigned_download_url(file.storage_key)
    return RedirectResponse(url=url, status_code=302)


@router.delete("/{file_id}", status_code=204)
async def admin_delete_file(
    file_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    file = await db.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    svc = TrashService(db)
    await svc.permanent_delete(file_id, file.owner_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="admin_delete_file",
        file_id=file_id,
        details={"file_name": file.name, "owner_id": str(file.owner_id)},
        ip_address=get_client_ip(request),
    )

    return None


@router.post("/bulk-delete")
async def admin_bulk_delete(
    body: BulkOperationRequest,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = TrashService(db)
    count = 0
    for fid in body.file_ids:
        try:
            file = await db.get(File, fid)
            if file:
                await svc.permanent_delete(fid, file.owner_id)
                count += 1
        except Exception:
            continue

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="admin_bulk_delete",
        details={"count": count, "file_ids": [str(fid) for fid in body.file_ids]},
        ip_address=get_client_ip(request),
    )

    return {"message": f"{count} files deleted"}
