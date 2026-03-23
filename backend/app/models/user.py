import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")  # superadmin, admin, user
    storage_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    storage_quota: Mapped[int] = mapped_column(BigInteger, nullable=False, default=5368709120)  # 5GB
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    files: Mapped[list["File"]] = relationship("File", back_populates="owner", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
    stars: Mapped[list["Star"]] = relationship("Star", back_populates="user", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
    tags: Mapped[list["Tag"]] = relationship("Tag", back_populates="user", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
    activity_logs: Mapped[list["ActivityLog"]] = relationship("ActivityLog", back_populates="user", lazy="selectin")  # type: ignore[name-defined] # noqa: F821
