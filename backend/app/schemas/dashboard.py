from datetime import date

from pydantic import BaseModel


class DashboardProjectSummary(BaseModel):
    id: int
    identifier: str
    name: str


class DashboardDateRange(BaseModel):
    from_date: date | None
    to_date: date | None
    field: str


class DashboardStatusItem(BaseModel):
    status_id: int | None
    status_name: str
    count: int


class DashboardPriorityItem(BaseModel):
    priority_id: int | None
    priority_name: str
    count: int


class DashboardAssigneeItem(BaseModel):
    assignee_id: int | None
    assignee_name: str
    count: int


class DashboardTrendItem(BaseModel):
    bucket: str
    label: str
    total_issues: int
    open_issues: int
    closed_issues: int


class DashboardHealthWarning(BaseModel):
    redmine_issue_id: int
    subject: str
    priority_id: int | None
    priority_name: str | None
    status_id: int | None
    status_name: str | None
    due_date: date | None
    warning_type: str


class DashboardProjectHealth(BaseModel):
    health_status: str
    completed_early_count: int
    at_risk_task_count: int
    high_priority_alert_count: int
    health_warnings: list[DashboardHealthWarning]


class DashboardSummaryResponse(BaseModel):
    project: DashboardProjectSummary | None
    date_range: DashboardDateRange
    total_issues: int
    open_issues: int
    closed_issues: int
    overdue_issues: int
    project_health: DashboardProjectHealth
    by_status: list[DashboardStatusItem]
    by_priority: list[DashboardPriorityItem]
    by_assignee: list[DashboardAssigneeItem]
    trend: list[DashboardTrendItem]
