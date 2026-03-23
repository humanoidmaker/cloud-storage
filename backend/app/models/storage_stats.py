import uuid
from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StorageStats(Base):
    __tablename__ = "storage_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    files_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    folders_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    uploads_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    downloads_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
