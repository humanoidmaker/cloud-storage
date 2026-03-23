import uuid

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def generate_thumbnail(self, file_id: str, storage_key: str, mime_type: str) -> dict:
    """Async thumbnail generation after file upload."""
    try:
        from app.services.storage_service import StorageService
        from app.services.thumbnail_service import ThumbnailService

        storage = StorageService()
        thumbnail_svc = ThumbnailService(storage=storage)

        # Download the file
        file_content = storage.download_file(storage_key)

        # Generate thumbnail
        thumb_bytes = thumbnail_svc.generate_thumbnail(file_content, mime_type)
        if not thumb_bytes:
            return {"status": "skipped", "reason": "unsupported_type"}

        # Upload thumbnail
        fid = uuid.UUID(file_id)
        thumb_key = storage.upload_thumbnail(fid, thumb_bytes)

        return {"status": "success", "thumbnail_key": thumb_key}

    except Exception as exc:
        self.retry(exc=exc)
        return {"status": "error", "error": str(exc)}
