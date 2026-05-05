from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.middleware.auth import get_current_user
from app.models.issue import Issue
from app.models.project import Project
from app.models.redmine_connection import RedmineConnection
from app.models.user import User
from app.routes.issues import perform_issue_sync
from app.schemas.dashboard import (
    DashboardAssigneeItem,
    DashboardDateRange,
    DashboardHealthWarning,
    DashboardPriorityItem,
    DashboardProjectHealth,
    DashboardProjectSummary,
    DashboardStatusItem,
    DashboardSummaryResponse,
    DashboardTrendItem,
)
from app.schemas.issue import IssueSyncResponse

router = APIRouter()
IN_PROGRESS_STATUS_ID = 2
HIGH_PRIORITY_IDS = {3, 4}


async def get_current_connection(session) -> RedmineConnection | None:
    result = await session.execute(select(RedmineConnection).order_by(RedmineConnection.id.desc()))
    return result.scalars().first()


async def get_current_project(session, connection: RedmineConnection | None) -> Project | None:
    if not connection or not connection.identifier.strip():
        return None
    result = await session.execute(
        select(Project).where(
            Project.connection_id == connection.id,
            Project.identifier == connection.identifier,
        )
    )
    return result.scalar_one_or_none()


def in_date_range(
    value: datetime | None,
    from_date: date | None,
    to_date: date | None,
) -> bool:
    if value is None:
        return from_date is None and to_date is None
    target = value.date()
    if from_date and target < from_date:
        return False
    if to_date and target > to_date:
        return False
    return True


def get_trend_bucket(value: datetime | None, group_by: Literal["day", "week"]) -> tuple[str, str]:
    if value is None:
        return ("unknown", "Unknown")
    target = value.date()
    if group_by == "week":
        iso_year, iso_week, _ = target.isocalendar()
        bucket = f"{iso_year}-W{iso_week:02d}"
        return bucket, bucket
    bucket = target.isoformat()
    return bucket, bucket


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    _: User = Depends(get_current_user),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    group_by: Literal["day", "week"] = Query(default="day"),
):
    today = datetime.now(UTC).date()

    async with AsyncSessionLocal() as session:
        connection = await get_current_connection(session)
        project = await get_current_project(session, connection)

        if not connection or not project:
            return {
                "project": None,
                "date_range": {
                    "from_date": from_date,
                    "to_date": to_date,
                    "field": "redmine_updated_on",
                },
                "total_issues": 0,
                "open_issues": 0,
                "closed_issues": 0,
                "overdue_issues": 0,
                "project_health": {
                    "health_status": "healthy",
                    "completed_early_count": 0,
                    "at_risk_task_count": 0,
                    "high_priority_alert_count": 0,
                    "health_warnings": [],
                },
                "by_status": [],
                "by_priority": [],
                "by_assignee": [],
                "trend": [],
            }

        result = await session.execute(
            select(Issue).where(
                Issue.connection_id == connection.id,
                Issue.project_id == project.id,
            )
        )
        issues = [
            issue
            for issue in result.scalars().all()
            if in_date_range(issue.redmine_updated_on, from_date, to_date)
        ]

        total_issues = len(issues)
        closed_issues = 0
        open_issues = 0
        overdue_issues = 0
        completed_early_count = 0
        at_risk_task_count = 0
        high_priority_alert_count = 0

        by_status_map: dict[tuple[int | None, str], int] = defaultdict(int)
        by_priority_map: dict[tuple[int | None, str], int] = defaultdict(int)
        by_assignee_map: dict[tuple[int | None, str], int] = defaultdict(int)
        trend_map: dict[str, dict[str, int | str]] = {}
        health_warnings: list[DashboardHealthWarning] = []

        for issue in issues:
            # Trust the synced local flag so dashboard stays consistent with issue sync output.
            is_closed = bool(issue.is_closed)
            is_high_priority = issue.priority_id in HIGH_PRIORITY_IDS
            is_in_progress = issue.status_id == IN_PROGRESS_STATUS_ID
            is_overdue = bool(issue.due_date and issue.due_date < today)

            if is_closed:
                closed_issues += 1
                if issue.due_date and issue.redmine_updated_on and issue.redmine_updated_on.date() < issue.due_date:
                    completed_early_count += 1
            else:
                open_issues += 1
                if is_overdue:
                    overdue_issues += 1
                    at_risk_task_count += 1

            warning_type: str | None = None
            if is_high_priority and (issue.status_id != 3 and issue.status_id != 4):
                if not is_in_progress :
                    high_priority_alert_count += 1
                    warning_type = "high_priority_but_status_not_in_progress"
                elif is_overdue:
                    high_priority_alert_count += 1
                    warning_type = "high_priority_late"
                elif not is_closed and is_overdue:
                    high_priority_alert_count += 1
                    warning_type = "overdue"

            by_status_map[(issue.status_id, issue.status_name or "Unknown")] += 1
            by_priority_map[(issue.priority_id, issue.priority_name or "Unknown")] += 1
            assignee_name = issue.assignee_name or "Unassigned"
            by_assignee_map[(issue.assignee_id, assignee_name)] += 1

            bucket, label = get_trend_bucket(issue.redmine_updated_on, group_by)
            if bucket not in trend_map:
                trend_map[bucket] = {
                    "bucket": bucket,
                    "label": label,
                    "total_issues": 0,
                    "open_issues": 0,
                    "closed_issues": 0,
                }
            trend_map[bucket]["total_issues"] = int(trend_map[bucket]["total_issues"]) + 1
            if is_closed:
                trend_map[bucket]["closed_issues"] = int(trend_map[bucket]["closed_issues"]) + 1
            else:
                trend_map[bucket]["open_issues"] = int(trend_map[bucket]["open_issues"]) + 1

            if warning_type:
                health_warnings.append(
                    DashboardHealthWarning(
                        redmine_issue_id=issue.redmine_issue_id,
                        subject=issue.subject,
                        priority_id=issue.priority_id,
                        priority_name=issue.priority_name,
                        status_id=issue.status_id,
                        status_name=issue.status_name,
                        due_date=issue.due_date,
                        warning_type=warning_type,
                    )
                )

        by_status = sorted(
            [
                DashboardStatusItem(status_id=status_id, status_name=status_name, count=count)
                for (status_id, status_name), count in by_status_map.items()
            ],
            key=lambda item: (-item.count, item.status_name),
        )
        by_priority = sorted(
            [
                DashboardPriorityItem(
                    priority_id=priority_id,
                    priority_name=priority_name,
                    count=count,
                )
                for (priority_id, priority_name), count in by_priority_map.items()
            ],
            key=lambda item: (-item.count, item.priority_name),
        )
        by_assignee = sorted(
            [
                DashboardAssigneeItem(
                    assignee_id=assignee_id,
                    assignee_name=assignee_name,
                    count=count,
                )
                for (assignee_id, assignee_name), count in by_assignee_map.items()
            ],
            key=lambda item: (-item.count, item.assignee_name),
        )
        trend = [
            DashboardTrendItem(
                bucket=str(item["bucket"]),
                label=str(item["label"]),
                total_issues=int(item["total_issues"]),
                open_issues=int(item["open_issues"]),
                closed_issues=int(item["closed_issues"]),
            )
            for _, item in sorted(trend_map.items(), key=lambda pair: pair[0])
        ]
        health_warnings.sort(
            key=lambda item: (
                0 if item.warning_type.startswith("high_priority") else 1,
                item.due_date or date.max,
                item.redmine_issue_id,
            )
        )
        project_health = DashboardProjectHealth(
            health_status=(
                "critical"
                if high_priority_alert_count > 0
                else "warning"
                if at_risk_task_count > 0
                else "healthy"
            ),
            completed_early_count=completed_early_count,
            at_risk_task_count=at_risk_task_count,
            high_priority_alert_count=high_priority_alert_count,
            health_warnings=health_warnings[:5],
        )

        return {
            "project": DashboardProjectSummary(
                id=project.id,
                identifier=project.identifier,
                name=project.name,
            ),
            "date_range": DashboardDateRange(
                from_date=from_date,
                to_date=to_date,
                field="redmine_updated_on",
            ),
            "total_issues": total_issues,
            "open_issues": open_issues,
            "closed_issues": closed_issues,
            "overdue_issues": overdue_issues,
            "project_health": project_health,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_assignee": by_assignee,
            "trend": trend,
        }


@router.post("/sync-issues", response_model=IssueSyncResponse)
async def sync_dashboard_issues(_: User = Depends(get_current_user)):
    return await perform_issue_sync()
