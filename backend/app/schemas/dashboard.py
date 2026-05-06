from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class DashboardProjectSummary(BaseModel):
    id: int
    identifier: str
    name: str


class DashboardDateRange(BaseModel):
    from_date: date | None
    to_date: date | None
    field: str


class DashboardHealthSummary(BaseModel):
    status: str
    score_label: str | None
    trend_value: float | None
    trend_direction: str


class DashboardKpiItem(BaseModel):
    code: str
    label: str
    status: str
    summary: str
    drilldown_risk_type: str | None
    details: dict[str, Any]


class DashboardRiskDriverItem(BaseModel):
    risk_type: str
    label: str
    issue_count: int
    issue_ratio: float | None
    dimension: str
    dimension_value: str | None
    drilldown_risk_type: str | None
    drilldown_dimension: str | None
    drilldown_value: str | None


class DashboardSuggestedActionItem(BaseModel):
    risk_type: str
    message: str
    drilldown_risk_type: str | None = None
    drilldown_dimension: str | None = None
    drilldown_value: str | None = None


class DashboardWarningItem(BaseModel):
    code: str
    level: str
    message: str


class DashboardHealthTrendItem(BaseModel):
    snapshot_at: datetime
    label: str
    score: float
    status: str
    trend_value: float | None
    trend_direction: str


class DashboardSummaryResponse(BaseModel):
    project: DashboardProjectSummary | None
    date_range: DashboardDateRange
    last_updated: datetime | None
    total_issues: int
    open_issues: int
    closed_issues: int
    overdue_issues: int
    health_summary: DashboardHealthSummary
    kpi_cards: list[DashboardKpiItem]
    main_risk_drivers: list[DashboardRiskDriverItem]
    suggested_actions: list[DashboardSuggestedActionItem]
    data_quality_warnings: list[DashboardWarningItem]
    health_trend: list[DashboardHealthTrendItem]
