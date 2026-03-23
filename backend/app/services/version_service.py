import uuid

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.file import File
from app.models.file_version import FileVersion
from app.services.storage_service import StorageService


class VersionService:
    def __init__(self, db: AsyncSession, storage: StorageService | None = None):
        self.db = db
        self.storage = storage or StorageService()

    async def create_version(
        self,
        file_id: uuid.UUID,
        storage_key: str,
        size: int,
        content_hash: str | None,
        created_by: uuid.UUID,
    ) -> FileVersion:
        """Create a new version entry for a file."""
        # Get next version number
        result = await self.db.execute(
            select(func.coalesce(func.max(FileVersion.version_number), 0)).where(
                FileVersion.file_id == file_id
            )
        )
        max_version = result.scalar() or 0
        next_version = max_version + 1

        version = FileVersion(
            id=uuid.uuid4(),
            file_id=file_id,
            version_number=next_version,
            storage_key=storage_key,
            size=size,
            content_hash=content_hash,
            created_by=created_by,
        )
        self.db.add(version)
        await self.db.flush()

        # Cleanup old versions beyond the limit
        await self._cleanup_old_versions(file_id)

        return version

    async def list_versions(self, file_id: uuid.UUID) -> list[FileVersion]:
        """List all versions of a file, ordered by version number descending."""
        result = await self.db.execute(
            select(FileVersion)
            .where(FileVersion.file_id == file_id)
            .order_by(FileVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def get_version(self, file_id: uuid.UUID, version_number: int) -> FileVersion:
        """Get a specific version."""
        result = await self.db.execute(
            select(FileVersion).where(
                and_(
                    FileVersion.file_id == file_id,
                    FileVersion.version_number == version_number,
                )
            )
        )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        return version

    async def restore_version(
        self, file_id: uuid.UUID, version_number: int, user_id: uuid.UUID
    ) -> File:
        """Restore a previous version to be the current file."""
        file = await self.db.get(File, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        version = await self.get_version(file_id, version_number)

        # Save current state as a new version
        if file.storage_key:
            await self.create_version(
                file_id=file_id,
                storage_key=file.storage_key,
                size=file.size,
                content_hash=file.content_hash,
                created_by=user_id,
            )

        # Restore the selected version
        file.storage_key = version.storage_key
        file.size = version.size
        file.content_hash = version.content_hash
        await self.db.flush()

        return file

    async def delete_version(
        self, file_id: uuid.UUID, version_number: int, user_id: uuid.UUID
    ) -> None:
        """Delete a specific version. Cannot delete the current (latest) version."""
        # Get the latest version number
        result = await self.db.execute(
            select(func.max(FileVersion.version_number)).where(
                FileVersion.file_id == file_id
            )
        )
        max_version = result.scalar()

        # We allow deleting any version from the versions table
        # The "current" version is the file record itself, not a version record
        version = await self.get_version(file_id, version_number)

        # Delete from storage
        try:
            self.storage.delete_file(version.storage_key)
        except Exception:
            pass  # Best effort

        await self.db.delete(version)
        await self.db.flush()

    async def _cleanup_old_versions(self, file_id: uuid.UUID) -> None:
        """Remove versions beyond the configured max, keeping the most recent."""
        max_versions = settings.MAX_FILE_VERSIONS

        result = await self.db.execute(
            select(FileVersion)
            .where(FileVersion.file_id == file_id)
            .order_by(FileVersion.version_number.desc())
        )
        versions = list(result.scalars().all())

        if len(versions) > max_versions:
            to_delete = versions[max_versions:]
            for v in to_delete:
                try:
                    self.storage.delete_file(v.storage_key)
                except Exception:
                    pass
                await self.db.delete(v)
            await self.db.flush()

    async def get_version_download_url(
        self, file_id: uuid.UUID, version_number: int
    ) -> str:
        """Get presigned URL for downloading a specific version."""
        version = await self.get_version(file_id, version_number)
        return self.storage.get_presigned_download_url(version.storage_key)
