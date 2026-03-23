import uuid
from datetime import datetime, timezone

from app.models.activity_log import ActivityLog
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.share import Share
from app.models.tag import Tag
from app.models.user import User
from app.utils.hashing import hash_password


class UserFactory:
    @staticmethod
    def create(
        email: str = "user@example.com",
        name: str = "Test User",
        password: str = "password123",
        role: str = "user",
        storage_quota: int = 5368709120,
        storage_used: int = 0,
        is_active: bool = True,
    ) -> User:
        return User(
            id=uuid.uuid4(),
            email=email,
            name=name,
            password_hash=hash_password(password),
            role=role,
            storage_quota=storage_quota,
            storage_used=storage_used,
            is_active=is_active,
        )


class FileFactory:
    @staticmethod
    def create(
        owner_id: uuid.UUID | None = None,
        name: str = "test_file.txt",
        mime_type: str = "text/plain",
        size: int = 1024,
        storage_key: str | None = None,
        parent_folder_id: uuid.UUID | None = None,
        is_folder: bool = False,
        is_trashed: bool = False,
        content_hash: str | None = None,
    ) -> File:
        file_id = uuid.uuid4()
        if storage_key is None and not is_folder:
            storage_key = f"{owner_id}/{file_id}/{name}"
        return File(
            id=file_id,
            name=name,
            mime_type=mime_type if not is_folder else None,
            size=size if not is_folder else 0,
            storage_key=storage_key if not is_folder else None,
            owner_id=owner_id or uuid.uuid4(),
            parent_folder_id=parent_folder_id,
            is_folder=is_folder,
            content_hash=content_hash,
            is_trashed=is_trashed,
            trashed_at=datetime.now(timezone.utc) if is_trashed else None,
        )


class FolderFactory:
    @staticmethod
    def create(
        owner_id: uuid.UUID | None = None,
        name: str = "test_folder",
        parent_folder_id: uuid.UUID | None = None,
        is_trashed: bool = False,
    ) -> File:
        return FileFactory.create(
            owner_id=owner_id,
            name=name,
            is_folder=True,
            parent_folder_id=parent_folder_id,
            is_trashed=is_trashed,
            size=0,
            mime_type="",
        )


class ShareFactory:
    @staticmethod
    def create(
        file_id: uuid.UUID | None = None,
        shared_by: uuid.UUID | None = None,
        shared_with_user_id: uuid.UUID | None = None,
        share_token: str | None = None,
        permission: str = "view",
        password: str | None = None,
        expires_at: datetime | None = None,
    ) -> Share:
        from app.utils.hashing import hash_password as hp
        return Share(
            id=uuid.uuid4(),
            file_id=file_id or uuid.uuid4(),
            shared_by=shared_by or uuid.uuid4(),
            shared_with_user_id=shared_with_user_id,
            share_token=share_token,
            permission=permission,
            password_hash=hp(password) if password else None,
            expires_at=expires_at,
        )


class TagFactory:
    @staticmethod
    def create(
        user_id: uuid.UUID | None = None,
        name: str = "test_tag",
        color: str = "#3B82F6",
    ) -> Tag:
        return Tag(
            id=uuid.uuid4(),
            name=name,
            user_id=user_id or uuid.uuid4(),
            color=color,
        )


class ActivityLogFactory:
    @staticmethod
    def create(
        user_id: uuid.UUID | None = None,
        action: str = "upload",
        file_id: uuid.UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> ActivityLog:
        return ActivityLog(
            id=uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            action=action,
            file_id=file_id,
            ip_address=ip_address,
        )


class FileVersionFactory:
    @staticmethod
    def create(
        file_id: uuid.UUID | None = None,
        version_number: int = 1,
        storage_key: str = "versions/test_key",
        size: int = 1024,
        content_hash: str | None = None,
        created_by: uuid.UUID | None = None,
    ) -> FileVersion:
        return FileVersion(
            id=uuid.uuid4(),
            file_id=file_id or uuid.uuid4(),
            version_number=version_number,
            storage_key=storage_key,
            size=size,
            content_hash=content_hash,
            created_by=created_by or uuid.uuid4(),
        )
