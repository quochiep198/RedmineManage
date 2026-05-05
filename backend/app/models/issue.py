from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("connection_id", "redmine_issue_id", name="uq_issues_conn_redmine_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    connection_id: Mapped[int] = mapped_column(ForeignKey("redmine_connections.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    redmine_issue_id: Mapped[int] = mapped_column(index=True)
    tracker_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tracker_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    priority_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    author_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    assignee_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    done_ratio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    spent_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    redmine_created_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    redmine_updated_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    raw_data_json: Mapped[dict] = mapped_column(JSON)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
