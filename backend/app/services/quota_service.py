import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.models.user import User


class QuotaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_storage_used(self, user_id: uuid.UUID) -> int:
        """Calculate total storage used by a user (includes trashed, excludes permanently deleted)."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(File.size), 0)).where(
                and_(
                    File.owner_id == user_id,
                    File.is_folder == False,
                )
            )
        )
        return result.scalar() or 0

    async def check_upload_allowed(self, user_id: uuid.UUID, file_size: int) -> bool:
        """Check if uploading a file of the given size would exceed the user's quota."""
        user = await self.db.get(User, user_id)
        if not user:
            return False

        # Unlimited quota (0 or None)
        if not user.storage_quota or user.storage_quota == 0:
            return True

        return (user.storage_used + file_size) <= user.storage_quota

    async def recalculate_quota(self, user_id: uuid.UUID) -> int:
        """Recalculate and update the user's storage_used field."""
        actual_used = await self.calculate_storage_used(user_id)
        user = await self.db.get(User, user_id)
        if user:
            user.storage_used = actual_used
            await self.db.flush()
        return actual_used

    async def recalculate_all_quotas(self) -> int:
        """Recalculate storage for all users. Returns number of users updated."""
        result = await self.db.execute(select(User.id))
        user_ids = [row[0] for row in result.all()]

        count = 0
        for uid in user_ids:
            await self.recalculate_quota(uid)
            count += 1

        return count

    async def get_storage_breakdown(self, user_id: uuid.UUID) -> dict[str, int]:
        """Get storage breakdown by file type category."""
        from app.utils.file_utils import get_file_category

        result = await self.db.execute(
            select(File.mime_type, func.sum(File.size)).where(
                and_(
                    File.owner_id == user_id,
                    File.is_folder == False,
                )
            ).group_by(File.mime_type)
        )

        breakdown: dict[str, int] = {
            "images": 0,
            "documents": 0,
            "videos": 0,
            "audio": 0,
            "other": 0,
        }

        for mime_type, size in result.all():
            category = get_file_category(mime_type or "")
            key = f"{category}s" if category != "other" else "other"
            if key not in breakdown:
                key = "other"
            breakdown[key] += size or 0

        breakdown["total"] = sum(breakdown.values())
        return breakdown
