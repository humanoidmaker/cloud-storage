import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File as FastAPIFile
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_client_ip, get_current_user
from app.schemas.file import (
    BulkMoveRequest,
    BulkOperationRequest,
    FileCopyRequest,
    FileMoveRequest,
    FileResponse,
    FileUpdate,
    FileUploadResponse,
)
from app.schemas.common import PaginatedResponse, calculate_total_pages
from app.services.activity_service import ActivityService
from app.services.file_service import FileService
from app.services.share_service import ShareService
from app.services.storage_service import StorageService
from app.utils.permissions import can_read, can_write

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", status_code=201, response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    parent_folder_id: uuid.UUID | None = None,
    request: Request = None,  # type: ignore[assignment]
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    storage = StorageService()
    file_svc = FileService(db, storage)

    result = await file_svc.create_file(
        owner_id=current_user.user_id,
        filename=file.filename or "unnamed",
        file_content=content,
        parent_folder_id=parent_folder_id,
        content_type=file.content_type,
    )

    # Log activity
    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="upload",
        file_id=result.id,
        details={"filename": result.name, "size": result.size},
        ip_address=get_client_ip(request) if request else None,
    )

    # Trigger thumbnail generation asynchronously
    try:
        from app.tasks.thumbnail_tasks import generate_thumbnail
        generate_thumbnail.delay(str(result.id), result.storage_key, result.mime_type or "")
    except Exception:
        pass  # Don't fail upload if Celery is unavailable

    return result


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    file = await file_svc.get_file(file_id)

    # Check permissions
    share_svc = ShareService(db)
    shares = await share_svc.get_user_shares_for_file(file_id, current_user.user_id)

    if not can_read(file.owner_id, current_user.user_id, current_user.role, shares):
        raise HTTPException(status_code=403, detail="Access denied")

    return file


@router.get("/{file_id}/download")
async def download_file(
    file_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    file = await file_svc.get_file(file_id)

    share_svc = ShareService(db)
    shares = await share_svc.get_user_shares_for_file(file_id, current_user.user_id)

    if not can_read(file.owner_id, current_user.user_id, current_user.role, shares):
        raise HTTPException(status_code=403, detail="Access denied")

    url = await file_svc.get_download_url(file_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="download",
        file_id=file_id,
        ip_address=get_client_ip(request),
    )

    return RedirectResponse(url=url, status_code=302)


@router.put("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: uuid.UUID,
    body: FileUpdate,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    file = await file_svc.get_file(file_id)

    share_svc = ShareService(db)
    shares = await share_svc.get_user_shares_for_file(file_id, current_user.user_id)

    if not can_write(file.owner_id, current_user.user_id, current_user.role, shares):
        raise HTTPException(status_code=403, detail="Access denied")

    updated = await file_svc.update_file(file_id, file.owner_id, name=body.name)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="rename",
        file_id=file_id,
        details={"new_name": body.name},
        ip_address=get_client_ip(request),
    )

    return updated


@router.post("/{file_id}/move", response_model=FileResponse)
async def move_file(
    file_id: uuid.UUID,
    body: FileMoveRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    file = await file_svc.move_file(file_id, current_user.user_id, body.target_folder_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="move",
        file_id=file_id,
        details={"target_folder_id": str(body.target_folder_id)},
        ip_address=get_client_ip(request),
    )

    return file


@router.post("/{file_id}/copy", status_code=201, response_model=FileResponse)
async def copy_file(
    file_id: uuid.UUID,
    body: FileCopyRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    new_file = await file_svc.copy_file(
        file_id, current_user.user_id, body.target_folder_id, body.new_name
    )

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="copy",
        file_id=new_file.id,
        details={"original_file_id": str(file_id)},
        ip_address=get_client_ip(request),
    )

    return new_file


@router.delete("/{file_id}")
async def delete_file(
    file_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    await file_svc.soft_delete(file_id, current_user.user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="delete",
        file_id=file_id,
        ip_address=get_client_ip(request),
    )

    return {"message": "File moved to trash"}


@router.post("/bulk/delete")
async def bulk_delete(
    body: BulkOperationRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    count = await file_svc.bulk_delete(body.file_ids, current_user.user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="bulk_delete",
        details={"count": count, "file_ids": [str(fid) for fid in body.file_ids]},
        ip_address=get_client_ip(request),
    )

    return {"message": f"{count} files moved to trash"}


@router.post("/bulk/move")
async def bulk_move(
    body: BulkMoveRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    count = 0
    for fid in body.file_ids:
        try:
            await file_svc.move_file(fid, current_user.user_id, body.target_folder_id)
            count += 1
        except HTTPException:
            continue

    return {"message": f"{count} files moved"}


@router.post("/bulk/download", status_code=202)
async def bulk_download(
    body: BulkOperationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Start async zip generation task
    try:
        from app.tasks.zip_tasks import generate_folder_zip
        # For bulk download, we'd need a custom task; for now use the first file's parent
        task = generate_folder_zip.delay(
            str(body.file_ids[0]) if body.file_ids else "",
            str(current_user.user_id),
        )
        return {"message": "Zip generation started", "task_id": task.id}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to start zip generation")
