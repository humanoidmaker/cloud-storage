from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, require_admin
from app.schemas.admin import AdminBulkQuotaRequest
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/admin/storage", tags=["admin-storage"])


@router.get("/breakdown")
async def get_storage_breakdown(
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    breakdown = await svc.get_storage_breakdown()
    return breakdown


@router.get("/top-consumers")
async def get_top_consumers(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    consumers = await svc.get_top_consumers(limit)
    return consumers


@router.get("/trends")
async def get_storage_trends(
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func, select
    from app.models.storage_stats import StorageStats

    thirty_days_ago = datetime.now(timezone.utc).date() - timedelta(days=30)

    result = await db.execute(
        select(
            StorageStats.date,
            func.sum(StorageStats.storage_used).label("total_storage"),
            func.sum(StorageStats.files_count).label("total_files"),
        )
        .where(StorageStats.date >= thirty_days_ago)
        .group_by(StorageStats.date)
        .order_by(StorageStats.date)
    )

    trends = [
        {
            "date": str(row.date),
            "total_storage": row.total_storage or 0,
            "total_files": row.total_files or 0,
        }
        for row in result.all()
    ]

    return trends


@router.post("/bulk-quota")
async def bulk_update_quota(
    body: AdminBulkQuotaRequest,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    count = await svc.bulk_update_quota(body.user_ids, body.storage_quota)
    return {"message": f"Quota updated for {count} users", "count": count}
