from datetime import date, datetime

from pydantic import BaseModel


class IssueListItemResponse(BaseModel):
    id: int
    connection_id: int
    project_id: int
    redmine_issue_id: int
    tracker_id: int | None
    tracker_name: str | None
    status_id: int | None
    status_name: str | None
    priority_id: int | None
    priority_name: str | None
    author_id: int | None
    author_name: str | None
    assignee_id: int | None
    assignee_name: str | None
    subject: str
    description: str | None
    start_date: date | None
    due_date: date | None
    done_ratio: int | None
    estimated_hours: float | None
    spent_hours: float | None
    is_closed: bool
    redmine_url: str
    redmine_created_on: datetime | None
    redmine_updated_on: datetime | None
    last_synced_at: datetime
    created_at: datetime
    updated_at: datetime


class IssueListResponse(BaseModel):
    items: list[IssueListItemResponse]
    page: int
    page_size: int
    total: int


class IssueSyncResponse(BaseModel):
    success: bool
    project_identifier: str
    total_synced: int
    created: int
    updated: int
    deleted: int
    synced_at: datetime


class IssueSyncStatusResponse(BaseModel):
    shared_connection_name: str
    project_identifier: str
    project_name: str | None
    last_sync_at: datetime | None
    last_status: str | None
    last_result: dict[str, int] | None


class IssueFilterOption(BaseModel):
    id: int
    name: str


class IssueFilterOptionsResponse(BaseModel):
    statuses: list[IssueFilterOption]
    priorities: list[IssueFilterOption]
