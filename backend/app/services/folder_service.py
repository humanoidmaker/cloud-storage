import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.utils.file_utils import sanitize_filename


class FolderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_folder(
        self, owner_id: uuid.UUID, name: str, parent_folder_id: uuid.UUID | None = None
    ) -> File:
        """Create a new folder."""
        name = sanitize_filename(name)

        # Check for duplicate names in same parent
        existing = await self._get_sibling_names(owner_id, parent_folder_id)
        if name in existing:
            raise HTTPException(status_code=409, detail="A folder with this name already exists")

        # Validate parent folder if specified
        if parent_folder_id:
            parent = await self.db.get(File, parent_folder_id)
            if not parent or not parent.is_folder or parent.owner_id != owner_id:
                raise HTTPException(status_code=400, detail="Invalid parent folder")

        folder = File(
            id=uuid.uuid4(),
            name=name,
            owner_id=owner_id,
            parent_folder_id=parent_folder_id,
            is_folder=True,
            size=0,
        )
        self.db.add(folder)
        await self.db.flush()
        return folder

    async def get_folder_contents(
        self,
        owner_id: uuid.UUID,
        folder_id: uuid.UUID | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[File], int]:
        """List contents of a folder (files and subfolders)."""
        if folder_id:
            folder = await self.db.get(File, folder_id)
            if not folder or not folder.is_folder:
                raise HTTPException(status_code=404, detail="Folder not found")

        base_query = select(File).where(
            and_(
                File.owner_id == owner_id,
                File.parent_folder_id == folder_id,
                File.is_trashed == False,
            )
        )

        # Count
        count_query = select(func.count()).select_from(base_query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        # Sort: folders first, then by specified field
        sort_col = getattr(File, sort_by, File.name)
        if sort_order == "desc":
            base_query = base_query.order_by(File.is_folder.desc(), sort_col.desc())
        else:
            base_query = base_query.order_by(File.is_folder.desc(), sort_col.asc())

        offset = (page - 1) * page_size
        base_query = base_query.offset(offset).limit(page_size)

        result = await self.db.execute(base_query)
        items = list(result.scalars().all())
        return items, total

    async def rename_folder(self, folder_id: uuid.UUID, owner_id: uuid.UUID, name: str) -> File:
        """Rename a folder."""
        folder = await self.db.get(File, folder_id)
        if not folder or not folder.is_folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        if folder.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        name = sanitize_filename(name)
        existing = await self._get_sibling_names(owner_id, folder.parent_folder_id, exclude_id=folder_id)
        if name in existing:
            raise HTTPException(status_code=409, detail="A folder with this name already exists")

        folder.name = name
        await self.db.flush()
        return folder

    async def delete_folder(self, folder_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        """Recursively soft-delete a folder and all its contents."""
        folder = await self.db.get(File, folder_id)
        if not folder or not folder.is_folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        if folder.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        await self._recursive_trash(folder_id, owner_id)

    async def _recursive_trash(self, folder_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        """Iteratively trash a folder and all descendants."""
        now = datetime.now(timezone.utc)
        queue = [folder_id]

        while queue:
            current_id = queue.pop(0)
            # Trash the current item
            item = await self.db.get(File, current_id)
            if item:
                item.is_trashed = True
                item.trashed_at = now

            # Find all children
            result = await self.db.execute(
                select(File.id).where(
                    and_(
                        File.parent_folder_id == current_id,
                        File.owner_id == owner_id,
                        File.is_trashed == False,
                    )
                )
            )
            child_ids = [row[0] for row in result.all()]
            queue.extend(child_ids)

        await self.db.flush()

    async def move_folder(
        self, folder_id: uuid.UUID, owner_id: uuid.UUID, target_folder_id: uuid.UUID | None
    ) -> File:
        """Move a folder to a new parent."""
        folder = await self.db.get(File, folder_id)
        if not folder or not folder.is_folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        if folder.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        # Can't move into self
        if target_folder_id and folder_id == target_folder_id:
            raise HTTPException(status_code=400, detail="Cannot move a folder into itself")

        # Can't move into a child
        if target_folder_id and await self._is_descendant(folder_id, target_folder_id):
            raise HTTPException(status_code=400, detail="Cannot move a folder into its own descendant")

        # Validate target
        if target_folder_id:
            target = await self.db.get(File, target_folder_id)
            if not target or not target.is_folder:
                raise HTTPException(status_code=400, detail="Target folder not found")

        folder.parent_folder_id = target_folder_id
        await self.db.flush()
        return folder

    async def get_breadcrumb(self, folder_id: uuid.UUID | None, owner_id: uuid.UUID) -> list[dict]:
        """Get breadcrumb path from root to the given folder."""
        breadcrumbs = [{"id": None, "name": "Root"}]
        if folder_id is None:
            return breadcrumbs

        path: list[dict] = []
        current_id = folder_id
        visited: set[uuid.UUID] = set()

        while current_id:
            if current_id in visited:
                break
            visited.add(current_id)
            folder = await self.db.get(File, current_id)
            if not folder:
                break
            path.append({"id": str(folder.id), "name": folder.name})
            current_id = folder.parent_folder_id  # type: ignore[assignment]

        path.reverse()
        breadcrumbs.extend(path)
        return breadcrumbs

    async def get_folder_tree(self, owner_id: uuid.UUID) -> list[dict]:
        """Get the full folder tree for a user."""
        result = await self.db.execute(
            select(File).where(
                and_(
                    File.owner_id == owner_id,
                    File.is_folder == True,
                    File.is_trashed == False,
                )
            )
        )
        folders = list(result.scalars().all())

        # Build tree
        folder_map: dict[uuid.UUID, dict] = {}
        for f in folders:
            folder_map[f.id] = {"id": str(f.id), "name": f.name, "children": []}

        roots: list[dict] = []
        for f in folders:
            node = folder_map[f.id]
            if f.parent_folder_id and f.parent_folder_id in folder_map:
                folder_map[f.parent_folder_id]["children"].append(node)
            else:
                roots.append(node)

        return roots

    async def calculate_folder_size(self, folder_id: uuid.UUID) -> int:
        """Calculate total size of all files in a folder (recursive)."""
        total = 0
        queue = [folder_id]

        while queue:
            current_id = queue.pop(0)
            # Sum file sizes
            result = await self.db.execute(
                select(func.coalesce(func.sum(File.size), 0)).where(
                    and_(
                        File.parent_folder_id == current_id,
                        File.is_folder == False,
                        File.is_trashed == False,
                    )
                )
            )
            total += result.scalar() or 0

            # Find subfolders
            result = await self.db.execute(
                select(File.id).where(
                    and_(
                        File.parent_folder_id == current_id,
                        File.is_folder == True,
                        File.is_trashed == False,
                    )
                )
            )
            queue.extend([row[0] for row in result.all()])

        return total

    async def _get_sibling_names(
        self, owner_id: uuid.UUID, parent_folder_id: uuid.UUID | None, exclude_id: uuid.UUID | None = None
    ) -> list[str]:
        """Get names of all items in the same folder."""
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
        """Check if potential_descendant_id is within the subtree of ancestor_id."""
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
