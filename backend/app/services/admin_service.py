import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.file import File
from app.models.share import Share
from app.models.storage_stats import StorageStats
from app.models.user import User
from app.utils.hashing import hash_password


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self) -> dict:
        """Get dashboard overview statistics."""
        # Total users
        result = await self.db.execute(select(func.count()).select_from(User))
        total_users = result.scalar() or 0

        # Active users (logged in within 30 days) - approximate via activity log
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        result = await self.db.execute(
            select(func.count(func.distinct(ActivityLog.user_id))).where(
                ActivityLog.created_at >= thirty_days_ago
            )
        )
        active_users = result.scalar() or 0

        # Total storage
        result = await self.db.execute(
            select(func.coalesce(func.sum(User.storage_used), 0))
        )
        total_storage = result.scalar() or 0

        # Total files
        result = await self.db.execute(
            select(func.count()).select_from(
                select(File).where(File.is_folder == False).subquery()
            )
        )
        total_files = result.scalar() or 0

        # Total shares
        result = await self.db.execute(select(func.count()).select_from(Share))
        total_shares = result.scalar() or 0

        # Recent activity (last 50)
        result = await self.db.execute(
            select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(50)
        )
        recent = []
        for log in result.scalars().all():
            user = await self.db.get(User, log.user_id)
            recent.append({
                "id": str(log.id),
                "user_name": user.name if user else "Unknown",
                "action": log.action,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            })

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_storage_used": total_storage,
            "total_files": total_files,
            "total_shares": total_shares,
            "recent_activity": recent,
            "user_growth": [],
            "storage_trend": [],
        }

    async def list_users(
        self,
        search: str | None = None,
        role: str | None = None,
        status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        """List users with search, filter, sort, pagination."""
        conditions: list = []
        if search:
            conditions.append(
                (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
            )
        if role:
            conditions.append(User.role == role)
        if status == "active":
            conditions.append(User.is_active == True)
        elif status == "inactive":
            conditions.append(User.is_active == False)

        base_q = select(User)
        if conditions:
            base_q = base_q.where(and_(*conditions))

        count_q = select(func.count()).select_from(base_q.subquery())
        result = await self.db.execute(count_q)
        total = result.scalar() or 0

        sort_col = getattr(User, sort_by, User.created_at)
        if sort_order == "desc":
            base_q = base_q.order_by(sort_col.desc())
        else:
            base_q = base_q.order_by(sort_col.asc())

        offset = (page - 1) * page_size
        base_q = base_q.offset(offset).limit(page_size)

        result = await self.db.execute(base_q)
        users = list(result.scalars().all())
        return users, total

    async def create_user(
        self,
        email: str,
        name: str,
        password: str,
        role: str = "user",
        storage_quota: int = 5368709120,
    ) -> User:
        """Create a new user (admin action)."""
        # Check duplicate email
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            id=uuid.uuid4(),
            email=email,
            name=name,
            password_hash=hash_password(password),
            role=role,
            storage_quota=storage_quota,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(
        self, user_id: uuid.UUID, name: str | None = None, email: str | None = None, role: str | None = None
    ) -> User:
        """Update user fields."""
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if name:
            user.name = name
        if email:
            user.email = email
        if role:
            user.role = role
        await self.db.flush()
        return user

    async def update_quota(self, user_id: uuid.UUID, storage_quota: int) -> User:
        """Update user storage quota."""
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.storage_quota = storage_quota
        await self.db.flush()
        return user

    async def deactivate_user(self, user_id: uuid.UUID, admin_id: uuid.UUID) -> User:
        """Deactivate a user account."""
        if user_id == admin_id:
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = False
        await self.db.flush()
        return user

    async def activate_user(self, user_id: uuid.UUID) -> User:
        """Reactivate a user account."""
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = True
        await self.db.flush()
        return user

    async def reset_password(self, user_id: uuid.UUID) -> str:
        """Reset user password and return temporary password."""
        import secrets
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        temp_password = secrets.token_urlsafe(12)
        user.password_hash = hash_password(temp_password)
        await self.db.flush()
        return temp_password

    async def delete_user(
        self, user_id: uuid.UUID, admin_id: uuid.UUID, transfer_to_user_id: uuid.UUID | None = None
    ) -> None:
        """Delete a user, optionally transferring their files."""
        if user_id == admin_id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if transfer_to_user_id:
            # Transfer files
            result = await self.db.execute(
                select(File).where(File.owner_id == user_id)
            )
            files = list(result.scalars().all())
            for f in files:
                f.owner_id = transfer_to_user_id

        await self.db.delete(user)
        await self.db.flush()

    async def get_storage_breakdown(self) -> list[dict]:
        """Get per-user storage breakdown."""
        result = await self.db.execute(select(User))
        users = list(result.scalars().all())

        breakdown = []
        for user in users:
            # Count files and folders
            file_count_q = select(func.count()).select_from(
                select(File).where(
                    and_(File.owner_id == user.id, File.is_folder == False)
                ).subquery()
            )
            folder_count_q = select(func.count()).select_from(
                select(File).where(
                    and_(File.owner_id == user.id, File.is_folder == True)
                ).subquery()
            )

            fc_result = await self.db.execute(file_count_q)
            file_count = fc_result.scalar() or 0

            fld_result = await self.db.execute(folder_count_q)
            folder_count = fld_result.scalar() or 0

            utilization = 0.0
            if user.storage_quota > 0:
                utilization = round((user.storage_used / user.storage_quota) * 100, 1)

            breakdown.append({
                "user_id": str(user.id),
                "user_name": user.name,
                "user_email": user.email,
                "files_count": file_count,
                "folders_count": folder_count,
                "storage_used": user.storage_used,
                "storage_quota": user.storage_quota,
                "utilization_percent": utilization,
            })

        return breakdown

    async def get_top_consumers(self, limit: int = 10) -> list[dict]:
        """Get top storage consumers."""
        result = await self.db.execute(
            select(User).order_by(User.storage_used.desc()).limit(limit)
        )
        users = list(result.scalars().all())
        return [
            {
                "user_id": str(u.id),
                "user_name": u.name,
                "user_email": u.email,
                "storage_used": u.storage_used,
                "storage_quota": u.storage_quota,
            }
            for u in users
        ]

    async def bulk_update_quota(self, user_ids: list[uuid.UUID], storage_quota: int) -> int:
        """Update quota for multiple users. Returns count updated."""
        count = 0
        for uid in user_ids:
            user = await self.db.get(User, uid)
            if user:
                user.storage_quota = storage_quota
                count += 1
        await self.db.flush()
        return count
