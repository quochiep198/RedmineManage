from datetime import date, datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select

from app.core.config import settings
from app.core.crypto import decrypt_secret
from app.db.session import AsyncSessionLocal
from app.middleware.auth import get_current_user, require_admin
from app.models.issue import Issue
from app.models.issue_sync_log import IssueSyncLog
from app.models.project import Project
from app.models.redmine_connection import RedmineConnection
from app.models.user import User
from app.schemas.issue import (
    IssueFilterOptionsResponse,
    IssueListItemResponse,
    IssueListResponse,
    IssueFilterOption,
    IssueSyncResponse,
    IssueSyncStatusResponse,
)
from app.services.redmine_client import build_redmine_issue_url, fetch_redmine_issues

router = APIRouter()

REDMINE_ISSUES_PAGE_SIZE = 100


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


def parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def extract_named_entity(payload: dict | None) -> tuple[int | None, str | None]:
    if not payload:
        return None, None
    return payload.get("id"), payload.get("name")


def derive_is_closed(item: dict) -> bool:
    status = item.get("status") or {}
    status_id = status.get("id")
    return status_id in set(settings.closed_status_ids)


async def write_sync_log(
    *,
    connection_id: int | None,
    project_id: int | None,
    status: str,
    started_at: datetime,
    finished_at: datetime,
    error_code: str | None = None,
    error_message: str | None = None,
    total_synced: int | None = None,
    created_count: int | None = None,
    updated_count: int | None = None,
):
    async with AsyncSessionLocal() as session:
        session.add(
            IssueSyncLog(
                connection_id=connection_id,
                project_id=project_id,
                status=status,
                error_code=error_code,
                error_message=error_message,
                total_synced=total_synced,
                created_count=created_count,
                updated_count=updated_count,
                started_at=started_at,
                finished_at=finished_at,
            )
        )
        await session.commit()


@router.get("/sync/status", response_model=IssueSyncStatusResponse)
async def get_issue_sync_status(_: User = Depends(require_admin)):
    async with AsyncSessionLocal() as session:
        connection = await get_current_connection(session)
        if not connection:
            return JSONResponse(
                status_code=404,
                content={"detail": "Redmine connection not found"},
            )

        project = await get_current_project(session, connection)
        log_result = await session.execute(
            select(IssueSyncLog)
            .where(IssueSyncLog.connection_id == connection.id)
            .order_by(IssueSyncLog.finished_at.desc())
        )
        last_log = log_result.scalars().first()

        return {
            "shared_connection_name": connection.name,
            "project_identifier": connection.identifier,
            "project_name": project.name if project else None,
            "last_sync_at": last_log.finished_at if last_log else None,
            "last_status": last_log.status if last_log else None,
            "last_result": (
                {
                    "total_synced": last_log.total_synced or 0,
                    "created": last_log.created_count or 0,
                    "updated": last_log.updated_count or 0,
                }
                if last_log
                else None
            ),
        }


@router.get("/filters", response_model=IssueFilterOptionsResponse)
async def get_issue_filter_options(_: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        connection = await get_current_connection(session)
        project = await get_current_project(session, connection)
        if not connection or not project:
            return {
                "statuses": [],
                "priorities": [],
            }

        status_result = await session.execute(
            select(Issue.status_id, Issue.status_name)
            .where(
                Issue.connection_id == connection.id,
                Issue.project_id == project.id,
                Issue.status_id.is_not(None),
                Issue.status_name.is_not(None),
            )
            .distinct()
            .order_by(Issue.status_name.asc())
        )
        priority_result = await session.execute(
            select(Issue.priority_id, Issue.priority_name)
            .where(
                Issue.connection_id == connection.id,
                Issue.project_id == project.id,
                Issue.priority_id.is_not(None),
                Issue.priority_name.is_not(None),
            )
            .distinct()
            .order_by(Issue.priority_name.asc())
        )

        return {
            "statuses": [
                IssueFilterOption(id=status_id, name=status_name)
                for status_id, status_name in status_result.all()
                if status_id is not None and status_name
            ],
            "priorities": [
                IssueFilterOption(id=priority_id, name=priority_name)
                for priority_id, priority_name in priority_result.all()
                if priority_id is not None and priority_name
            ],
        }


@router.post("/sync", response_model=IssueSyncResponse)
async def sync_issues(_: User = Depends(require_admin)):
    return await perform_issue_sync()


async def perform_issue_sync():
    started_at = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        connection = await get_current_connection(session)
        if not connection or not connection.identifier.strip():
            await write_sync_log(
                connection_id=connection.id if connection else None,
                project_id=None,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                error_code="REDMINE_CONNECTION_NOT_CONFIGURED",
                error_message="Redmine connection is not configured",
            )
            return JSONResponse(
                status_code=409,
                content={
                    "code": "REDMINE_CONNECTION_NOT_CONFIGURED",
                    "message": "Redmine connection is not configured",
                },
            )

        project = await get_current_project(session, connection)
        if not project:
            await write_sync_log(
                connection_id=connection.id,
                project_id=None,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                error_code="PROJECT_NOT_SYNCED",
                error_message="Current project is not synced",
            )
            return JSONResponse(
                status_code=409,
                content={
                    "code": "PROJECT_NOT_SYNCED",
                    "message": "Current project is not synced",
                },
            )

        api_key = decrypt_secret(connection.encrypted_api_key)
        synced_at = datetime.now(timezone.utc)
        total_synced = 0
        created_count = 0
        updated_count = 0
        offset = 0

        try:
            while True:
                response = await fetch_redmine_issues(
                    connection.base_url,
                    api_key,
                    connection.identifier,
                    limit=REDMINE_ISSUES_PAGE_SIZE,
                    offset=offset,
                )

                if response.status_code != 200:
                    await write_sync_log(
                        connection_id=connection.id,
                        project_id=project.id,
                        status="failed",
                        started_at=started_at,
                        finished_at=datetime.now(timezone.utc),
                        error_code="REDMINE_SYNC_FAILED",
                        error_message=f"Unexpected Redmine status: {response.status_code}",
                    )
                    return JSONResponse(
                        status_code=502,
                        content={
                            "code": "REDMINE_SYNC_FAILED",
                            "message": "Failed to sync issues from Redmine",
                        },
                    )

                payload = response.json()
                items = payload.get("issues") or []
                total_count = int(payload.get("total_count") or len(items))
                current_limit = int(payload.get("limit") or REDMINE_ISSUES_PAGE_SIZE)
                current_offset = int(payload.get("offset") or offset)

                for item in items:
                    tracker_id, tracker_name = extract_named_entity(item.get("tracker"))
                    status_id, status_name = extract_named_entity(item.get("status"))
                    priority_id, priority_name = extract_named_entity(item.get("priority"))
                    author_id, author_name = extract_named_entity(item.get("author"))
                    assignee_id, assignee_name = extract_named_entity(item.get("assigned_to"))

                    result = await session.execute(
                        select(Issue).where(
                            Issue.connection_id == connection.id,
                            Issue.redmine_issue_id == item["id"],
                        )
                    )
                    issue = result.scalar_one_or_none()

                    if issue is None:
                        issue = Issue(
                            connection_id=connection.id,
                            project_id=project.id,
                            redmine_issue_id=item["id"],
                            tracker_id=tracker_id,
                            tracker_name=tracker_name,
                            status_id=status_id,
                            status_name=status_name,
                            priority_id=priority_id,
                            priority_name=priority_name,
                            author_id=author_id,
                            author_name=author_name,
                            assignee_id=assignee_id,
                            assignee_name=assignee_name,
                            subject=item.get("subject") or f"Issue {item['id']}",
                            description=item.get("description"),
                            start_date=parse_optional_date(item.get("start_date")),
                            due_date=parse_optional_date(item.get("due_date")),
                            done_ratio=item.get("done_ratio"),
                            estimated_hours=item.get("estimated_hours"),
                            spent_hours=item.get("spent_hours"),
                            is_closed=derive_is_closed(item),
                            redmine_created_on=parse_optional_datetime(item.get("created_on")),
                            redmine_updated_on=parse_optional_datetime(item.get("updated_on")),
                            raw_data_json=item,
                            last_synced_at=synced_at,
                        )
                        session.add(issue)
                        created_count += 1
                    else:
                        issue.project_id = project.id
                        issue.tracker_id = tracker_id
                        issue.tracker_name = tracker_name
                        issue.status_id = status_id
                        issue.status_name = status_name
                        issue.priority_id = priority_id
                        issue.priority_name = priority_name
                        issue.author_id = author_id
                        issue.author_name = author_name
                        issue.assignee_id = assignee_id
                        issue.assignee_name = assignee_name
                        issue.subject = item.get("subject") or issue.subject
                        issue.description = item.get("description")
                        issue.start_date = parse_optional_date(item.get("start_date"))
                        issue.due_date = parse_optional_date(item.get("due_date"))
                        issue.done_ratio = item.get("done_ratio")
                        issue.estimated_hours = item.get("estimated_hours")
                        issue.spent_hours = item.get("spent_hours")
                        issue.is_closed = derive_is_closed(item)
                        issue.redmine_created_on = parse_optional_datetime(item.get("created_on"))
                        issue.redmine_updated_on = parse_optional_datetime(item.get("updated_on"))
                        issue.raw_data_json = item
                        issue.last_synced_at = synced_at
                        updated_count += 1

                total_synced += len(items)
                if total_synced >= total_count or not items:
                    break
                offset = current_offset + current_limit
        except httpx.TimeoutException:
            await session.rollback()
            await write_sync_log(
                connection_id=connection.id,
                project_id=project.id,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                error_code="REDMINE_TIMEOUT",
                error_message="Timed out while syncing issues from Redmine",
            )
            return JSONResponse(
                status_code=504,
                content={
                    "code": "REDMINE_TIMEOUT",
                    "message": "Timed out while syncing issues from Redmine",
                },
            )
        except httpx.HTTPError:
            await session.rollback()
            await write_sync_log(
                connection_id=connection.id,
                project_id=project.id,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                error_code="REDMINE_SYNC_FAILED",
                error_message="Failed to sync issues from Redmine",
            )
            return JSONResponse(
                status_code=502,
                content={
                    "code": "REDMINE_SYNC_FAILED",
                    "message": "Failed to sync issues from Redmine",
                },
            )

        await session.commit()

    await write_sync_log(
        connection_id=connection.id,
        project_id=project.id,
        status="success",
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        total_synced=total_synced,
        created_count=created_count,
        updated_count=updated_count,
    )

    return {
        "success": True,
        "project_identifier": connection.identifier,
        "total_synced": total_synced,
        "created": created_count,
        "updated": updated_count,
        "synced_at": synced_at,
    }


@router.get("", response_model=IssueListResponse)
async def list_issues(
    _: User = Depends(get_current_user),
    status_id: int | None = Query(default=None),
    priority_id: int | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    due_date_from: date | None = Query(default=None),
    due_date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    async with AsyncSessionLocal() as session:
        connection = await get_current_connection(session)
        project = await get_current_project(session, connection)
        if not connection or not project:
            return {
                "items": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
            }

        stmt = select(Issue).where(
            Issue.connection_id == connection.id,
            Issue.project_id == project.id,
        )

        if status_id is not None:
            stmt = stmt.where(Issue.status_id == status_id)
        if priority_id is not None:
            stmt = stmt.where(Issue.priority_id == priority_id)
        if assignee_id is not None:
            stmt = stmt.where(Issue.assignee_id == assignee_id)
        if keyword:
            like_value = f"%{keyword.strip()}%"
            stmt = stmt.where(
                or_(
                    Issue.subject.ilike(like_value),
                    Issue.description.ilike(like_value),
                )
            )
        if due_date_from is not None:
            stmt = stmt.where(Issue.due_date >= due_date_from)
        if due_date_to is not None:
            stmt = stmt.where(Issue.due_date <= due_date_to)

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = await session.scalar(count_stmt)

        stmt = (
            stmt.order_by(Issue.redmine_updated_on.desc(), Issue.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        issues = result.scalars().all()

        return {
            "items": [
                IssueListItemResponse(
                    id=issue.id,
                    connection_id=issue.connection_id,
                    project_id=issue.project_id,
                    redmine_issue_id=issue.redmine_issue_id,
                    tracker_id=issue.tracker_id,
                    tracker_name=issue.tracker_name,
                    status_id=issue.status_id,
                    status_name=issue.status_name,
                    priority_id=issue.priority_id,
                    priority_name=issue.priority_name,
                    author_id=issue.author_id,
                    author_name=issue.author_name,
                    assignee_id=issue.assignee_id,
                    assignee_name=issue.assignee_name,
                    subject=issue.subject,
                    description=issue.description,
                    start_date=issue.start_date,
                    due_date=issue.due_date,
                    done_ratio=issue.done_ratio,
                    estimated_hours=issue.estimated_hours,
                    spent_hours=issue.spent_hours,
                    is_closed=issue.is_closed,
                    redmine_url=build_redmine_issue_url(connection.base_url, issue.redmine_issue_id),
                    redmine_created_on=issue.redmine_created_on,
                    redmine_updated_on=issue.redmine_updated_on,
                    last_synced_at=issue.last_synced_at,
                    created_at=issue.created_at,
                    updated_at=issue.updated_at,
                )
                for issue in issues
            ],
            "page": page,
            "page_size": page_size,
            "total": total or 0,
        }
