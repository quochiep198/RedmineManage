from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.core.crypto import decrypt_secret
from app.db.session import AsyncSessionLocal
from app.middleware.auth import get_current_user, require_admin
from app.models.project import Project
from app.models.project_sync_log import ProjectSyncLog
from app.models.redmine_connection import RedmineConnection
from app.models.user import User
from app.schemas.project import ProjectResponse, ProjectSyncResponse, ProjectSyncStatusResponse
from app.services.redmine_client import fetch_redmine_project

router = APIRouter()


async def get_current_connection(session) -> RedmineConnection | None:
    result = await session.execute(select(RedmineConnection).order_by(RedmineConnection.id.desc()))
    return result.scalars().first()


async def write_sync_log(
    *,
    connection_id: int | None,
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
            ProjectSyncLog(
                connection_id=connection_id,
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


@router.get("/sync/status", response_model=ProjectSyncStatusResponse)
async def get_sync_status(_: User = Depends(require_admin)):
    async with AsyncSessionLocal() as session:
        connection = await get_current_connection(session)
        if not connection:
            raise HTTPException(status_code=404, detail="Redmine connection not found")

        log_result = await session.execute(
            select(ProjectSyncLog)
            .where(ProjectSyncLog.connection_id == connection.id)
            .order_by(ProjectSyncLog.finished_at.desc())
        )
        last_log = log_result.scalars().first()

        return {
            "shared_connection_name": connection.name,
            "connection_id": connection.id,
            "identifier": connection.identifier,
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


@router.post("/sync", response_model=ProjectSyncResponse)
async def sync_projects(_: User = Depends(require_admin)):
    started_at = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        connection = await get_current_connection(session)
        if not connection or not connection.identifier.strip():
            await write_sync_log(
                connection_id=connection.id if connection else None,
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

        api_key = decrypt_secret(connection.encrypted_api_key)
        synced_at = datetime.now(timezone.utc)

        try:
            response = await fetch_redmine_project(connection.base_url, api_key, connection.identifier)
        except httpx.TimeoutException:
            await write_sync_log(
                connection_id=connection.id,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                error_code="REDMINE_TIMEOUT",
                error_message="Timed out while syncing projects from Redmine",
            )
            return JSONResponse(
                status_code=504,
                content={
                    "code": "REDMINE_TIMEOUT",
                    "message": "Timed out while syncing projects from Redmine",
                },
            )
        except httpx.HTTPError:
            await write_sync_log(
                connection_id=connection.id,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                error_code="REDMINE_SYNC_FAILED",
                error_message="Failed to sync projects from Redmine",
            )
            return JSONResponse(
                status_code=502,
                content={
                    "code": "REDMINE_SYNC_FAILED",
                    "message": "Failed to sync projects from Redmine",
                },
            )

        if response.status_code != 200:
            await write_sync_log(
                connection_id=connection.id,
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
                    "message": "Failed to sync projects from Redmine",
                },
            )

        payload = response.json()
        item = payload.get("project")
        if not item:
            await write_sync_log(
                connection_id=connection.id,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                error_code="REDMINE_SYNC_FAILED",
                error_message="Project payload missing from Redmine response",
            )
            return JSONResponse(
                status_code=502,
                content={
                    "code": "REDMINE_SYNC_FAILED",
                    "message": "Failed to sync projects from Redmine",
                },
            )

        result = await session.execute(
            select(Project).where(
                Project.connection_id == connection.id,
                Project.redmine_project_id == item["id"],
            )
        )
        project = result.scalar_one_or_none()
        created_count = 0
        updated_count = 0

        if project is None:
            project = Project(
                connection_id=connection.id,
                redmine_project_id=item["id"],
                identifier=item["identifier"],
                name=item["name"],
                description=item.get("description"),
                is_active=True,
                raw_data_json=item,
                last_synced_at=synced_at,
            )
            session.add(project)
            created_count = 1
        else:
            project.identifier = item["identifier"]
            project.name = item["name"]
            project.description = item.get("description")
            project.is_active = True
            project.raw_data_json = item
            project.last_synced_at = synced_at
            updated_count = 1

        await session.commit()

    await write_sync_log(
        connection_id=connection.id,
        status="success",
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        total_synced=1,
        created_count=created_count,
        updated_count=updated_count,
    )

    return {
        "success": True,
        "total_synced": 1,
        "created": created_count,
        "updated": updated_count,
        "connection_id": connection.id,
        "identifier": connection.identifier,
        "synced_at": synced_at,
    }


@router.get("/current", response_model=ProjectResponse)
async def get_current_project(_: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        connection = await get_current_connection(session)
        if not connection or not connection.identifier.strip():
            raise HTTPException(status_code=404, detail="Current project not found")

        result = await session.execute(
            select(Project).where(
                Project.connection_id == connection.id,
                Project.identifier == connection.identifier,
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Current project not found")
        return ProjectResponse.model_validate(project)
