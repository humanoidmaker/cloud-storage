import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.user import User
from app.services.storage_service import StorageService


class TrashService:
    def __init__(self, db: AsyncSession, storage: StorageService | None = None):
        self.db = db
        self.storage = storage or StorageService()

    async def trash_file(self, file_id: uuid.UUID, owner_id: uuid.UUID) -> File:
        """Move a file or folder to trash (soft delete)."""
        file = await self.db.get(File, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        if file.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        now = datetime.now(timezone.utc)
        file.is_trashed = True
        file.trashed_at = now

        # If it's a folder, recursively trash contents
        if file.is_folder:
            await self._recursive_trash(file_id, owner_id, now)

        await self.db.flush()
        return file

    async def _recursive_trash(
        self, folder_id: uuid.UUID, owner_id: uuid.UUID, now: datetime
    ) -> None:
        """Recursively trash all descendants of a folder."""
        queue = [folder_id]
        while queue:
            current_id = queue.pop(0)
            result = await self.db.execute(
                select(File).where(
                    and_(
                        File.parent_folder_id == current_id,
                        File.owner_id == owner_id,
                        File.is_trashed == False,
                    )
                )
            )
            children = list(result.scalars().all())
            for child in children:
                child.is_trashed = True
                child.trashed_at = now
                if child.is_folder:
                    queue.append(child.id)

    async def restore_file(self, file_id: uuid.UUID, owner_id: uuid.UUID) -> File:
        """Restore a file from trash."""
        file = await self.db.get(File, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        if file.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Permission denied")
        if not file.is_trashed:
            raise HTTPException(status_code=400, detail="File is not in trash")

        # Check if parent folder still exists and is not trashed
        if file.parent_folder_id:
            parent = await self.db.get(File, file.parent_folder_id)
            if not parent or parent.is_trashed:
                # Move to root
                file.parent_folder_id = None

        file.is_trashed = False
        file.trashed_at = None

        # If folder, recursively restore
        if file.is_folder:
            await self._recursive_restore(file_id, owner_id)

        await self.db.flush()
        return file

    async def _recursive_restore(self, folder_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        """Recursively restore all trashed descendants of a folder."""
        queue = [folder_id]
        while queue:
            current_id = queue.pop(0)
            result = await self.db.execute(
                select(File).where(
                    and_(
                        File.parent_folder_id == current_id,
                        File.owner_id == owner_id,
                        File.is_trashed == True,
                    )
                )
            )
            children = list(result.scalars().all())
            for child in children:
                child.is_trashed = False
                child.trashed_at = None
                if child.is_folder:
                    queue.append(child.id)

    async def permanent_delete(self, file_id: uuid.UUID, owner_id: uuid.UUID) -> int:
        """Permanently delete a file/folder from DB and storage. Returns freed bytes."""
        file = await self.db.get(File, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        if file.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        freed = 0

        if file.is_folder:
            freed = await self._recursive_permanent_delete(file_id, owner_id)
        else:
            freed = file.size
            # Delete versions
            result = await self.db.execute(
                select(FileVersion).where(FileVersion.file_id == file_id)
            )
            versions = list(result.scalars().all())
            for v in versions:
                try:
                    self.storage.delete_file(v.storage_key)
                except Exception:
                    pass
                await self.db.delete(v)

            # Delete from storage
            if file.storage_key:
                try:
                    self.storage.delete_file(file.storage_key)
                except Exception:
                    pass

        await self.db.delete(file)

        # Update user storage
        user = await self.db.get(User, owner_id)
        if user:
            user.storage_used = max(0, user.storage_used - freed)

        await self.db.flush()
        return freed

    async def _recursive_permanent_delete(
        self, folder_id: uuid.UUID, owner_id: uuid.UUID
    ) -> int:
        """Recursively permanently delete folder contents. Returns total freed bytes."""
        freed = 0
        queue = [folder_id]

        while queue:
            current_id = queue.pop(0)
            result = await self.db.execute(
                select(File).where(
                    and_(
                        File.parent_folder_id == current_id,
                        File.owner_id == owner_id,
                    )
                )
            )
            children = list(result.scalars().all())
            for child in children:
                if child.is_folder:
                    queue.append(child.id)
                else:
                    freed += child.size
                    # Delete versions
                    vresult = await self.db.execute(
                        select(FileVersion).where(FileVersion.file_id == child.id)
                    )
                    for v in vresult.scalars().all():
                        try:
                            self.storage.delete_file(v.storage_key)
                        except Exception:
                            pass
                        await self.db.delete(v)

                    if child.storage_key:
                        try:
                            self.storage.delete_file(child.storage_key)
                        except Exception:
                            pass
                await self.db.delete(child)

        return freed

    async def list_trash(self, owner_id: uuid.UUID, page: int = 1, page_size: int = 20) -> tuple[list[File], int]:
        """List trashed items for a user."""
        from sqlalchemy import func as sqlfunc

        base_q = select(File).where(
            and_(File.owner_id == owner_id, File.is_trashed == True)
        )

        count_q = select(sqlfunc.count()).select_from(base_q.subquery())
        result = await self.db.execute(count_q)
        total = result.scalar() or 0

        base_q = base_q.order_by(File.trashed_at.desc())
        offset = (page - 1) * page_size
        base_q = base_q.offset(offset).limit(page_size)

        result = await self.db.execute(base_q)
        items = list(result.scalars().all())
        return items, total

    async def empty_trash(self, owner_id: uuid.UUID) -> int:
        """Permanently delete all trashed items for a user. Returns freed bytes."""
        result = await self.db.execute(
            select(File).where(
                and_(File.owner_id == owner_id, File.is_trashed == True)
            )
        )
        items = list(result.scalars().all())

        total_freed = 0
        for item in items:
            if not item.is_folder:
                total_freed += item.size
                if item.storage_key:
                    try:
                        self.storage.delete_file(item.storage_key)
                    except Exception:
                        pass
            await self.db.delete(item)

        user = await self.db.get(User, owner_id)
        if user:
            user.storage_used = max(0, user.storage_used - total_freed)

        await self.db.flush()
        return total_freed

    async def auto_purge_old_trash(self, days: int | None = None) -> int:
        """Find and permanently delete items trashed more than N days ago."""
        purge_days = days or settings.TRASH_AUTO_PURGE_DAYS
        threshold = datetime.now(timezone.utc) - timedelta(days=purge_days)

        result = await self.db.execute(
            select(File).where(
                and_(
                    File.is_trashed == True,
                    File.trashed_at <= threshold,
                )
            )
        )
        items = list(result.scalars().all())

        total_freed = 0
        owners_freed: dict[uuid.UUID, int] = {}

        for item in items:
            if not item.is_folder:
                total_freed += item.size
                owners_freed[item.owner_id] = owners_freed.get(item.owner_id, 0) + item.size
                if item.storage_key:
                    try:
                        self.storage.delete_file(item.storage_key)
                    except Exception:
                        pass
            await self.db.delete(item)

        # Update owner storage
        for uid, freed in owners_freed.items():
            user = await self.db.get(User, uid)
            if user:
                user.storage_used = max(0, user.storage_used - freed)

        await self.db.flush()
        return total_freed
