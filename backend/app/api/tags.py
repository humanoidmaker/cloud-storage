import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user
from app.models.file import File
from app.models.file_tag import FileTag
from app.models.tag import Tag
from app.schemas.tag import TagCreateRequest, TagUpdateRequest

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.post("", status_code=201)
async def create_tag(
    body: TagCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check duplicate name
    result = await db.execute(
        select(Tag).where(
            and_(Tag.user_id == current_user.user_id, Tag.name == body.name)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tag with this name already exists")

    tag = Tag(
        id=uuid.uuid4(),
        name=body.name,
        color=body.color,
        user_id=current_user.user_id,
    )
    db.add(tag)
    await db.flush()

    return _serialize_tag(tag, 0)


@router.get("")
async def list_tags(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Tag).where(Tag.user_id == current_user.user_id)
    )
    tags = list(result.scalars().all())

    items = []
    for tag in tags:
        count_result = await db.execute(
            select(func.count()).select_from(
                select(FileTag).where(FileTag.tag_id == tag.id).subquery()
            )
        )
        file_count = count_result.scalar() or 0
        items.append(_serialize_tag(tag, file_count))

    return items


@router.put("/{tag_id}")
async def update_tag(
    tag_id: uuid.UUID,
    body: TagUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tag = await db.get(Tag, tag_id)
    if not tag or tag.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Tag not found")

    if body.name is not None:
        # Check duplicate
        result = await db.execute(
            select(Tag).where(
                and_(
                    Tag.user_id == current_user.user_id,
                    Tag.name == body.name,
                    Tag.id != tag_id,
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Tag with this name already exists")
        tag.name = body.name

    if body.color is not None:
        tag.color = body.color

    await db.flush()
    return _serialize_tag(tag, 0)


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tag = await db.get(Tag, tag_id)
    if not tag or tag.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Remove all file_tag associations
    result = await db.execute(
        select(FileTag).where(FileTag.tag_id == tag_id)
    )
    for ft in result.scalars().all():
        await db.delete(ft)

    await db.delete(tag)
    await db.flush()
    return None


@router.post("/files/{file_id}/tags/{tag_id}")
async def tag_file(
    file_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify file ownership
    file = await db.get(File, file_id)
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Verify tag ownership
    tag = await db.get(Tag, tag_id)
    if not tag or tag.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Check if already tagged
    result = await db.execute(
        select(FileTag).where(
            and_(FileTag.file_id == file_id, FileTag.tag_id == tag_id)
        )
    )
    if result.scalar_one_or_none():
        return {"message": "File already tagged"}

    ft = FileTag(id=uuid.uuid4(), file_id=file_id, tag_id=tag_id)
    db.add(ft)
    await db.flush()
    return {"message": "Tag added to file"}


@router.delete("/files/{file_id}/tags/{tag_id}", status_code=204)
async def untag_file(
    file_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FileTag).where(
            and_(FileTag.file_id == file_id, FileTag.tag_id == tag_id)
        )
    )
    ft = result.scalar_one_or_none()
    if ft:
        await db.delete(ft)
        await db.flush()
    return None


@router.get("/{tag_id}/files")
async def get_files_by_tag(
    tag_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tag = await db.get(Tag, tag_id)
    if not tag or tag.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Tag not found")

    result = await db.execute(
        select(File)
        .join(FileTag, FileTag.file_id == File.id)
        .where(
            and_(
                FileTag.tag_id == tag_id,
                File.is_trashed == False,
            )
        )
    )
    files = list(result.scalars().all())

    return [
        {
            "id": str(f.id),
            "name": f.name,
            "mime_type": f.mime_type,
            "size": f.size,
            "is_folder": f.is_folder,
            "thumbnail_key": f.thumbnail_key,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]


def _serialize_tag(tag, file_count: int) -> dict:
    return {
        "id": str(tag.id),
        "name": tag.name,
        "color": tag.color,
        "user_id": str(tag.user_id),
        "created_at": tag.created_at.isoformat() if tag.created_at else None,
        "file_count": file_count,
    }
