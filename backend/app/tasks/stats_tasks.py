import asyncio
import uuid
from datetime import date

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def aggregate_daily_stats(self) -> dict:
    """Aggregate daily storage stats for all users."""
    try:
        from app.database import async_session_factory
        from app.models.activity_log import ActivityLog
        from app.models.file import File
        from app.models.storage_stats import StorageStats
        from app.models.user import User

        from sqlalchemy import and_, func, select

        async def _aggregate() -> int:
            async with async_session_factory() as session:
                today = date.today()

                result = await session.execute(select(User))
                users = list(result.scalars().all())

                count = 0
                for user in users:
                    # Count files
                    fc_result = await session.execute(
                        select(func.count()).select_from(
                            select(File).where(
                                and_(File.owner_id == user.id, File.is_folder == False)
                            ).subquery()
                        )
                    )
                    files_count = fc_result.scalar() or 0

                    # Count folders
                    fld_result = await session.execute(
                        select(func.count()).select_from(
                            select(File).where(
                                and_(File.owner_id == user.id, File.is_folder == True)
                            ).subquery()
                        )
                    )
                    folders_count = fld_result.scalar() or 0

                    # Count uploads today
                    uploads_result = await session.execute(
                        select(func.count()).select_from(
                            select(ActivityLog).where(
                                and_(
                                    ActivityLog.user_id == user.id,
                                    ActivityLog.action == "upload",
                                    func.date(ActivityLog.created_at) == today,
                                )
                            ).subquery()
                        )
                    )
                    uploads_count = uploads_result.scalar() or 0

                    # Count downloads today
                    downloads_result = await session.execute(
                        select(func.count()).select_from(
                            select(ActivityLog).where(
                                and_(
                                    ActivityLog.user_id == user.id,
                                    ActivityLog.action == "download",
                                    func.date(ActivityLog.created_at) == today,
                                )
                            ).subquery()
                        )
                    )
                    downloads_count = downloads_result.scalar() or 0

                    # Check if stats already exist for today
                    existing = await session.execute(
                        select(StorageStats).where(
                            and_(
                                StorageStats.user_id == user.id,
                                StorageStats.date == today,
                            )
                        )
                    )
                    stat = existing.scalar_one_or_none()

                    if stat:
                        stat.files_count = files_count
                        stat.folders_count = folders_count
                        stat.storage_used = user.storage_used
                        stat.uploads_count = uploads_count
                        stat.downloads_count = downloads_count
                    else:
                        stat = StorageStats(
                            id=uuid.uuid4(),
                            user_id=user.id,
                            date=today,
                            files_count=files_count,
                            folders_count=folders_count,
                            storage_used=user.storage_used,
                            uploads_count=uploads_count,
                            downloads_count=downloads_count,
                        )
                        session.add(stat)

                    count += 1

                await session.commit()
                return count

        loop = asyncio.new_event_loop()
        try:
            count = loop.run_until_complete(_aggregate())
        finally:
            loop.close()

        return {"status": "success", "users_processed": count}
    except Exception as exc:
        self.retry(exc=exc)
        return {"status": "error", "error": str(exc)}
