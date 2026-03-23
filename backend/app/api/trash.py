import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_client_ip, get_current_user
from app.services.activity_service import ActivityService
from app.services.trash_service import TrashService

router = APIRouter(prefix="/api/trash", tags=["trash"])


@router.get("")
async def list_trash(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TrashService(db)
    items, total = await svc.list_trash(current_user.user_id, page, page_size)

    return {
        "items": [
            {
                "id": str(f.id),
                "name": f.name,
                "mime_type": f.mime_type,
                "size": f.size,
                "is_folder": f.is_folder,
                "trashed_at": f.trashed_at.isoformat() if f.trashed_at else None,
                "parent_folder_id": str(f.parent_folder_id) if f.parent_folder_id else None,
            }
            for f in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{file_id}/restore")
async def restore_file(
    file_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TrashService(db)
    file = await svc.restore_file(file_id, current_user.user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="restore",
        file_id=file_id,
        ip_address=get_client_ip(request),
    )

    return {"message": "File restored", "file_id": str(file.id)}


@router.delete("/{file_id}", status_code=204)
async def permanent_delete(
    file_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TrashService(db)
    freed = await svc.permanent_delete(file_id, current_user.user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="permanent_delete",
        file_id=file_id,
        details={"freed_bytes": freed},
        ip_address=get_client_ip(request),
    )

    return None


@router.post("/empty")
async def empty_trash(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TrashService(db)
    freed = await svc.empty_trash(current_user.user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="empty_trash",
        details={"freed_bytes": freed},
        ip_address=get_client_ip(request),
    )

    return {"message": "Trash emptied", "freed_bytes": freed}
