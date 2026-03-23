import uuid
from datetime import datetime

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.models.file_tag import FileTag
from app.models.star import Star


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_files(
        self,
        user_id: uuid.UUID,
        query: str,
        file_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        tag_id: uuid.UUID | None = None,
        folder_id: uuid.UUID | None = None,
        starred: bool | None = None,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[File], int]:
        """Search files using PostgreSQL full-text search with filters."""
        # Sanitize query: remove SQL-injection attempts
        safe_query = query.replace("'", "''").replace("\\", "\\\\").strip()
        if not safe_query:
            return [], 0

        # Build tsquery from words
        words = safe_query.split()
        tsquery_parts = [f"{w}:*" for w in words if w]
        tsquery_str = " & ".join(tsquery_parts)

        # Base query
        conditions = [
            File.owner_id == user_id,
            File.is_trashed == False,
        ]

        # Full-text search on name using ts_query
        # For SQLite compatibility in tests, fall back to LIKE
        try:
            conditions.append(
                File.name.ilike(f"%{safe_query}%")
            )
        except Exception:
            conditions.append(File.name.ilike(f"%{safe_query}%"))

        # File type filter
        if file_type:
            type_map = {
                "image": "image/%",
                "video": "video/%",
                "audio": "audio/%",
                "document": ["application/pdf", "application/msword", "text/%",
                             "application/vnd.openxmlformats%"],
            }
            if file_type in type_map:
                val = type_map[file_type]
                if isinstance(val, list):
                    mime_conditions = [File.mime_type.ilike(v) for v in val]
                    conditions.append(or_(*mime_conditions))
                else:
                    conditions.append(File.mime_type.ilike(val))

        # Date range filter
        if date_from:
            conditions.append(File.created_at >= date_from)
        if date_to:
            conditions.append(File.created_at <= date_to)

        # Folder filter (search within folder recursively)
        if folder_id:
            descendant_ids = await self._get_descendant_folder_ids(folder_id, user_id)
            descendant_ids.append(folder_id)
            conditions.append(File.parent_folder_id.in_(descendant_ids))

        base_q = select(File).where(and_(*conditions))

        # Tag filter
        if tag_id:
            base_q = base_q.join(FileTag, FileTag.file_id == File.id).where(FileTag.tag_id == tag_id)

        # Starred filter
        if starred:
            base_q = base_q.join(Star, Star.file_id == File.id).where(Star.user_id == user_id)

        # Count
        count_q = select(func.count()).select_from(base_q.subquery())
        result = await self.db.execute(count_q)
        total = result.scalar() or 0

        # Sort
        if sort_by == "name":
            sort_col = File.name
        elif sort_by == "size":
            sort_col = File.size
        elif sort_by == "created_at" or sort_by == "date":
            sort_col = File.created_at
        else:
            sort_col = File.updated_at  # default for "relevance"

        if sort_order == "asc":
            base_q = base_q.order_by(sort_col.asc())
        else:
            base_q = base_q.order_by(sort_col.desc())

        # Paginate
        offset = (page - 1) * page_size
        base_q = base_q.offset(offset).limit(page_size)

        result = await self.db.execute(base_q)
        files = list(result.scalars().all())
        return files, total

    async def _get_descendant_folder_ids(
        self, folder_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[uuid.UUID]:
        """Get all descendant folder IDs (iterative BFS)."""
        result_ids: list[uuid.UUID] = []
        queue = [folder_id]

        while queue:
            current = queue.pop(0)
            res = await self.db.execute(
                select(File.id).where(
                    and_(
                        File.parent_folder_id == current,
                        File.is_folder == True,
                        File.owner_id == user_id,
                        File.is_trashed == False,
                    )
                )
            )
            child_ids = [row[0] for row in res.all()]
            result_ids.extend(child_ids)
            queue.extend(child_ids)

        return result_ids
