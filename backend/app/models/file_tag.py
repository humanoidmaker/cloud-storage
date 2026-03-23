import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FileTag(Base):
    __tablename__ = "file_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False, index=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    file: Mapped["File"] = relationship("File", back_populates="file_tags", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
    tag: Mapped["Tag"] = relationship("Tag", back_populates="file_tags", lazy="selectin")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (UniqueConstraint("file_id", "tag_id", name="uq_file_tag"),)
