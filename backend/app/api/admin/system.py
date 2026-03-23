from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, require_admin

router = APIRouter(prefix="/api/admin/system", tags=["admin-system"])


@router.get("/health")
async def system_health(
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = {
        "minio": await _check_minio(),
        "postgres": await _check_postgres(db),
        "redis": await _check_redis(),
        "celery": await _check_celery(),
        "api": {"status": "healthy", "color": "green"},
    }
    return result


@router.get("/minio")
async def minio_status(
    current_user: CurrentUser = Depends(require_admin),
):
    return await _check_minio()


@router.get("/database")
async def database_status(
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _check_postgres(db)


@router.get("/redis")
async def redis_status(
    current_user: CurrentUser = Depends(require_admin),
):
    return await _check_redis()


@router.get("/celery")
async def celery_status(
    current_user: CurrentUser = Depends(require_admin),
):
    return await _check_celery()


async def _check_minio() -> dict:
    try:
        from app.utils.minio_client import get_minio_client
        from app.config import settings

        client = get_minio_client()
        buckets = client.list_buckets()
        bucket_info = []
        total_objects = 0

        for bucket in buckets:
            objects = list(client.list_objects(bucket.name, recursive=True))
            bucket_size = sum(obj.size or 0 for obj in objects)
            total_objects += len(objects)
            bucket_info.append({
                "name": bucket.name,
                "objects": len(objects),
                "size": bucket_size,
            })

        return {
            "status": "healthy",
            "color": "green",
            "buckets": bucket_info,
            "total_objects": total_objects,
        }
    except Exception as e:
        return {"status": "unhealthy", "color": "red", "error": str(e)}


async def _check_postgres(db: AsyncSession) -> dict:
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        # Get database size
        size_result = await db.execute(
            text("SELECT pg_database_size(current_database())")
        )
        db_size = size_result.scalar() or 0

        # Get active connections
        conn_result = await db.execute(
            text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
        )
        active_connections = conn_result.scalar() or 0

        return {
            "status": "healthy",
            "color": "green",
            "database_size": db_size,
            "active_connections": active_connections,
        }
    except Exception as e:
        return {"status": "unhealthy", "color": "red", "error": str(e)}


async def _check_redis() -> dict:
    try:
        import redis
        from app.config import settings

        r = redis.from_url(settings.REDIS_URL)
        info = r.info()

        return {
            "status": "healthy",
            "color": "green",
            "memory_used": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "keys_count": r.dbsize(),
        }
    except Exception as e:
        return {"status": "unhealthy", "color": "red", "error": str(e)}


async def _check_celery() -> dict:
    try:
        from app.tasks.celery_app import celery_app

        inspector = celery_app.control.inspect(timeout=3)
        active = inspector.active() or {}
        reserved = inspector.reserved() or {}
        stats = inspector.stats() or {}

        total_active = sum(len(tasks) for tasks in active.values())
        total_queued = sum(len(tasks) for tasks in reserved.values())
        num_workers = len(stats)

        return {
            "status": "healthy" if num_workers > 0 else "degraded",
            "color": "green" if num_workers > 0 else "yellow",
            "workers": num_workers,
            "active_tasks": total_active,
            "queued_tasks": total_queued,
        }
    except Exception as e:
        return {"status": "unhealthy", "color": "red", "error": str(e)}
