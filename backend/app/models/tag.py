import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#3B82F6")  # hex color
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="tags", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
    file_tags: Mapped[list["FileTag"]] = relationship("FileTag", back_populates="tag", lazy="selectin")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_tag_name"),)
