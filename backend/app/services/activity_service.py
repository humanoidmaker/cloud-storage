import json
import uuid
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.file import File
from app.models.user import User


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_activity(
        self,
        user_id: uuid.UUID,
        action: str,
        file_id: uuid.UUID | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> ActivityLog:
        """Log a user activity."""
        entry = ActivityLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            file_id=file_id,
            details_json=json.dumps(details) if details else None,
            ip_address=ip_address,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_user_activity(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """Get activity logs for a specific user."""
        conditions = [ActivityLog.user_id == user_id]
        if file_id:
            conditions.append(ActivityLog.file_id == file_id)

        base_q = select(ActivityLog).where(and_(*conditions))

        count_q = select(func.count()).select_from(base_q.subquery())
        result = await self.db.execute(count_q)
        total = result.scalar() or 0

        base_q = base_q.order_by(ActivityLog.created_at.desc())
        offset = (page - 1) * page_size
        base_q = base_q.offset(offset).limit(page_size)

        result = await self.db.execute(base_q)
        logs = list(result.scalars().all())

        items = []
        for log in logs:
            item = {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "action": log.action,
                "file_id": str(log.file_id) if log.file_id else None,
                "details_json": log.details_json,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            items.append(item)

        return items, total

    async def get_global_activity(
        self,
        user_id: uuid.UUID | None = None,
        action: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        """Get global activity logs with optional filters (admin only)."""
        conditions: list = []
        if user_id:
            conditions.append(ActivityLog.user_id == user_id)
        if action:
            conditions.append(ActivityLog.action == action)
        if date_from:
            conditions.append(ActivityLog.created_at >= date_from)
        if date_to:
            conditions.append(ActivityLog.created_at <= date_to)

        base_q = select(ActivityLog)
        if conditions:
            base_q = base_q.where(and_(*conditions))

        count_q = select(func.count()).select_from(base_q.subquery())
        result = await self.db.execute(count_q)
        total = result.scalar() or 0

        base_q = base_q.order_by(ActivityLog.created_at.desc())
        offset = (page - 1) * page_size
        base_q = base_q.offset(offset).limit(page_size)

        result = await self.db.execute(base_q)
        logs = list(result.scalars().all())

        items = []
        for log in logs:
            # Fetch user info
            user = await self.db.get(User, log.user_id)
            # Fetch file info
            file_name = None
            if log.file_id:
                f = await self.db.get(File, log.file_id)
                file_name = f.name if f else None

            item = {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "user_name": user.name if user else None,
                "user_email": user.email if user else None,
                "action": log.action,
                "file_id": str(log.file_id) if log.file_id else None,
                "file_name": file_name,
                "details_json": log.details_json,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            items.append(item)

        return items, total

    async def export_activity_csv(
        self,
        user_id: uuid.UUID | None = None,
        action: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> str:
        """Export activity logs as CSV string."""
        items, _ = await self.get_global_activity(
            user_id=user_id,
            action=action,
            date_from=date_from,
            date_to=date_to,
            page=1,
            page_size=10000,
        )

        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "user_id", "user_name", "user_email", "action", "file_id", "file_name", "ip_address", "created_at"])

        for item in items:
            writer.writerow([
                item.get("id"),
                item.get("user_id"),
                item.get("user_name"),
                item.get("user_email"),
                item.get("action"),
                item.get("file_id"),
                item.get("file_name"),
                item.get("ip_address"),
                item.get("created_at"),
            ])

        return output.getvalue()
