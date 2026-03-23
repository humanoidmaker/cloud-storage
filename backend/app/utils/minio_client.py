from minio import Minio

from app.config import settings

_client: Minio | None = None


def get_minio_client() -> Minio:
    """Get or create a MinIO client singleton."""
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _client


def init_buckets() -> None:
    """Initialize required MinIO buckets if they don't exist."""
    client = get_minio_client()
    for bucket_name in [settings.MINIO_FILES_BUCKET, settings.MINIO_THUMBNAILS_BUCKET]:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
