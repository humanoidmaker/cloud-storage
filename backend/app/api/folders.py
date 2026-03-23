import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_client_ip, get_current_user
from app.schemas.file import FileMoveRequest, FileUpdate
from app.schemas.folder import BreadcrumbItem, FolderCreateRequest, FolderResponse
from app.services.activity_service import ActivityService
from app.services.folder_service import FolderService

router = APIRouter(prefix="/api/folders", tags=["folders"])


@router.post("", status_code=201)
async def create_folder(
    body: FolderCreateRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FolderService(db)
    folder = await svc.create_folder(
        owner_id=current_user.user_id,
        name=body.name,
        parent_folder_id=body.parent_folder_id,
    )

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="create_folder",
        file_id=folder.id,
        details={"name": folder.name},
        ip_address=get_client_ip(request),
    )

    return {
        "id": str(folder.id),
        "name": folder.name,
        "owner_id": str(folder.owner_id),
        "parent_folder_id": str(folder.parent_folder_id) if folder.parent_folder_id else None,
        "is_folder": True,
        "is_trashed": False,
        "created_at": folder.created_at.isoformat() if folder.created_at else None,
        "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
    }


@router.get("/contents")
async def get_root_contents(
    sort_by: str = Query(default="name"),
    sort_order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FolderService(db)
    items, total = await svc.get_folder_contents(
        owner_id=current_user.user_id,
        folder_id=None,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    return {
        "items": [_serialize_file(f) for f in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get("/tree")
async def get_folder_tree(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FolderService(db)
    tree = await svc.get_folder_tree(current_user.user_id)
    return tree


@router.get("/{folder_id}/contents")
async def get_folder_contents(
    folder_id: uuid.UUID,
    sort_by: str = Query(default="name"),
    sort_order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FolderService(db)
    items, total = await svc.get_folder_contents(
        owner_id=current_user.user_id,
        folder_id=folder_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    return {
        "items": [_serialize_file(f) for f in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get("/{folder_id}/breadcrumb")
async def get_breadcrumb(
    folder_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FolderService(db)
    breadcrumbs = await svc.get_breadcrumb(folder_id, current_user.user_id)
    return breadcrumbs


@router.put("/{folder_id}")
async def rename_folder(
    folder_id: uuid.UUID,
    body: FileUpdate,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.name:
        raise HTTPException(status_code=422, detail="Name is required")

    svc = FolderService(db)
    folder = await svc.rename_folder(folder_id, current_user.user_id, body.name)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="rename",
        file_id=folder_id,
        details={"new_name": body.name},
        ip_address=get_client_ip(request),
    )

    return _serialize_file(folder)


@router.post("/{folder_id}/move")
async def move_folder(
    folder_id: uuid.UUID,
    body: FileMoveRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FolderService(db)
    folder = await svc.move_folder(folder_id, current_user.user_id, body.target_folder_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="move",
        file_id=folder_id,
        details={"target_folder_id": str(body.target_folder_id)},
        ip_address=get_client_ip(request),
    )

    return _serialize_file(folder)


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FolderService(db)
    await svc.delete_folder(folder_id, current_user.user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="delete",
        file_id=folder_id,
        ip_address=get_client_ip(request),
    )

    return {"message": "Folder moved to trash"}


def _serialize_file(f) -> dict:
    return {
        "id": str(f.id),
        "name": f.name,
        "mime_type": f.mime_type,
        "size": f.size,
        "owner_id": str(f.owner_id),
        "parent_folder_id": str(f.parent_folder_id) if f.parent_folder_id else None,
        "is_folder": f.is_folder,
        "is_trashed": f.is_trashed,
        "thumbnail_key": f.thumbnail_key,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
    }
