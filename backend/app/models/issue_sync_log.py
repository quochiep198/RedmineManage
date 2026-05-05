from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IssueSyncLog(Base):
    __tablename__ = "issue_sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("redmine_connections.id"),
        index=True,
        nullable=True,
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"),
        index=True,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20))
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_synced: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime] = mapped_column(DateTime)
