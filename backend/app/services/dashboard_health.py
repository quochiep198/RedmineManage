from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.dashboard_health_config import DashboardHealthConfig
from app.models.dashboard_health_snapshot import DashboardHealthSnapshot
from app.models.issue import Issue
from app.models.issue_status_transition import IssueStatusTransition

DEFAULT_CLOSED_STATUS_IDS = [3, 4, 5]
DEFAULT_KPI_THRESHOLDS = {
    "aging_warning_days": 7,
    "aging_critical_days": 14,
    "overload_warning_hours": 160,
    "overload_critical_hours": 200,
    "overload_warning_share_pct": 30,
    "overload_critical_share_pct": 50,
    "reopen_warning_pct": 5,
    "reopen_critical_pct": 15,
    "reopen_window_days": 15,
    "estimate_missing_warning_pct": 30,
}


def default_health_config_payload() -> dict[str, Any]:
    return {
        "closed_status_ids_json": DEFAULT_CLOSED_STATUS_IDS,
        "bug_tracker_names_json": [],
        "metric_thresholds_json": DEFAULT_KPI_THRESHOLDS,
        "metric_weights_json": {},
        "health_status_thresholds_json": {},
    }


async def ensure_default_health_config(session) -> DashboardHealthConfig:
    result = await session.execute(
        select(DashboardHealthConfig).where(DashboardHealthConfig.scope == "global")
    )
    config = result.scalar_one_or_none()
    if config is None:
        config = DashboardHealthConfig(scope="global", **default_health_config_payload())
        session.add(config)
        await session.commit()
        await session.refresh(config)
        return config

    config.closed_status_ids_json = DEFAULT_CLOSED_STATUS_IDS
    config.metric_thresholds_json = {**(config.metric_thresholds_json or {}), **DEFAULT_KPI_THRESHOLDS}
    if config.bug_tracker_names_json is None:
        config.bug_tracker_names_json = []
    if config.metric_weights_json is None:
        config.metric_weights_json = {}
    if config.health_status_thresholds_json is None:
        config.health_status_thresholds_json = {}
    await session.commit()
    await session.refresh(config)
    return config


async def get_health_config(session) -> DashboardHealthConfig:
    return await ensure_default_health_config(session)


@dataclass
class KpiCard:
    code: str
    label: str
    status: str
    summary: str
    drilldown_risk_type: str | None
    details: dict[str, Any]


def _safe_round(value: float | None, digits: int = 1) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def _status_rank(value: str) -> int:
    return {"N/A": -1, "Good": 0, "Warning": 1, "Critical": 2}.get(value, -1)


def _overall_status(statuses: list[str]) -> str:
    if any(status == "Critical" for status in statuses):
        return "Red"
    if any(status == "Warning" for status in statuses):
        return "Yellow"
    return "Green"


def _reference_score(status: str) -> int:
    return {
        "Good": 2,
        "Warning": 1,
        "Critical": 0,
        "N/A": 0,
    }.get(status, 0)


def _trend_direction(value: float | None) -> str:
    if value is None:
        return "none"
    if value > 0:
        return "up"
    if value < 0:
        return "down"
    return "flat"


def _issue_created_date(issue: Issue) -> date | None:
    if issue.redmine_created_on:
        return issue.redmine_created_on.date()
    return None


def _is_closed_issue(issue: Issue, closed_status_ids: list[int]) -> bool:
    return issue.status_id in set(closed_status_ids)


def _aging_days(issue: Issue, today: date) -> int | None:
    created_on = _issue_created_date(issue)
    if created_on is None:
        return None
    return max(0, (today - created_on).days)


def _serialize_kpi(card: KpiCard) -> dict[str, Any]:
    return {
        "code": card.code,
        "label": card.label,
        "status": card.status,
        "summary": card.summary,
        "drilldown_risk_type": card.drilldown_risk_type,
        "details": card.details,
    }


def _build_ticket_aging_card(
    issues: list[Issue],
    thresholds: dict[str, Any],
    today: date,
    closed_status_ids: list[int],
) -> tuple[KpiCard, list[Issue]]:
    aging_warning_days = int(thresholds["aging_warning_days"])
    aging_critical_days = int(thresholds["aging_critical_days"])
    open_issues = [issue for issue in issues if not _is_closed_issue(issue, closed_status_ids)]

    enriched: list[tuple[Issue, int]] = []
    for issue in open_issues:
        days = _aging_days(issue, today)
        if days is not None:
            enriched.append((issue, days))

    warning_issues = [issue for issue, days in enriched if days >= aging_warning_days]
    critical_issues = [issue for issue, days in enriched if days >= aging_critical_days]

    if critical_issues:
        status = "Critical"
    elif warning_issues:
        status = "Warning"
    else:
        status = "Good"

    average_aging = None
    max_aging = None
    if enriched:
        values = [days for _, days in enriched]
        average_aging = round(sum(values) / len(values), 1)
        max_aging = max(values)

    top_aging_issues = [
        {
            "issue_id": issue.redmine_issue_id,
            "subject": issue.subject,
            "status": issue.status_name,
            "priority": issue.priority_name,
            "assignee": issue.assignee_name or "Unassigned",
            "aging_days": days,
        }
        for issue, days in sorted(enriched, key=lambda item: item[1], reverse=True)[:10]
    ]

    summary = (
        f"{len(critical_issues)} issues aging >= {aging_critical_days} days"
        if status == "Critical"
        else f"{len(warning_issues)} issues aging >= {aging_warning_days} days"
        if status == "Warning"
        else f"{len(open_issues)} open issues within aging threshold"
    )

    return (
        KpiCard(
            code="ticket_aging",
            label="Ticket Aging",
            status=status,
            summary=summary,
            drilldown_risk_type="aging",
            details={
                "total_open_issues": len(open_issues),
                "aging_issue_count": len(warning_issues),
                "critical_aging_issue_count": len(critical_issues),
                "average_aging_days": average_aging,
                "max_aging_days": max_aging,
                "top_aging_issues": top_aging_issues,
                "warning_threshold_days": aging_warning_days,
                "critical_threshold_days": aging_critical_days,
            },
        ),
        warning_issues,
    )


def _build_assignee_overload_card(
    issues: list[Issue],
    thresholds: dict[str, Any],
    closed_status_ids: list[int],
) -> tuple[KpiCard, list[dict[str, Any]], list[dict[str, Any]]]:
    warning_hours = float(thresholds["overload_warning_hours"])
    critical_hours = float(thresholds["overload_critical_hours"])
    warning_share = float(thresholds["overload_warning_share_pct"])
    critical_share = float(thresholds["overload_critical_share_pct"])
    estimate_missing_warning_pct = float(thresholds["estimate_missing_warning_pct"])

    open_issues = [issue for issue in issues if not _is_closed_issue(issue, closed_status_ids)]
    total_open_workload = sum(float(issue.estimated_hours or 0) for issue in open_issues)
    missing_estimate_count = sum(1 for issue in open_issues if issue.estimated_hours in (None, 0))
    missing_estimate_pct = (missing_estimate_count / len(open_issues) * 100.0) if open_issues else 0.0

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "assignee": "Unassigned",
            "open_issue_count": 0,
            "total_estimated_hours": 0.0,
            "high_priority_issue_count": 0,
            "overdue_issue_count": 0,
            "issues": [],
        }
    )
    today = datetime.now(UTC).date()
    for issue in open_issues:
        assignee = issue.assignee_name or "Unassigned"
        bucket = grouped[assignee]
        bucket["assignee"] = assignee
        bucket["open_issue_count"] += 1
        bucket["total_estimated_hours"] += float(issue.estimated_hours or 0)
        bucket["issues"].append(issue)
        if (issue.priority_name or "").strip().lower() in {"high", "critical", "urgent"}:
            bucket["high_priority_issue_count"] += 1
        if issue.due_date and issue.due_date < today:
            bucket["overdue_issue_count"] += 1

    rows: list[dict[str, Any]] = []
    overloaded_rows: list[dict[str, Any]] = []
    for assignee, bucket in grouped.items():
        hours = float(bucket["total_estimated_hours"])
        share = 0.0 if total_open_workload <= 0 else (hours / total_open_workload) * 100.0

        status_by_hours = "Critical" if hours >= critical_hours else "Warning" if hours >= warning_hours else "Good"
        status_by_share = "Critical" if share >= critical_share else "Warning" if share >= warning_share else "Good"
        risk_level = status_by_hours if _status_rank(status_by_hours) >= _status_rank(status_by_share) else status_by_share
        if _status_rank(status_by_hours) >= _status_rank(status_by_share):
            risk_reason = f"Workload hours = {int(hours) if hours.is_integer() else round(hours, 1)}h"
        else:
            risk_reason = f"Workload share = {round(share, 1)}%"

        row = {
            "assignee": assignee,
            "open_issue_count": bucket["open_issue_count"],
            "total_estimated_hours": round(hours, 1),
            "workload_share_pct": round(share, 1),
            "high_priority_issue_count": bucket["high_priority_issue_count"],
            "overdue_issue_count": bucket["overdue_issue_count"],
            "risk_level": risk_level,
            "risk_reason": risk_reason,
        }
        rows.append(row)
        if risk_level in {"Warning", "Critical"}:
            overloaded_rows.append(row)

    rows.sort(key=lambda item: (item["total_estimated_hours"], item["workload_share_pct"]), reverse=True)
    overloaded_rows.sort(key=lambda item: (_status_rank(item["risk_level"]), item["total_estimated_hours"]), reverse=True)

    status = overloaded_rows[0]["risk_level"] if overloaded_rows else "Good"
    summary = (
        f'{overloaded_rows[0]["assignee"]} has {int(overloaded_rows[0]["total_estimated_hours"])}h and {overloaded_rows[0]["workload_share_pct"]}% workload share'
        if overloaded_rows
        else "No assignee is overloaded"
    )

    warnings: list[dict[str, Any]] = []
    if open_issues and missing_estimate_pct >= estimate_missing_warning_pct:
        warnings.append(
            {
                "code": "workload_data_incomplete",
                "level": "Warning",
                "message": "Workload data may be incomplete.",
            }
        )

    return (
        KpiCard(
            code="assignee_overload",
            label="Assignee Overload",
            status=status,
            summary=summary,
            drilldown_risk_type="overload",
            details={
                "rows": rows,
                "warning_hours": warning_hours,
                "critical_hours": critical_hours,
                "warning_share_pct": warning_share,
                "critical_share_pct": critical_share,
                "missing_estimate_pct": round(missing_estimate_pct, 1),
            },
        ),
        overloaded_rows,
        warnings,
    )


def _build_reopen_rate_card(
    issues: list[Issue],
    transitions: list[IssueStatusTransition],
    thresholds: dict[str, Any],
    today: date,
    history_ready: bool,
    closed_status_ids: list[int],
) -> tuple[KpiCard, list[dict[str, Any]], list[dict[str, Any]]]:
    window_days = int(thresholds["reopen_window_days"])
    warning_pct = float(thresholds["reopen_warning_pct"])
    critical_pct = float(thresholds["reopen_critical_pct"])

    if not history_ready:
        return (
            KpiCard(
                code="reopen_rate",
                label="Reopen Rate",
                status="N/A",
                summary="Reopen data unavailable",
                drilldown_risk_type=None,
                details={"reason": "Reopen data unavailable"},
            ),
            [],
            [
                {
                    "code": "reopen_data_unavailable",
                    "level": "Warning",
                    "message": "Reopen data unavailable.",
                }
            ],
        )

    window_start = datetime.combine(today - timedelta(days=window_days), datetime.min.time(), tzinfo=UTC)
    window_transitions = [item for item in transitions if item.changed_on.replace(tzinfo=UTC) >= window_start]

    closed_status_ids_set = set(closed_status_ids)
    closed_issue_ids: set[int] = set()
    reopened_issue_ids: set[int] = set()
    reopen_meta: dict[int, dict[str, Any]] = {}

    for transition in sorted(window_transitions, key=lambda item: item.changed_on):
        if transition.to_status_id in closed_status_ids_set:
            closed_issue_ids.add(transition.redmine_issue_id)
        if transition.from_status_id in closed_status_ids_set and transition.to_status_id not in closed_status_ids_set:
            reopened_issue_ids.add(transition.redmine_issue_id)
            meta = reopen_meta.setdefault(
                transition.redmine_issue_id,
                {
                    "reopen_count": 0,
                    "last_reopened_date": None,
                    "previous_closed_status_id": transition.from_status_id,
                    "new_status_id": transition.to_status_id,
                },
            )
            meta["reopen_count"] += 1
            meta["last_reopened_date"] = transition.changed_on
            meta["previous_closed_status_id"] = transition.from_status_id
            meta["new_status_id"] = transition.to_status_id

    relevant_reopened_ids = reopened_issue_ids & closed_issue_ids
    issue_lookup = {issue.redmine_issue_id: issue for issue in issues}
    reopened_items: list[dict[str, Any]] = []
    for issue_id in sorted(relevant_reopened_ids):
        issue = issue_lookup.get(issue_id)
        if issue is None:
            continue
        meta = reopen_meta[issue_id]
        reopened_items.append(
            {
                "issue_id": issue.redmine_issue_id,
                "subject": issue.subject,
                "tracker": issue.tracker_name,
                "assignee": issue.assignee_name or "Unassigned",
                "current_status": issue.status_name,
                "reopen_count": meta["reopen_count"],
                "last_reopened_date": meta["last_reopened_date"].isoformat() if meta["last_reopened_date"] else None,
                "previous_closed_status_id": meta["previous_closed_status_id"],
                "new_status_id": meta["new_status_id"],
            }
        )

    closed_issue_count = len(closed_issue_ids)
    reopened_issue_count = len(relevant_reopened_ids)
    reopen_rate_pct = None if closed_issue_count == 0 else (reopened_issue_count / closed_issue_count) * 100.0

    if reopen_rate_pct is None:
        status = "N/A"
        summary = "No closed issues in reopen window"
    elif reopen_rate_pct >= critical_pct:
        status = "Critical"
        summary = f"{round(reopen_rate_pct, 1)}% in last {window_days} days"
    elif reopen_rate_pct >= warning_pct:
        status = "Warning"
        summary = f"{round(reopen_rate_pct, 1)}% in last {window_days} days"
    else:
        status = "Good"
        summary = f"{round(reopen_rate_pct, 1)}% in last {window_days} days"

    count_by_assignee = Counter(item["assignee"] for item in reopened_items)
    count_by_tracker = Counter(item["tracker"] or "Unknown" for item in reopened_items)

    return (
        KpiCard(
            code="reopen_rate",
            label="Reopen Rate",
            status=status,
            summary=summary,
            drilldown_risk_type="reopen" if reopen_rate_pct is not None else None,
            details={
                "closed_issue_count": closed_issue_count,
                "reopened_issue_count": reopened_issue_count,
                "reopen_rate_pct": _safe_round(reopen_rate_pct, 1),
                "reopen_count_by_assignee": dict(count_by_assignee),
                "reopen_count_by_tracker": dict(count_by_tracker),
                "items": reopened_items,
                "window_days": window_days,
            },
        ),
        reopened_items,
        [],
    )


def _build_risk_drivers(
    aging_issues: list[Issue],
    overload_rows: list[dict[str, Any]],
    reopen_items: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[dict[str, Any]]:
    drivers: list[dict[str, Any]] = []
    if aging_issues:
        drivers.append(
            {
                "risk_type": "aging",
                "label": f'{len(aging_issues)} open issues have aging >= {int(thresholds["aging_warning_days"])} days.',
                "issue_count": len(aging_issues),
                "issue_ratio": None,
                "dimension": "project",
                "dimension_value": "current_project",
                "drilldown_risk_type": "aging",
                "drilldown_dimension": "project",
                "drilldown_value": "current_project",
            }
        )
    if overload_rows:
        top = overload_rows[0]
        drivers.append(
            {
                "risk_type": "overload",
                "label": f'{top["assignee"]} owns {top["workload_share_pct"]}% of open estimated workload.',
                "issue_count": int(top["open_issue_count"]),
                "issue_ratio": top["workload_share_pct"],
                "dimension": "assignee",
                "dimension_value": top["assignee"],
                "drilldown_risk_type": "overload",
                "drilldown_dimension": "assignee",
                "drilldown_value": top["assignee"],
            }
        )
    if reopen_items:
        count = len(reopen_items)
        window_days = int(thresholds["reopen_window_days"])
        drivers.append(
            {
                "risk_type": "reopen",
                "label": f"Reopen issues are present in the last {window_days} days.",
                "issue_count": count,
                "issue_ratio": None,
                "dimension": "project",
                "dimension_value": "current_project",
                "drilldown_risk_type": "reopen",
                "drilldown_dimension": "project",
                "drilldown_value": "current_project",
            }
        )
    return drivers[:3]


def _build_suggested_actions(
    cards: list[KpiCard],
    overload_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    by_code = {card.code: card for card in cards}
    if by_code["ticket_aging"].status in {"Warning", "Critical"}:
        actions.append(
            {
                "risk_type": "aging",
                "message": "Review critical aging issues first.",
                "drilldown_risk_type": "aging",
                "drilldown_dimension": "project",
                "drilldown_value": "current_project",
            }
        )
    if by_code["assignee_overload"].status in {"Warning", "Critical"} and overload_rows:
        assignee = overload_rows[0]["assignee"]
        actions.append(
            {
                "risk_type": "overload",
                "message": f"Rebalance workload of {assignee}.",
                "drilldown_risk_type": "overload",
                "drilldown_dimension": "assignee",
                "drilldown_value": assignee,
            }
        )
    if by_code["reopen_rate"].status in {"Warning", "Critical"}:
        actions.append(
            {
                "risk_type": "reopen",
                "message": "Analyze reopened issues to identify quality gaps.",
                "drilldown_risk_type": "reopen",
                "drilldown_dimension": "project",
                "drilldown_value": "current_project",
            }
        )
    return actions[:3]


def _make_snapshot_trend_item(snapshot: DashboardHealthSnapshot, previous_score: float | None) -> dict[str, Any]:
    trend_value = None if previous_score is None else round(float(snapshot.health_score) - previous_score, 2)
    return {
        "snapshot_at": snapshot.snapshot_at,
        "label": snapshot.snapshot_at.date().isoformat(),
        "score": round(float(snapshot.health_score), 2),
        "status": snapshot.health_status,
        "trend_value": trend_value,
        "trend_direction": _trend_direction(trend_value),
    }


async def calculate_project_health(
    *,
    session,
    connection_id: int,
    project_id: int,
    issues: list[Issue],
) -> dict[str, Any]:
    config = await get_health_config(session)
    thresholds = {**DEFAULT_KPI_THRESHOLDS, **(config.metric_thresholds_json or {})}
    closed_status_ids = config.closed_status_ids_json or DEFAULT_CLOSED_STATUS_IDS
    today = datetime.now(UTC).date()

    transitions_result = await session.execute(
        select(IssueStatusTransition).where(
            IssueStatusTransition.connection_id == connection_id,
            IssueStatusTransition.project_id == project_id,
        )
    )
    transitions = transitions_result.scalars().all()
    history_ready = len(transitions) > 0

    aging_card, aging_issues = _build_ticket_aging_card(issues, thresholds, today, closed_status_ids)
    overload_card, overload_rows, overload_warnings = _build_assignee_overload_card(
        issues,
        thresholds,
        closed_status_ids,
    )
    reopen_card, reopen_items, reopen_warnings = _build_reopen_rate_card(
        issues,
        transitions,
        thresholds,
        today,
        history_ready,
        closed_status_ids,
    )
    cards = [aging_card, overload_card, reopen_card]

    kpi_statuses = [card.status for card in cards if card.status != "N/A"]
    overall_status = _overall_status(kpi_statuses or ["Good"])
    internal_score = sum(_reference_score(card.status) for card in cards)

    snapshot_result = await session.execute(
        select(DashboardHealthSnapshot)
        .where(
            DashboardHealthSnapshot.connection_id == connection_id,
            DashboardHealthSnapshot.project_id == project_id,
        )
        .order_by(DashboardHealthSnapshot.snapshot_at.desc())
        .limit(8)
    )
    previous_snapshots = snapshot_result.scalars().all()
    trend_items: list[dict[str, Any]] = []
    previous_score: float | None = None
    for snapshot in reversed(previous_snapshots[-8:]):
        trend_items.append(_make_snapshot_trend_item(snapshot, previous_score))
        previous_score = float(snapshot.health_score)

    current_trend_value = None
    if previous_snapshots:
        current_trend_value = round(internal_score - float(previous_snapshots[0].health_score), 2)

    risk_drivers = _build_risk_drivers(aging_issues, overload_rows, reopen_items, thresholds)
    suggested_actions = _build_suggested_actions(cards, overload_rows)
    warnings = overload_warnings + reopen_warnings

    open_count = sum(1 for issue in issues if not _is_closed_issue(issue, closed_status_ids))
    closed_count = sum(1 for issue in issues if _is_closed_issue(issue, closed_status_ids))
    overdue_count = sum(
        1
        for issue in issues
        if (not _is_closed_issue(issue, closed_status_ids) and issue.due_date and issue.due_date < today)
    )

    return {
        "total_issues": len(issues),
        "open_issues": open_count,
        "closed_issues": closed_count,
        "overdue_issues": overdue_count,
        "health_summary": {
            "status": overall_status,
            "score_label": f"{internal_score} / 6",
            "trend_value": current_trend_value,
            "trend_direction": _trend_direction(current_trend_value),
        },
        "kpi_cards": [_serialize_kpi(card) for card in cards],
        "main_risk_drivers": risk_drivers,
        "suggested_actions": suggested_actions,
        "data_quality_warnings": warnings,
        "health_trend": trend_items,
        "metric_scores_json": {card.code: {"status": card.status, "summary": card.summary} for card in cards},
        "metric_values_json": {card.code: card.details for card in cards},
        "internal_health_score": internal_score,
    }


async def persist_health_snapshot(connection_id: int, project_id: int) -> None:
    async with AsyncSessionLocal() as session:
        issues_result = await session.execute(
            select(Issue).where(
                Issue.connection_id == connection_id,
                Issue.project_id == project_id,
            )
        )
        issues = issues_result.scalars().all()
        summary = await calculate_project_health(
            session=session,
            connection_id=connection_id,
            project_id=project_id,
            issues=issues,
        )
        snapshot = DashboardHealthSnapshot(
            connection_id=connection_id,
            project_id=project_id,
            snapshot_at=datetime.now(UTC),
            health_score=float(summary["internal_health_score"]),
            health_status=str(summary["health_summary"]["status"]),
            metric_scores_json=summary["metric_scores_json"],
            metric_values_json=summary["metric_values_json"],
            main_risk_drivers_json=summary["main_risk_drivers"],
            warnings_json=summary["data_quality_warnings"],
            suggested_actions_json=summary["suggested_actions"],
        )
        session.add(snapshot)
        await session.commit()
