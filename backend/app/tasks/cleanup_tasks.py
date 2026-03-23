import asyncio

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def auto_purge_trash(self) -> dict:
    """Auto-purge trash items older than configured threshold."""
    try:
        from app.database import async_session_factory
        from app.services.trash_service import TrashService

        async def _purge() -> int:
            async with async_session_factory() as session:
                svc = TrashService(session)
                freed = await svc.auto_purge_old_trash()
                await session.commit()
                return freed

        loop = asyncio.new_event_loop()
        try:
            freed = loop.run_until_complete(_purge())
        finally:
            loop.close()

        return {"status": "success", "freed_bytes": freed}
    except Exception as exc:
        self.retry(exc=exc)
        return {"status": "error", "error": str(exc)}


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def cleanup_old_versions(self) -> dict:
    """Clean up file versions beyond the configured limit."""
    try:
        from app.config import settings
        from app.database import async_session_factory
        from app.models.file import File
        from app.models.file_version import FileVersion
        from app.services.version_service import VersionService

        from sqlalchemy import func, select

        async def _cleanup() -> int:
            async with async_session_factory() as session:
                # Find files with too many versions
                result = await session.execute(
                    select(FileVersion.file_id, func.count(FileVersion.id))
                    .group_by(FileVersion.file_id)
                    .having(func.count(FileVersion.id) > settings.MAX_FILE_VERSIONS)
                )
                files_to_clean = list(result.all())

                cleaned = 0
                svc = VersionService(session)
                for file_id, count in files_to_clean:
                    await svc._cleanup_old_versions(file_id)
                    cleaned += 1

                await session.commit()
                return cleaned

        loop = asyncio.new_event_loop()
        try:
            cleaned = loop.run_until_complete(_cleanup())
        finally:
            loop.close()

        return {"status": "success", "files_cleaned": cleaned}
    except Exception as exc:
        self.retry(exc=exc)
        return {"status": "error", "error": str(exc)}
