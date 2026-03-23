import io
import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.config import settings
from app.utils.minio_client import get_minio_client


class StorageError(Exception):
    """Raised when a storage operation fails."""
    pass


class StorageService:
    def __init__(self, client: Minio | None = None):
        self.client = client or get_minio_client()
        self.files_bucket = settings.MINIO_FILES_BUCKET
        self.thumbnails_bucket = settings.MINIO_THUMBNAILS_BUCKET

    def upload_file(
        self,
        file_content: bytes | io.BytesIO,
        storage_key: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload a file to MinIO. Returns the storage key."""
        try:
            if isinstance(file_content, bytes):
                file_content = io.BytesIO(file_content)

            file_content.seek(0, 2)
            size = file_content.tell()
            file_content.seek(0)

            self.client.put_object(
                self.files_bucket,
                storage_key,
                file_content,
                length=size,
                content_type=content_type,
                metadata=metadata,
            )
            return storage_key
        except S3Error as e:
            raise StorageError(f"Failed to upload file: {str(e)}")
        except Exception as e:
            raise StorageError(f"Storage connection error: {str(e)}")

    def download_file(self, storage_key: str) -> bytes:
        """Download a file from MinIO. Returns bytes."""
        try:
            response = self.client.get_object(self.files_bucket, storage_key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise StorageError("File not found in storage")
            raise StorageError(f"Failed to download file: {str(e)}")
        except Exception as e:
            raise StorageError(f"Storage connection error: {str(e)}")

    def delete_file(self, storage_key: str) -> None:
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(self.files_bucket, storage_key)
        except S3Error as e:
            raise StorageError(f"Failed to delete file: {str(e)}")
        except Exception as e:
            raise StorageError(f"Storage connection error: {str(e)}")

    def get_presigned_download_url(self, storage_key: str, expires: int | None = None) -> str:
        """Generate a presigned download URL."""
        try:
            expiry = timedelta(seconds=expires or settings.PRESIGNED_URL_EXPIRY_SECONDS)
            url = self.client.presigned_get_object(self.files_bucket, storage_key, expires=expiry)
            return url
        except S3Error as e:
            raise StorageError(f"Failed to generate presigned URL: {str(e)}")
        except Exception as e:
            raise StorageError(f"Storage connection error: {str(e)}")

    def get_presigned_upload_url(self, storage_key: str, expires: int | None = None) -> str:
        """Generate a presigned upload URL for direct browser-to-MinIO upload."""
        try:
            expiry = timedelta(seconds=expires or settings.PRESIGNED_URL_EXPIRY_SECONDS)
            url = self.client.presigned_put_object(self.files_bucket, storage_key, expires=expiry)
            return url
        except S3Error as e:
            raise StorageError(f"Failed to generate presigned upload URL: {str(e)}")
        except Exception as e:
            raise StorageError(f"Storage connection error: {str(e)}")

    def copy_object(self, source_key: str, dest_key: str) -> str:
        """Copy an object within the same bucket."""
        try:
            from minio.commonconfig import CopySource
            self.client.copy_object(
                self.files_bucket,
                dest_key,
                CopySource(self.files_bucket, source_key),
            )
            return dest_key
        except S3Error as e:
            raise StorageError(f"Failed to copy object: {str(e)}")
        except Exception as e:
            raise StorageError(f"Storage connection error: {str(e)}")

    def get_object_metadata(self, storage_key: str) -> dict[str, str]:
        """Get metadata for an object (size, content_type)."""
        try:
            stat = self.client.stat_object(self.files_bucket, storage_key)
            return {
                "size": str(stat.size),
                "content_type": stat.content_type or "application/octet-stream",
                "etag": stat.etag or "",
                "last_modified": str(stat.last_modified) if stat.last_modified else "",
            }
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise StorageError("File not found in storage")
            raise StorageError(f"Failed to get object metadata: {str(e)}")
        except Exception as e:
            raise StorageError(f"Storage connection error: {str(e)}")

    def upload_thumbnail(self, file_id: uuid.UUID, thumbnail_bytes: bytes) -> str:
        """Upload a thumbnail to the thumbnails bucket."""
        try:
            key = f"thumbnails/{file_id}.jpg"
            data = io.BytesIO(thumbnail_bytes)
            self.client.put_object(
                self.thumbnails_bucket,
                key,
                data,
                length=len(thumbnail_bytes),
                content_type="image/jpeg",
            )
            return key
        except Exception as e:
            raise StorageError(f"Failed to upload thumbnail: {str(e)}")

    def get_thumbnail_url(self, thumbnail_key: str) -> str:
        """Get presigned URL for a thumbnail."""
        try:
            return self.client.presigned_get_object(
                self.thumbnails_bucket,
                thumbnail_key,
                expires=timedelta(seconds=settings.PRESIGNED_URL_EXPIRY_SECONDS),
            )
        except Exception as e:
            raise StorageError(f"Failed to get thumbnail URL: {str(e)}")
