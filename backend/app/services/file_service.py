import io
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.file import File
from app.models.user import User
from app.services.storage_service import StorageService
from app.utils.file_utils import (
    calculate_content_hash,
    detect_mime_type,
    generate_unique_filename,
    sanitize_filename,
    validate_extension,
)


class FileService:
    def __init__(self, db: AsyncSession, storage: StorageService | None = None):
        self.db = db
        self.storage = storage or StorageService()

    async def create_file(
        self,
        owner_id: uuid.UUID,
        filename: str,
        file_content: bytes,
        parent_folder_id: uuid.UUID | None = None,
        content_type: str | None = None,
    ) -> File:
        """Create a new file: validate, upload to storage, create DB record."""
        # Sanitize filename
        filename = sanitize_filename(filename)

        # Validate extension
        allowed = settings.allowed_extensions_list
        if not validate_extension(filename, allowed):
            raise HTTPException(status_code=400, detail=f"File extension not allowed")

        # Check file size
        file_size = len(file_content)
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds maximum upload size")

        # Check quota
        user = await self.db.get(User, owner_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if user.storage_quota > 0 and (user.storage_used + file_size) > user.storage_quota:
            raise HTTPException(status_code=413, detail="Upload would exceed storage quota")

        # Validate parent folder if specified
        if parent_folder_id:
            parent = await self.db.get(File, parent_folder_id)
            if not parent or not parent.is_folder or parent.owner_id != owner_id:
                raise HTTPException(status_code=400, detail="Invalid parent folder")

        # Detect MIME type
        mime_type = detect_mime_type(file_content, filename) if not content_type else content_type

        # Calculate content hash
        content_hash = calculate_content_hash(file_content)

        # Handle duplicate filenames
        existing_names = await self._get_sibling_names(owner_id, parent_folder_id)
        filename = generate_unique_filename(filename, existing_names)

        # Upload to storage
        file_id = uuid.uuid4()
        storage_key = f"{owner_id}/{file_id}/{filename}"
        self.storage.upload_file(
            file_content,
            storage_key,
            content_type=mime_type,
            metadata={"content_hash": content_hash},
        )

        # Create DB record
        file_record = File(
            id=file_id,
            name=filename,
            mime_type=mime_type,
            size=file_size,
            storage_key=storage_key,
            owner_id=owner_id,
            parent_folder_id=parent_folder_id,
            is_folder=False,
            content_hash=content_hash,
        )
        self.db.add(file_record)

        # Update user storage
        user.storage_used += file_size
        await self.db.flush()

        return file_record

    async def get_file(self, file_id: uuid.UUID) -> File:
        """Get a file by ID. Raises 404 if not found."""
        file = await self.db.get(File, file_id)
        if file is None:
            raise HTTPException(status_code=404, detail="File not found")
        return file

    async def update_file(self, file_id: uuid.UUID, owner_id: uuid.UUID, name: str | None = None) -> File:
        """Update file metadata (rename)."""
        file = await self.get_file(file_id)
        if file.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        if name:
            name = sanitize_filename(name)
            # Check for duplicates in same folder
            existing_names = await self._get_sibling_names(owner_id, file.parent_folder_id, exclude_id=file_id)
            if name in existing_names:
                raise HTTPException(status_code=409, detail="A file with this name already exists in this folder")
            file.name = name

        await self.db.flush()
        return file

    async def move_file(self, file_id: uuid.UUID, owner_id: uuid.UUID, target_folder_id: uuid.UUID | None) -> File:
        """Move a file to a different folder."""
        file = await self.get_file(file_id)
        if file.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        # Can't move file into itself (only relevant for folders)
        if file.is_folder and target_folder_id:
            if file_id == target_folder_id:
                raise HTTPException(status_code=400, detail="Cannot move a folder into itself")
            # Check if target is a descendant of the folder
            if await self._is_descendant(file_id, target_folder_id):
                raise HTTPException(status_code=400, detail="Cannot move a folder into its own descendant")

        # Validate target folder
        if target_folder_id:
            target = await self.db.get(File, target_folder_id)
            if not target or not target.is_folder:
                raise HTTPException(status_code=400, detail="Target folder not found")

        # Handle name conflicts
        existing_names = await self._get_sibling_names(owner_id, target_folder_id, exclude_id=file_id)
        if file.name in existing_names:
            file.name = generate_unique_filename(file.name, existing_names)

        file.parent_folder_id = target_folder_id
        await self.db.flush()
        return file

    async def copy_file(
        self, file_id: uuid.UUID, owner_id: uuid.UUID, target_folder_id: uuid.UUID | None = None, new_name: str | None = None
    ) -> File:
        """Copy a file: new DB entry + new storage key."""
        original = await self.get_file(file_id)

        # Handle name
        name = new_name or original.name
        name = sanitize_filename(name)
        existing_names = await self._get_sibling_names(owner_id, target_folder_id)
        name = generate_unique_filename(name, existing_names)

        # Copy in storage
        new_file_id = uuid.uuid4()
        new_storage_key = f"{owner_id}/{new_file_id}/{name}"
        if original.storage_key:
            self.storage.copy_object(original.storage_key, new_storage_key)

        # Create new DB record
        new_file = File(
            id=new_file_id,
            name=name,
            mime_type=original.mime_type,
            size=original.size,
            storage_key=new_storage_key,
            owner_id=owner_id,
            parent_folder_id=target_folder_id,
            is_folder=False,
            content_hash=original.content_hash,
        )
        self.db.add(new_file)

        # Update user storage
        user = await self.db.get(User, owner_id)
        if user:
            user.storage_used += original.size

        await self.db.flush()
        return new_file

    async def soft_delete(self, file_id: uuid.UUID, owner_id: uuid.UUID) -> File:
        """Soft delete (move to trash)."""
        file = await self.get_file(file_id)
        if file.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        file.is_trashed = True
        file.trashed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return file

    async def list_files(
        self,
        owner_id: uuid.UUID,
        parent_folder_id: uuid.UUID | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[File], int]:
        """List files in a folder with pagination and sorting."""
        base_query = select(File).where(
            and_(
                File.owner_id == owner_id,
                File.parent_folder_id == parent_folder_id,
                File.is_trashed == False,
            )
        )

        # Count
        count_query = select(func.count()).select_from(base_query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        # Sort
        sort_column = getattr(File, sort_by, File.name)
        if sort_order == "desc":
            base_query = base_query.order_by(sort_column.desc())
        else:
            base_query = base_query.order_by(sort_column.asc())

        # Paginate
        offset = (page - 1) * page_size
        base_query = base_query.offset(offset).limit(page_size)

        result = await self.db.execute(base_query)
        files = list(result.scalars().all())

        return files, total

    async def bulk_delete(self, file_ids: list[uuid.UUID], owner_id: uuid.UUID) -> int:
        """Bulk soft delete multiple files."""
        count = 0
        for fid in file_ids:
            try:
                await self.soft_delete(fid, owner_id)
                count += 1
            except HTTPException:
                continue
        return count

    async def get_download_url(self, file_id: uuid.UUID) -> str:
        """Get presigned download URL for a file."""
        file = await self.get_file(file_id)
        if not file.storage_key:
            raise HTTPException(status_code=400, detail="File has no storage key")
        return self.storage.get_presigned_download_url(file.storage_key)

    async def check_deduplication(self, content_hash: str, owner_id: uuid.UUID) -> File | None:
        """Check if a file with the same hash already exists for this user."""
        query = select(File).where(
            and_(
                File.content_hash == content_hash,
                File.owner_id == owner_id,
                File.is_trashed == False,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_sibling_names(
        self, owner_id: uuid.UUID, parent_folder_id: uuid.UUID | None, exclude_id: uuid.UUID | None = None
    ) -> list[str]:
        """Get names of all files in the same folder."""
        query = select(File.name).where(
            and_(
                File.owner_id == owner_id,
                File.parent_folder_id == parent_folder_id,
                File.is_trashed == False,
            )
        )
        if exclude_id:
            query = query.where(File.id != exclude_id)
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]

    async def _is_descendant(self, ancestor_id: uuid.UUID, potential_descendant_id: uuid.UUID) -> bool:
        """Check if potential_descendant_id is a descendant of ancestor_id."""
        current_id = potential_descendant_id
        visited: set[uuid.UUID] = set()
        while current_id:
            if current_id in visited:
                break
            visited.add(current_id)
            if current_id == ancestor_id:
                return True
            folder = await self.db.get(File, current_id)
            if not folder:
                break
            current_id = folder.parent_folder_id  # type: ignore[assignment]
        return False
