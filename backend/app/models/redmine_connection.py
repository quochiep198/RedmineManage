from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RedmineConnection(Base):
    __tablename__ = "redmine_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    base_url: Mapped[str] = mapped_column(String(255))
    identifier: Mapped[str] = mapped_column(String(255))
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="untested")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
