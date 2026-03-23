import secrets
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.models.share import Share
from app.models.user import User
from app.utils.hashing import hash_password, verify_password


class ShareService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_share(
        self,
        file_id: uuid.UUID,
        shared_by: uuid.UUID,
        shared_with_email: str | None = None,
        permission: str = "view",
        create_link: bool = False,
        password: str | None = None,
        expires_at: datetime | None = None,
    ) -> Share:
        """Create a share for a file or generate a share link."""
        # Verify the file exists and the user owns it
        file = await self.db.get(File, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        if file.owner_id != shared_by:
            raise HTTPException(status_code=403, detail="You can only share files you own")

        shared_with_user_id = None
        share_token = None

        if shared_with_email:
            # Find the user by email
            result = await self.db.execute(
                select(User).where(User.email == shared_with_email)
            )
            target_user = result.scalar_one_or_none()
            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            shared_with_user_id = target_user.id

            # Check for existing share; update instead of duplicating
            existing = await self.db.execute(
                select(Share).where(
                    and_(
                        Share.file_id == file_id,
                        Share.shared_with_user_id == shared_with_user_id,
                    )
                )
            )
            existing_share = existing.scalar_one_or_none()
            if existing_share:
                existing_share.permission = permission
                if expires_at is not None:
                    existing_share.expires_at = expires_at
                await self.db.flush()
                return existing_share

        if create_link:
            share_token = secrets.token_urlsafe(32)

        password_hash = hash_password(password) if password else None

        share = Share(
            id=uuid.uuid4(),
            file_id=file_id,
            shared_by=shared_by,
            shared_with_user_id=shared_with_user_id,
            shared_with_email=shared_with_email,
            share_token=share_token,
            permission=permission,
            password_hash=password_hash,
            expires_at=expires_at,
        )
        self.db.add(share)
        await self.db.flush()
        return share

    async def validate_share_token(self, token: str, password: str | None = None) -> Share:
        """Validate a share link token. Checks expiry and password."""
        result = await self.db.execute(
            select(Share).where(Share.share_token == token)
        )
        share = result.scalar_one_or_none()
        if not share:
            raise HTTPException(status_code=404, detail="Share link not found")

        # Check expiry
        if share.expires_at:
            expires = share.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                raise HTTPException(status_code=410, detail="Share link has expired")

        # Check password
        if share.password_hash:
            if not password:
                raise HTTPException(status_code=403, detail="Password required")
            if not verify_password(password, share.password_hash):
                raise HTTPException(status_code=403, detail="Incorrect password")

        return share

    async def list_shares_for_file(self, file_id: uuid.UUID, user_id: uuid.UUID) -> list[Share]:
        """List all shares for a file. Only owner can see all shares."""
        file = await self.db.get(File, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        result = await self.db.execute(
            select(Share).where(Share.file_id == file_id)
        )
        return list(result.scalars().all())

    async def list_shared_with_user(self, user_id: uuid.UUID) -> list[Share]:
        """List all files shared with a specific user."""
        result = await self.db.execute(
            select(Share).where(Share.shared_with_user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_share_permission(
        self, share_id: uuid.UUID, user_id: uuid.UUID, permission: str
    ) -> Share:
        """Update share permission. Only the file owner can update."""
        share = await self.db.get(Share, share_id)
        if not share:
            raise HTTPException(status_code=404, detail="Share not found")
        if share.shared_by != user_id:
            raise HTTPException(status_code=403, detail="Only the file owner can update share permissions")

        share.permission = permission
        await self.db.flush()
        return share

    async def revoke_share(self, share_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Revoke (delete) a share."""
        share = await self.db.get(Share, share_id)
        if not share:
            raise HTTPException(status_code=404, detail="Share not found")
        if share.shared_by != user_id:
            raise HTTPException(status_code=403, detail="Only the file owner can revoke shares")

        await self.db.delete(share)
        await self.db.flush()

    async def get_user_shares_for_file(
        self, file_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[dict]:
        """Get share info for permission checking."""
        result = await self.db.execute(
            select(Share).where(Share.file_id == file_id)
        )
        shares = result.scalars().all()
        return [
            {
                "shared_with_user_id": str(s.shared_with_user_id) if s.shared_with_user_id else None,
                "permission": s.permission,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            }
            for s in shares
        ]
