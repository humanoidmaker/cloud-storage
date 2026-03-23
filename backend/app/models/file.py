import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    storage_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # None for folders
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    parent_folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=True, index=True
    )
    is_folder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256
    thumbnail_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_trashed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    trashed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship("User", back_populates="files", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
    parent_folder: Mapped["File | None"] = relationship("File", remote_side=[id], lazy="selectin")
    versions: Mapped[list["FileVersion"]] = relationship("FileVersion", back_populates="file", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
    shares: Mapped[list["Share"]] = relationship("Share", back_populates="file", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
    stars: Mapped[list["Star"]] = relationship("Star", back_populates="file", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
    file_tags: Mapped[list["FileTag"]] = relationship("FileTag", back_populates="file", lazy="selectin")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (
        Index("ix_files_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_files_owner_parent", "owner_id", "parent_folder_id"),
    )
