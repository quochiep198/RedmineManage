from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    connection_id: int
    redmine_project_id: int
    identifier: str
    name: str
    description: str | None
    is_active: bool
    last_synced_at: datetime
    created_at: datetime
    updated_at: datetime


class ProjectSyncResponse(BaseModel):
    success: bool
    total_synced: int
    created: int
    updated: int
    connection_id: int
    identifier: str
    synced_at: datetime


class ProjectSyncStatusResponse(BaseModel):
    shared_connection_name: str
    connection_id: int
    identifier: str
    last_sync_at: datetime | None
    last_status: str | None
    last_result: dict[str, int] | None
