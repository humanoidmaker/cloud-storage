import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_client_ip, require_admin
from app.schemas.admin import AdminQuotaUpdateRequest, AdminUserCreateRequest, AdminUserUpdateRequest
from app.schemas.user import UserResponse
from app.services.activity_service import ActivityService
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


@router.get("")
async def list_users(
    search: str | None = Query(default=None),
    role: str | None = Query(default=None),
    status: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    users, total = await svc.list_users(
        search=search, role=role, status=status,
        sort_by=sort_by, sort_order=sort_order,
        page=page, page_size=page_size,
    )

    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "role": u.role,
                "storage_used": u.storage_used,
                "storage_quota": u.storage_quota,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", status_code=201)
async def create_user(
    body: AdminUserCreateRequest,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    user = await svc.create_user(
        email=body.email,
        name=body.name,
        password=body.password,
        role=body.role,
        storage_quota=body.storage_quota,
    )

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="admin_create_user",
        details={"created_user_email": body.email},
        ip_address=get_client_ip(request),
    )

    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "storage_quota": user.storage_quota,
        "is_active": user.is_active,
    }


@router.put("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: AdminUserUpdateRequest,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    user = await svc.update_user(user_id, name=body.name, email=body.email, role=body.role)
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.put("/{user_id}/quota")
async def update_quota(
    user_id: uuid.UUID,
    body: AdminQuotaUpdateRequest,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    user = await svc.update_quota(user_id, body.storage_quota)
    return {
        "id": str(user.id),
        "storage_used": user.storage_used,
        "storage_quota": user.storage_quota,
    }


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    user = await svc.deactivate_user(user_id, current_user.user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="admin_deactivate_user",
        details={"target_user_id": str(user_id)},
        ip_address=get_client_ip(request),
    )

    return {"message": "User deactivated", "user_id": str(user.id)}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    user = await svc.activate_user(user_id)
    return {"message": "User activated", "user_id": str(user.id)}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    temp_password = await svc.reset_password(user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="admin_reset_password",
        details={"target_user_id": str(user_id)},
        ip_address=get_client_ip(request),
    )

    return {"message": "Password reset", "temporary_password": temp_password}


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    transfer_to: uuid.UUID | None = Query(default=None),
    request: Request = None,  # type: ignore[assignment]
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    await svc.delete_user(user_id, current_user.user_id, transfer_to)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="admin_delete_user",
        details={"deleted_user_id": str(user_id), "transferred_to": str(transfer_to) if transfer_to else None},
        ip_address=get_client_ip(request) if request else None,
    )

    return {"message": "User deleted"}
