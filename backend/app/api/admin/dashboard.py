from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, require_admin
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])


@router.get("")
async def get_dashboard(
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = AdminService(db)
    stats = await svc.get_dashboard_stats()
    return stats
