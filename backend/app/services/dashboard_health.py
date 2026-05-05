from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from math import isfinite
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.dashboard_health_config import DashboardHealthConfig
from app.models.dashboard_health_snapshot import DashboardHealthSnapshot
from app.models.issue import Issue

MAX_METRIC_SCORE = 2
MAX_HEALTH_SCORE = 12
DEFAULT_STALE_DAYS = 7
DEFAULT_BUG_TRACKERS = ["Bug", "Defect"]
DEFAULT_CLOSED_STATUS_IDS = [3, 5]


def default_metric_thresholds() -> dict[str, Any]:
    return {
        "progress": {"lag_warning_pct": 10.0},
        "closed_rate": {"green_min": 80.0, "yellow_min": 50.0},
        "overdue_rate": {"green_max": 0.0, "yellow_max": 10.0},
        "bug_rate": {"green_max": 10.0, "yellow_max": 25.0},
        "effort_ratio": {"green_max": 100.0, "yellow_max": 120.0},
        "stale_rate": {"green_max": 5.0, "yellow_max": 15.0},
        "stale_days": DEFAULT_STALE_DAYS,
    }


def default_metric_weights() -> dict[str, int]:
    return {
        "progress": 1,
        "closed_rate": 1,
        "overdue_rate": 1,
        "bug_rate": 1,
        "effort_ratio": 1,
        "stale_rate": 1,
    }


def default_health_status_thresholds() -> dict[str, int]:
    return {"green_min": 10, "yellow_min": 7, "red_max": 6}


def default_health_config_payload() -> dict[str, Any]:
    return {
        "closed_status_ids_json": DEFAULT_CLOSED_STATUS_IDS,
        "bug_tracker_names_json": DEFAULT_BUG_TRACKERS,
        "metric_thresholds_json": default_metric_thresholds(),
        "metric_weights_json": default_metric_weights(),
        "health_status_thresholds_json": default_health_status_thresholds(),
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


async def get_health_config(session) -> DashboardHealthConfig:
    return await ensure_default_health_config(session)


@dataclass
class MetricResult:
    code: str
    label: str
    score: int
    max_score: int
    value: float | None
    value_display: str
    benchmark: str
    drilldown_risk_type: str | None
    details: dict[str, Any]


def _safe_round(value: float | None, digits: int = 1) -> float | None:
    if value is None or not isfinite(value):
        return None
    return round(value, digits)


def _format_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{_safe_round(value, 1)}%"


def _average_done_ratio(issues: list[Issue]) -> float | None:
    ratios = [float(issue.done_ratio or 0) for issue in issues if issue.done_ratio is not None]
    if not ratios:
        return None
    return sum(ratios) / len(ratios)


def _planned_progress(issues: list[Issue], today: date) -> tuple[float | None, date | None, date | None]:
    start_dates = [issue.start_date for issue in issues if issue.start_date is not None]
    due_dates = [issue.due_date for issue in issues if issue.due_date is not None]
    if not start_dates or not due_dates:
        return None, None, None
    project_start = min(start_dates)
    project_due = max(due_dates)
    if project_start == project_due:
        if today < project_start:
            return 0.0, project_start, project_due
        return 100.0, project_start, project_due
    if today <= project_start:
        return 0.0, project_start, project_due
    if today >= project_due:
        return 100.0, project_start, project_due
    elapsed_days = (today - project_start).days
    total_days = (project_due - project_start).days
    if total_days <= 0:
        return None, project_start, project_due
    return max(0.0, min(100.0, (elapsed_days / total_days) * 100.0)), project_start, project_due


def _group_counter(
    issues: list[Issue],
    *,
    attr_name: str,
    fallback: str,
) -> Counter[str]:
    counter: Counter[str] = Counter()
    for issue in issues:
        value = getattr(issue, attr_name, None) or fallback
        counter[str(value)] += 1
    return counter


def _make_risk_driver(
    *,
    risk_type: str,
    label: str,
    issue_count: int,
    issue_ratio: float | None,
    dimension: str,
    dimension_value: str | None,
    drilldown_risk_type: str | None = None,
    drilldown_dimension: str | None = None,
    drilldown_value: str | None = None,
) -> dict[str, Any]:
    return {
        "risk_type": risk_type,
        "label": label,
        "issue_count": issue_count,
        "issue_ratio": _safe_round(issue_ratio, 1),
        "dimension": dimension,
        "dimension_value": dimension_value,
        "drilldown_risk_type": drilldown_risk_type or risk_type,
        "drilldown_dimension": drilldown_dimension or dimension,
        "drilldown_value": drilldown_value or dimension_value,
    }


def _progress_metric(issues: list[Issue], thresholds: dict[str, Any], today: date) -> MetricResult:
    planned, project_start, project_due = _planned_progress(issues, today)
    actual = _average_done_ratio(issues)
    lag_warning_pct = float(thresholds["progress"]["lag_warning_pct"])
    if planned is None or actual is None:
        score = 0
    elif actual >= planned:
        score = 2
    elif planned - actual <= lag_warning_pct:
        score = 1
    else:
        score = 0
    value_display = (
        f"Actual {_format_percent(actual)} / Planned {_format_percent(planned)}"
        if planned is not None and actual is not None
        else "N/A"
    )
    return MetricResult(
        code="progress",
        label="Progress",
        score=score,
        max_score=MAX_METRIC_SCORE,
        value=None if planned is None or actual is None else actual - planned,
        value_display=value_display,
        benchmark=f"lag <= {lag_warning_pct}%",
        drilldown_risk_type="progress",
        details={
            "planned_progress_pct": _safe_round(planned, 1),
            "actual_progress_pct": _safe_round(actual, 1),
            "schedule_gap_pct": None if planned is None or actual is None else _safe_round(actual - planned, 1),
            "project_start_date": project_start.isoformat() if project_start else None,
            "project_due_date": project_due.isoformat() if project_due else None,
        },
    )


def _closed_rate_metric(issues: list[Issue], thresholds: dict[str, Any]) -> MetricResult:
    total = len(issues)
    closed = sum(1 for issue in issues if issue.is_closed)
    value = None if total == 0 else (closed / total) * 100.0
    green_min = float(thresholds["closed_rate"]["green_min"])
    yellow_min = float(thresholds["closed_rate"]["yellow_min"])
    if value is None:
        score = 0
    elif value >= green_min:
        score = 2
    elif value >= yellow_min:
        score = 1
    else:
        score = 0
    return MetricResult(
        code="closed_rate",
        label="Closed Rate",
        score=score,
        max_score=MAX_METRIC_SCORE,
        value=value,
        value_display=_format_percent(value),
        benchmark=f">= {yellow_min}% / >= {green_min}%",
        drilldown_risk_type="closed_rate",
        details={"closed_count": closed, "total_issue_count": total},
    )


def _overdue_rate_metric(issues: list[Issue], thresholds: dict[str, Any], today: date) -> tuple[MetricResult, list[Issue]]:
    open_issues = [issue for issue in issues if not issue.is_closed]
    overdue_issues = [issue for issue in open_issues if issue.due_date and issue.due_date < today]
    value = None if not open_issues else (len(overdue_issues) / len(open_issues)) * 100.0
    green_max = float(thresholds["overdue_rate"]["green_max"])
    yellow_max = float(thresholds["overdue_rate"]["yellow_max"])
    if value is None:
        score = 0
    elif value <= green_max:
        score = 2
    elif value <= yellow_max:
        score = 1
    else:
        score = 0
    return (
        MetricResult(
            code="overdue_rate",
            label="Overdue",
            score=score,
            max_score=MAX_METRIC_SCORE,
            value=value,
            value_display=f"{len(overdue_issues)} issues ({_format_percent(value)})" if value is not None else "N/A",
            benchmark=f"0% / <= {yellow_max}%",
            drilldown_risk_type="overdue",
            details={
                "overdue_count": len(overdue_issues),
                "open_issue_count": len(open_issues),
            },
        ),
        overdue_issues,
    )


def _bug_rate_metric(
    issues: list[Issue],
    thresholds: dict[str, Any],
    bug_trackers: list[str],
) -> tuple[MetricResult, list[Issue]]:
    open_issues = [issue for issue in issues if not issue.is_closed]
    bug_set = {item.strip().lower() for item in bug_trackers if item.strip()}
    open_bugs = [
        issue
        for issue in open_issues
        if (issue.tracker_name or "").strip().lower() in bug_set
    ]
    value = None if not open_issues else (len(open_bugs) / len(open_issues)) * 100.0
    green_max = float(thresholds["bug_rate"]["green_max"])
    yellow_max = float(thresholds["bug_rate"]["yellow_max"])
    if value is None:
        score = 0
    elif value <= green_max:
        score = 2
    elif value <= yellow_max:
        score = 1
    else:
        score = 0
    return (
        MetricResult(
            code="bug_rate",
            label="Bug Rate",
            score=score,
            max_score=MAX_METRIC_SCORE,
            value=value,
            value_display=f"{len(open_bugs)} bugs ({_format_percent(value)})" if value is not None else "N/A",
            benchmark=f"<= {green_max}% / <= {yellow_max}%",
            drilldown_risk_type="bug",
            details={
                "open_bug_count": len(open_bugs),
                "open_issue_count": len(open_issues),
                "bug_trackers": bug_trackers,
            },
        ),
        open_bugs,
    )


def _effort_metric(issues: list[Issue], thresholds: dict[str, Any]) -> tuple[MetricResult, list[Issue]]:
    eligible = [issue for issue in issues if (issue.estimated_hours or 0) > 0]
    estimated_total = sum(float(issue.estimated_hours or 0) for issue in eligible)
    spent_total = sum(float(issue.spent_hours or 0) for issue in eligible)
    value = None if estimated_total <= 0 else (spent_total / estimated_total) * 100.0
    green_max = float(thresholds["effort_ratio"]["green_max"])
    yellow_max = float(thresholds["effort_ratio"]["yellow_max"])
    high_effort_issues = [
        issue
        for issue in eligible
        if float(issue.spent_hours or 0) / float(issue.estimated_hours or 1) * 100.0 > yellow_max
    ]
    if value is None:
        score = 0
    elif value <= green_max:
        score = 2
    elif value <= yellow_max:
        score = 1
    else:
        score = 0
    return (
        MetricResult(
            code="effort_ratio",
            label="Effort",
            score=score,
            max_score=MAX_METRIC_SCORE,
            value=value,
            value_display=_format_percent(value),
            benchmark=f"<= {green_max}% / <= {yellow_max}%",
            drilldown_risk_type="effort",
            details={
                "estimated_hours_total": _safe_round(estimated_total, 2),
                "spent_hours_total": _safe_round(spent_total, 2),
                "eligible_issue_count": len(eligible),
            },
        ),
        high_effort_issues,
    )


def _stale_metric(issues: list[Issue], thresholds: dict[str, Any], today: date) -> tuple[MetricResult, list[Issue]]:
    stale_days = int(thresholds.get("stale_days") or DEFAULT_STALE_DAYS)
    open_issues = [issue for issue in issues if not issue.is_closed]
    stale_cutoff = today - timedelta(days=stale_days)
    stale_issues = [
        issue
        for issue in open_issues
        if issue.redmine_updated_on and issue.redmine_updated_on.date() < stale_cutoff
    ]
    value = None if not open_issues else (len(stale_issues) / len(open_issues)) * 100.0
    green_max = float(thresholds["stale_rate"]["green_max"])
    yellow_max = float(thresholds["stale_rate"]["yellow_max"])
    if value is None:
        score = 0
    elif value <= green_max:
        score = 2
    elif value <= yellow_max:
        score = 1
    else:
        score = 0
    return (
        MetricResult(
            code="stale_rate",
            label="Stale Issue",
            score=score,
            max_score=MAX_METRIC_SCORE,
            value=value,
            value_display=f"{len(stale_issues)} issues ({_format_percent(value)})" if value is not None else "N/A",
            benchmark=f"<= {green_max}% / <= {yellow_max}%",
            drilldown_risk_type="stale",
            details={
                "stale_issue_count": len(stale_issues),
                "open_issue_count": len(open_issues),
                "stale_threshold_days": stale_days,
            },
        ),
        stale_issues,
    )


def _metric_status(score: float, status_thresholds: dict[str, int]) -> str:
    if score >= status_thresholds["green_min"]:
        return "Green"
    if score >= status_thresholds["yellow_min"]:
        return "Yellow"
    return "Red"


def _trend_direction(value: float | None) -> str:
    if value is None:
        return "none"
    if value > 0:
        return "up"
    if value < 0:
        return "down"
    return "flat"


def _pick_top_group(issues: list[Issue], attr_name: str, fallback: str) -> tuple[str, int]:
    counter = _group_counter(issues, attr_name=attr_name, fallback=fallback)
    if not counter:
        return fallback, 0
    label, count = counter.most_common(1)[0]
    return label, count


def build_risk_drivers(
    metrics: dict[str, MetricResult],
    *,
    overdue_issues: list[Issue],
    open_bugs: list[Issue],
    high_effort_issues: list[Issue],
    stale_issues: list[Issue],
) -> list[dict[str, Any]]:
    candidates: list[tuple[int, dict[str, Any]]] = []
    progress_metric = metrics["progress"]
    closed_metric = metrics["closed_rate"]
    overdue_metric = metrics["overdue_rate"]
    bug_metric = metrics["bug_rate"]
    effort_metric = metrics["effort_ratio"]
    stale_metric = metrics["stale_rate"]

    if progress_metric.score < MAX_METRIC_SCORE:
        gap = progress_metric.details.get("schedule_gap_pct")
        candidates.append(
            (
                progress_metric.score,
                _make_risk_driver(
                    risk_type="progress",
                    label=f"Schedule gap is {_format_percent(abs(gap) if gap is not None else None)} behind plan",
                    issue_count=0,
                    issue_ratio=None,
                    dimension="project",
                    dimension_value="current_project",
                ),
            )
        )
    if closed_metric.score < MAX_METRIC_SCORE and closed_metric.value is not None:
        candidates.append(
            (
                closed_metric.score,
                _make_risk_driver(
                    risk_type="closed_rate",
                    label=f"Closed rate is only {_format_percent(closed_metric.value)}",
                    issue_count=int(closed_metric.details["closed_count"]),
                    issue_ratio=closed_metric.value,
                    dimension="project",
                    dimension_value="current_project",
                ),
            )
        )
    if overdue_metric.score < MAX_METRIC_SCORE and overdue_issues:
        assignee, count = _pick_top_group(overdue_issues, "assignee_name", "Unassigned")
        ratio = (count / len(overdue_issues)) * 100.0 if overdue_issues else None
        candidates.append(
            (
                overdue_metric.score,
                _make_risk_driver(
                    risk_type="overdue",
                    label=f"{_format_percent(ratio)} of overdue issues belong to assignee {assignee}",
                    issue_count=count,
                    issue_ratio=ratio,
                    dimension="assignee",
                    dimension_value=assignee,
                ),
            )
        )
    if bug_metric.score < MAX_METRIC_SCORE and open_bugs:
        tracker, tracker_count = _pick_top_group(open_bugs, "tracker_name", "Unknown")
        subject, subject_count = _pick_top_group(open_bugs, "subject", "Unknown")
        if tracker_count >= subject_count:
            label = f"{_format_percent((tracker_count / len(open_bugs)) * 100.0)} of open bugs are in tracker {tracker}"
            dimension = "tracker"
            value = tracker
            count = tracker_count
        else:
            label = f"{_format_percent((subject_count / len(open_bugs)) * 100.0)} of open bugs are in issue group \"{subject}\""
            dimension = "subject_group"
            value = subject
            count = subject_count
        candidates.append(
            (
                bug_metric.score,
                _make_risk_driver(
                    risk_type="bug",
                    label=label,
                    issue_count=count,
                    issue_ratio=(count / len(open_bugs)) * 100.0,
                    dimension=dimension,
                    dimension_value=value,
                ),
            )
        )
    if effort_metric.score < MAX_METRIC_SCORE and high_effort_issues:
        top_issue = sorted(
            high_effort_issues,
            key=lambda item: (float(item.spent_hours or 0) / float(item.estimated_hours or 1)),
            reverse=True,
        )[0]
        ratio = float(top_issue.spent_hours or 0) / float(top_issue.estimated_hours or 1) * 100.0
        candidates.append(
            (
                effort_metric.score,
                _make_risk_driver(
                    risk_type="effort",
                    label=f"Issue #{top_issue.redmine_issue_id} is at {_format_percent(ratio)} effort ratio",
                    issue_count=len(high_effort_issues),
                    issue_ratio=(len(high_effort_issues) / max(1, int(effort_metric.details["eligible_issue_count"]))) * 100.0,
                    dimension="issue",
                    dimension_value=str(top_issue.redmine_issue_id),
                ),
            )
        )
    if stale_metric.score < MAX_METRIC_SCORE and stale_issues:
        assignee, count = _pick_top_group(stale_issues, "assignee_name", "Unassigned")
        ratio = (count / len(stale_issues)) * 100.0 if stale_issues else None
        candidates.append(
            (
                stale_metric.score,
                _make_risk_driver(
                    risk_type="stale",
                    label=f"{_format_percent(ratio)} of stale issues belong to assignee {assignee}",
                    issue_count=count,
                    issue_ratio=ratio,
                    dimension="assignee",
                    dimension_value=assignee,
                ),
            )
        )

    return [item for _, item in sorted(candidates, key=lambda pair: (pair[0], -pair[1]["issue_count"]))[:3]]


def build_suggested_actions(
    metrics: dict[str, MetricResult],
    risk_drivers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    by_risk = {item["risk_type"]: item for item in risk_drivers}
    if metrics["overdue_rate"].score < MAX_METRIC_SCORE:
        actions.append(
            {
                "risk_type": "overdue",
                "message": "Review overdue issues first, prioritize High/Critical items.",
                "drilldown_risk_type": "overdue",
            }
        )
    if metrics["bug_rate"].score < MAX_METRIC_SCORE:
        bug_driver = by_risk.get("bug")
        label = bug_driver["dimension_value"] if bug_driver else "the top bug group"
        actions.append(
            {
                "risk_type": "bug",
                "message": f"Focus bug fixing on {label} first.",
                "drilldown_risk_type": "bug",
                "drilldown_dimension": bug_driver["dimension"] if bug_driver else None,
                "drilldown_value": label if bug_driver else None,
            }
        )
    if metrics["effort_ratio"].score < MAX_METRIC_SCORE:
        actions.append(
            {
                "risk_type": "effort",
                "message": "Review estimate and scope for issues exceeding effort thresholds.",
                "drilldown_risk_type": "effort",
            }
        )
    if metrics["stale_rate"].score < MAX_METRIC_SCORE:
        actions.append(
            {
                "risk_type": "stale",
                "message": "Ask assignees to update stale issues immediately.",
                "drilldown_risk_type": "stale",
            }
        )
    if metrics["progress"].score < MAX_METRIC_SCORE:
        actions.append(
            {
                "risk_type": "progress",
                "message": "Review schedule and split large issues if actual progress is lagging.",
                "drilldown_risk_type": "progress",
            }
        )
    return actions[:4]


def build_early_warnings(
    *,
    metrics: dict[str, MetricResult],
    overdue_issues: list[Issue],
    today: date,
    previous_snapshots: list[DashboardHealthSnapshot],
    current_score: float,
    current_status: str,
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    previous_snapshot = previous_snapshots[0] if previous_snapshots else None
    two_previous = previous_snapshots[1] if len(previous_snapshots) > 1 else None

    if metrics["effort_ratio"].value is not None and metrics["effort_ratio"].value > 120.0:
        warnings.append({"code": "effort_ratio_over_120_percent", "level": "Critical", "message": "Effort Ratio exceeded 120%."})
    if metrics["stale_rate"].value is not None and metrics["stale_rate"].value > 15.0:
        warnings.append({"code": "stale_rate_over_15_percent", "level": "Warning", "message": "Stale Rate exceeded 15%."})
    high_priority_overdue = [
        issue for issue in overdue_issues if (issue.priority_name or "").strip().lower() in {"high", "critical"}
    ]
    if high_priority_overdue:
        warnings.append(
            {
                "code": "high_or_critical_issue_overdue",
                "level": "Critical",
                "message": f"{len(high_priority_overdue)} High/Critical issues are overdue.",
                "drilldown_risk_type": "overdue",
            }
        )

    if previous_snapshot is not None:
        previous_score = float(previous_snapshot.health_score)
        if two_previous is not None and current_score < previous_score < float(two_previous.health_score):
            warnings.append({"code": "score_down_2_periods", "level": "Warning", "message": "Health score decreased for 2 consecutive snapshots."})
        if previous_score >= 10 and current_status == "Yellow":
            warnings.append({"code": "score_green_to_yellow", "level": "Warning", "message": "Health score dropped from Green to Yellow."})
        if previous_score >= 7 and previous_score < 10 and current_status == "Red":
            warnings.append({"code": "score_yellow_to_red", "level": "Critical", "message": "Health score dropped from Yellow to Red."})
        previous_metric_values = previous_snapshot.metric_values_json or {}
        current_actual_progress = metrics["progress"].details.get("actual_progress_pct")
        if current_actual_progress is not None and len(previous_snapshots) >= 4:
            recent_progress_values = [
                current_actual_progress,
                previous_metric_values.get("progress", {}).get("details", {}).get("actual_progress_pct"),
                (previous_snapshots[1].metric_values_json or {}).get("progress", {}).get("details", {}).get("actual_progress_pct") if len(previous_snapshots) > 1 else None,
                (previous_snapshots[2].metric_values_json or {}).get("progress", {}).get("details", {}).get("actual_progress_pct") if len(previous_snapshots) > 2 else None,
                (previous_snapshots[3].metric_values_json or {}).get("progress", {}).get("details", {}).get("actual_progress_pct") if len(previous_snapshots) > 3 else None,
            ]
            if all(value is not None and value == current_actual_progress for value in recent_progress_values):
                warnings.append({"code": "progress_not_changed_5_snapshots", "level": "Warning", "message": "Progress did not change across 5 consecutive snapshots."})
        previous_overdue = previous_metric_values.get("overdue_rate", {}).get("value")
        current_overdue = metrics["overdue_rate"].value
        if (
            two_previous is not None
            and previous_overdue is not None
            and current_overdue is not None
        ):
            two_prev_overdue = (two_previous.metric_values_json or {}).get("overdue_rate", {}).get("value")
            if two_prev_overdue is not None and current_overdue > previous_overdue > two_prev_overdue:
                warnings.append({"code": "overdue_rate_up_2_periods", "level": "Warning", "message": "Overdue Rate increased for 2 consecutive snapshots."})
        previous_bug = previous_metric_values.get("bug_rate", {}).get("value")
        current_bug = metrics["bug_rate"].value
        if previous_bug not in (None, 0) and current_bug is not None:
            change_pct = ((current_bug - previous_bug) / previous_bug) * 100.0
            if change_pct > 20.0:
                warnings.append({"code": "bug_rate_up_over_20_percent", "level": "Warning", "message": "Bug Rate increased by more than 20%."})
        if two_previous is not None and current_score <= 6 and float(previous_snapshot.health_score) <= 6:
            warnings.append({"code": "score_red_2_periods", "level": "Critical", "message": "Health score stayed Red for 2 consecutive snapshots."})

    return warnings[:5]


def serialize_metric(metric: MetricResult) -> dict[str, Any]:
    return {
        "code": metric.code,
        "label": metric.label,
        "score": metric.score,
        "max_score": metric.max_score,
        "value": _safe_round(metric.value, 2),
        "value_display": metric.value_display,
        "benchmark": metric.benchmark,
        "drilldown_risk_type": metric.drilldown_risk_type,
        "details": metric.details,
    }


def _score_value(metric: MetricResult, weight: float) -> float:
    return metric.score * weight


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
    thresholds = config.metric_thresholds_json or default_metric_thresholds()
    weights = config.metric_weights_json or default_metric_weights()
    status_thresholds = config.health_status_thresholds_json or default_health_status_thresholds()
    bug_trackers = config.bug_tracker_names_json or DEFAULT_BUG_TRACKERS
    today = datetime.now(UTC).date()

    progress_metric = _progress_metric(issues, thresholds, today)
    closed_metric = _closed_rate_metric(issues, thresholds)
    overdue_metric, overdue_issues = _overdue_rate_metric(issues, thresholds, today)
    bug_metric, open_bugs = _bug_rate_metric(issues, thresholds, bug_trackers)
    effort_metric, high_effort_issues = _effort_metric(issues, thresholds)
    stale_metric, stale_issues = _stale_metric(issues, thresholds, today)

    metrics = {
        "progress": progress_metric,
        "closed_rate": closed_metric,
        "overdue_rate": overdue_metric,
        "bug_rate": bug_metric,
        "effort_ratio": effort_metric,
        "stale_rate": stale_metric,
    }

    weighted_raw_score = sum(_score_value(metric, float(weights.get(metric.code, 1))) for metric in metrics.values())
    max_weighted_raw_score = MAX_METRIC_SCORE * sum(float(weights.get(metric.code, 1)) for metric in metrics.values())
    normalized_score = 0.0 if max_weighted_raw_score <= 0 else round((weighted_raw_score / max_weighted_raw_score) * MAX_HEALTH_SCORE, 2)
    status = _metric_status(normalized_score, status_thresholds)

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
    if len(previous_snapshots) >= 2:
        current_trend_value = round(
            float(previous_snapshots[0].health_score) - float(previous_snapshots[1].health_score),
            2,
        )

    risk_drivers = build_risk_drivers(
        metrics,
        overdue_issues=overdue_issues,
        open_bugs=open_bugs,
        high_effort_issues=high_effort_issues,
        stale_issues=stale_issues,
    )
    suggested_actions = build_suggested_actions(metrics, risk_drivers)
    early_warnings = build_early_warnings(
        metrics=metrics,
        overdue_issues=overdue_issues,
        today=today,
        previous_snapshots=previous_snapshots,
        current_score=normalized_score,
        current_status=status,
    )

    open_count = sum(1 for issue in issues if not issue.is_closed)
    closed_count = sum(1 for issue in issues if issue.is_closed)

    return {
        "total_issues": len(issues),
        "open_issues": open_count,
        "closed_issues": closed_count,
        "overdue_issues": len(overdue_issues),
        "health_summary": {
            "score": normalized_score,
            "max_score": MAX_HEALTH_SCORE,
            "status": status,
            "trend_value": current_trend_value,
            "trend_direction": _trend_direction(current_trend_value),
        },
        "metrics": [serialize_metric(metric) for metric in metrics.values()],
        "main_risk_drivers": risk_drivers,
        "suggested_actions": suggested_actions,
        "early_warnings": early_warnings,
        "health_trend": trend_items,
        "metric_scores_json": {key: serialize_metric(value) for key, value in metrics.items()},
        "metric_values_json": {
            key: {
                "value": _safe_round(value.value, 2),
                "value_display": value.value_display,
                "details": value.details,
            }
            for key, value in metrics.items()
        },
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
            health_score=float(summary["health_summary"]["score"]),
            health_status=str(summary["health_summary"]["status"]),
            metric_scores_json=summary["metric_scores_json"],
            metric_values_json=summary["metric_values_json"],
            main_risk_drivers_json=summary["main_risk_drivers"],
            warnings_json=summary["early_warnings"],
            suggested_actions_json=summary["suggested_actions"],
        )
        session.add(snapshot)
        await session.commit()
