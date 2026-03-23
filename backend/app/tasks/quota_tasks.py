import asyncio

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def recalculate_all_quotas(self) -> dict:
    """Nightly recalculation of all user storage quotas."""
    try:
        from app.database import async_session_factory
        from app.services.quota_service import QuotaService

        async def _recalculate() -> int:
            async with async_session_factory() as session:
                svc = QuotaService(session)
                count = await svc.recalculate_all_quotas()
                await session.commit()
                return count

        loop = asyncio.new_event_loop()
        try:
            count = loop.run_until_complete(_recalculate())
        finally:
            loop.close()

        return {"status": "success", "users_updated": count}
    except Exception as exc:
        self.retry(exc=exc)
        return {"status": "error", "error": str(exc)}
