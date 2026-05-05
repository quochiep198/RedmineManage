from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DashboardHealthSnapshot(Base):
    __tablename__ = "dashboard_health_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    connection_id: Mapped[int] = mapped_column(ForeignKey("redmine_connections.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    health_score: Mapped[float] = mapped_column(Float)
    health_status: Mapped[str] = mapped_column(String(20), index=True)
    metric_scores_json: Mapped[dict] = mapped_column(JSON)
    metric_values_json: Mapped[dict] = mapped_column(JSON)
    main_risk_drivers_json: Mapped[list[dict]] = mapped_column(JSON)
    warnings_json: Mapped[list[dict]] = mapped_column(JSON)
    suggested_actions_json: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
