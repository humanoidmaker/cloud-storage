import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search_files(
    q: str = Query(default=""),
    type: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    tag_id: uuid.UUID | None = Query(default=None),
    folder_id: uuid.UUID | None = Query(default=None),
    starred: bool | None = Query(default=None),
    sort: str = Query(default="relevance"),
    order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not q or not q.strip():
        raise HTTPException(status_code=422, detail="Search query is required")

    svc = SearchService(db)
    files, total = await svc.search_files(
        user_id=current_user.user_id,
        query=q.strip(),
        file_type=type,
        date_from=date_from,
        date_to=date_to,
        tag_id=tag_id,
        folder_id=folder_id,
        starred=starred,
        sort_by=sort,
        sort_order=order,
        page=page,
        page_size=page_size,
    )

    return {
        "items": [
            {
                "id": str(f.id),
                "name": f.name,
                "mime_type": f.mime_type,
                "size": f.size,
                "is_folder": f.is_folder,
                "parent_folder_id": str(f.parent_folder_id) if f.parent_folder_id else None,
                "thumbnail_key": f.thumbnail_key,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in files
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "query": q,
    }
