from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "cloud_storage",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_max_retries=3,
    result_expires=3600,
    beat_schedule={
        "auto-purge-trash": {
            "task": "app.tasks.cleanup_tasks.auto_purge_trash",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "recalculate-quotas": {
            "task": "app.tasks.quota_tasks.recalculate_all_quotas",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        "aggregate-daily-stats": {
            "task": "app.tasks.stats_tasks.aggregate_daily_stats",
            "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
        },
        "cleanup-old-versions": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_versions",
            "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
        },
    },
)

celery_app.autodiscover_tasks([
    "app.tasks.thumbnail_tasks",
    "app.tasks.cleanup_tasks",
    "app.tasks.quota_tasks",
    "app.tasks.zip_tasks",
    "app.tasks.stats_tasks",
])
