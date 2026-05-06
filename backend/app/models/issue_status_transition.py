from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IssueStatusTransition(Base):
    __tablename__ = "issue_status_transitions"
    __table_args__ = (
        UniqueConstraint(
            "connection_id",
            "redmine_issue_id",
            "from_status_id",
            "to_status_id",
            "changed_on",
            name="uq_issue_status_transitions_event",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    connection_id: Mapped[int] = mapped_column(ForeignKey("redmine_connections.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    redmine_issue_id: Mapped[int] = mapped_column(Integer, index=True)
    from_status_id: Mapped[int] = mapped_column(Integer, index=True)
    to_status_id: Mapped[int] = mapped_column(Integer, index=True)
    changed_on: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
