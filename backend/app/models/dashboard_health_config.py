from datetime import datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DashboardHealthConfig(Base):
    __tablename__ = "dashboard_health_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(50), default="global", unique=True, index=True)
    closed_status_ids_json: Mapped[list[int]] = mapped_column(JSON)
    bug_tracker_names_json: Mapped[list[str]] = mapped_column(JSON)
    metric_thresholds_json: Mapped[dict] = mapped_column(JSON)
    metric_weights_json: Mapped[dict] = mapped_column(JSON)
    health_status_thresholds_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
