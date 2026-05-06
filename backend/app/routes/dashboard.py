from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.middleware.auth import get_current_user
from app.models.issue import Issue
from app.models.project import Project
from app.models.redmine_connection import RedmineConnection
from app.models.user import User
from app.routes.issues import perform_issue_sync
from app.schemas.dashboard import DashboardDateRange, DashboardProjectSummary, DashboardSummaryResponse
from app.schemas.issue import IssueSyncResponse
from app.services.dashboard_health import calculate_project_health

router = APIRouter()


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


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    _: User = Depends(get_current_user),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    group_by: Literal["day", "week"] = Query(default="week"),
):
    async with AsyncSessionLocal() as session:
        connection = await get_current_connection(session)
        project = await get_current_project(session, connection)

        empty_response = {
            "project": None,
            "date_range": {
                "from_date": from_date,
                "to_date": to_date,
                "field": "redmine_updated_on",
            },
            "last_updated": None,
            "total_issues": 0,
            "open_issues": 0,
            "closed_issues": 0,
            "overdue_issues": 0,
            "health_summary": {
                "status": "Red",
                "score_label": None,
                "trend_value": None,
                "trend_direction": "none",
            },
            "kpi_cards": [],
            "main_risk_drivers": [],
            "suggested_actions": [],
            "data_quality_warnings": [],
            "health_trend": [],
        }
        if not connection or not project:
            return empty_response

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
        summary = await calculate_project_health(
            session=session,
            connection_id=connection.id,
            project_id=project.id,
            issues=issues,
        )

        if group_by == "day":
            health_trend = summary["health_trend"]
        else:
            weekly_items: list[dict] = []
            week_buckets: dict[str, dict] = {}
            for item in summary["health_trend"]:
                snapshot_at = item["snapshot_at"]
                iso_year, iso_week, _ = snapshot_at.date().isocalendar()
                bucket = f"{iso_year}-W{iso_week:02d}"
                week_buckets[bucket] = {
                    "snapshot_at": snapshot_at,
                    "label": bucket,
                    "score": item["score"],
                    "status": item["status"],
                    "trend_value": item["trend_value"],
                    "trend_direction": item["trend_direction"],
                }
            for _, item in sorted(week_buckets.items(), key=lambda pair: pair[0]):
                weekly_items.append(item)
            health_trend = weekly_items

        last_updated = None
        if issues:
            last_updated = max((issue.redmine_updated_on for issue in issues if issue.redmine_updated_on), default=None)

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
            "last_updated": last_updated,
            "total_issues": summary["total_issues"],
            "open_issues": summary["open_issues"],
            "closed_issues": summary["closed_issues"],
            "overdue_issues": summary["overdue_issues"],
            "health_summary": summary["health_summary"],
            "kpi_cards": summary["kpi_cards"],
            "main_risk_drivers": summary["main_risk_drivers"],
            "suggested_actions": summary["suggested_actions"],
            "data_quality_warnings": summary["data_quality_warnings"],
            "health_trend": health_trend,
        }


@router.post("/sync-issues", response_model=IssueSyncResponse)
async def sync_dashboard_issues(_: User = Depends(get_current_user)):
    return await perform_issue_sync()
