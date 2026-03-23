import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user
from app.models.file import File
from app.models.star import Star
from app.services.share_service import ShareService
from app.utils.permissions import can_read

router = APIRouter(prefix="/api/stars", tags=["stars"])


@router.post("/{file_id}", status_code=201)
async def star_file(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check file exists and user has access
    file = await db.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    share_svc = ShareService(db)
    shares = await share_svc.get_user_shares_for_file(file_id, current_user.user_id)
    if not can_read(file.owner_id, current_user.user_id, current_user.role, shares):
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if already starred (idempotent)
    result = await db.execute(
        select(Star).where(
            and_(Star.user_id == current_user.user_id, Star.file_id == file_id)
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {"message": "File already starred"}

    star = Star(id=uuid.uuid4(), user_id=current_user.user_id, file_id=file_id)
    db.add(star)
    await db.flush()

    return {"message": "File starred"}


@router.delete("/{file_id}", status_code=204)
async def unstar_file(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Star).where(
            and_(Star.user_id == current_user.user_id, Star.file_id == file_id)
        )
    )
    star = result.scalar_one_or_none()
    if star:
        await db.delete(star)
        await db.flush()
    return None


@router.get("")
async def list_starred(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Star).where(Star.user_id == current_user.user_id)
    )
    stars = list(result.scalars().all())

    items = []
    for star in stars:
        file = await db.get(File, star.file_id)
        if file and not file.is_trashed:
            items.append({
                "id": str(file.id),
                "name": file.name,
                "mime_type": file.mime_type,
                "size": file.size,
                "is_folder": file.is_folder,
                "thumbnail_key": file.thumbnail_key,
                "created_at": file.created_at.isoformat() if file.created_at else None,
                "starred_at": star.created_at.isoformat() if star.created_at else None,
            })

    return items
