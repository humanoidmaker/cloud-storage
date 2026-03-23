import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_client_ip, get_current_user
from app.models.user import User
from app.schemas.share import (
    ShareCreateRequest,
    ShareLinkAccessRequest,
    ShareResponse,
    ShareUpdateRequest,
)
from app.services.activity_service import ActivityService
from app.services.share_service import ShareService

router = APIRouter(prefix="/api/shares", tags=["sharing"])


@router.post("", status_code=201)
async def create_share(
    body: ShareCreateRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ShareService(db)
    share = await svc.create_share(
        file_id=body.file_id,
        shared_by=current_user.user_id,
        shared_with_email=body.shared_with_email,
        permission=body.permission,
        create_link=body.create_link,
        password=body.password,
        expires_at=body.expires_at,
    )

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="share",
        file_id=body.file_id,
        details={
            "shared_with": body.shared_with_email,
            "permission": body.permission,
            "is_link": body.create_link,
        },
        ip_address=get_client_ip(request),
    )

    return _serialize_share(share)


@router.get("/file/{file_id}")
async def list_shares_for_file(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ShareService(db)
    shares = await svc.list_shares_for_file(file_id, current_user.user_id)
    return [_serialize_share(s) for s in shares]


@router.get("/shared-with-me")
async def shared_with_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ShareService(db)
    shares = await svc.list_shared_with_user(current_user.user_id)

    results = []
    for share in shares:
        file_data = None
        if share.file:
            file_data = {
                "id": str(share.file.id),
                "name": share.file.name,
                "mime_type": share.file.mime_type,
                "size": share.file.size,
                "is_folder": share.file.is_folder,
            }

        shared_by_user = await db.get(User, share.shared_by)
        results.append({
            "file": file_data,
            "permission": share.permission,
            "shared_by_name": shared_by_user.name if shared_by_user else "Unknown",
            "shared_at": share.created_at.isoformat() if share.created_at else None,
        })

    return results


@router.put("/{share_id}")
async def update_share(
    share_id: uuid.UUID,
    body: ShareUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ShareService(db)
    if not body.permission:
        raise HTTPException(status_code=422, detail="Permission is required")
    share = await svc.update_share_permission(share_id, current_user.user_id, body.permission)
    return _serialize_share(share)


@router.delete("/{share_id}", status_code=204)
async def revoke_share(
    share_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ShareService(db)
    await svc.revoke_share(share_id, current_user.user_id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id,
        action="unshare",
        details={"share_id": str(share_id)},
        ip_address=get_client_ip(request),
    )

    return None


@router.get("/link/{token}")
async def access_share_link(
    token: str,
    password: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint - no auth required."""
    svc = ShareService(db)
    share = await svc.validate_share_token(token, password)

    file_data = None
    if share.file:
        file_data = {
            "id": str(share.file.id),
            "name": share.file.name,
            "mime_type": share.file.mime_type,
            "size": share.file.size,
            "is_folder": share.file.is_folder,
            "thumbnail_key": share.file.thumbnail_key,
        }

    return {
        "file": file_data,
        "permission": share.permission,
    }


def _serialize_share(share) -> dict:
    return {
        "id": str(share.id),
        "file_id": str(share.file_id),
        "shared_by": str(share.shared_by),
        "shared_with_user_id": str(share.shared_with_user_id) if share.shared_with_user_id else None,
        "shared_with_email": share.shared_with_email,
        "share_token": share.share_token,
        "permission": share.permission,
        "has_password": share.password_hash is not None,
        "expires_at": share.expires_at.isoformat() if share.expires_at else None,
        "created_at": share.created_at.isoformat() if share.created_at else None,
    }
