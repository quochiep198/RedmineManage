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
    score: float
    max_score: int
    status: str
    trend_value: float | None
    trend_direction: str


class DashboardMetricItem(BaseModel):
    code: str
    label: str
    score: int
    max_score: int
    value: float | None
    value_display: str
    benchmark: str
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


class DashboardEarlyWarningItem(BaseModel):
    code: str
    level: str
    message: str
    drilldown_risk_type: str | None = None


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
    metrics: list[DashboardMetricItem]
    main_risk_drivers: list[DashboardRiskDriverItem]
    suggested_actions: list[DashboardSuggestedActionItem]
    early_warnings: list[DashboardEarlyWarningItem]
    health_trend: list[DashboardHealthTrendItem]
