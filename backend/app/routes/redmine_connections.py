from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.core.crypto import decrypt_secret, encrypt_secret
from app.db.session import AsyncSessionLocal
from app.middleware.auth import require_admin
from app.models.redmine_connection import RedmineConnection
from app.models.user import User
from app.schemas.redmine_connection import (
    RedmineConnectionCreate,
    RedmineConnectionResponse,
    RedmineConnectionTestResponse,
    RedmineConnectionUpdate,
)
from app.services.redmine_client import fetch_redmine_account

router = APIRouter()


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


@router.get("/current", response_model=RedmineConnectionResponse)
async def get_current_connection(_: User = Depends(require_admin)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RedmineConnection).order_by(RedmineConnection.id.desc())
        )
        connection = result.scalars().first()
        if not connection:
            raise HTTPException(status_code=404, detail="Redmine connection not found")
        return connection


@router.post("", response_model=RedmineConnectionResponse, status_code=201)
async def create_connection(
    payload: RedmineConnectionCreate,
    admin: User = Depends(require_admin),
):
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(RedmineConnection.id).limit(1))
        if existing.first():
            return JSONResponse(
                status_code=409,
                content={
                    "code": "REDMINE_CONNECTION_ALREADY_EXISTS",
                    "message": "Only one Redmine connection is supported.",
                },
            )

        connection = RedmineConnection(
            name=payload.name.strip(),
            base_url=normalize_base_url(str(payload.base_url)),
            identifier=payload.identifier.strip(),
            encrypted_api_key=encrypt_secret(payload.api_key),
            status="untested",
            created_by=admin.id,
        )
        session.add(connection)
        await session.commit()
        await session.refresh(connection)
        return connection


@router.patch("/{connection_id}", response_model=RedmineConnectionResponse)
async def update_connection(
    connection_id: int,
    payload: RedmineConnectionUpdate,
    _: User = Depends(require_admin),
):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RedmineConnection).where(RedmineConnection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        if not connection:
            raise HTTPException(status_code=404, detail="Redmine connection not found")

        reset_status = False

        if payload.name is not None:
            connection.name = payload.name.strip()
        if payload.base_url is not None:
            normalized_url = normalize_base_url(str(payload.base_url))
            if normalized_url != connection.base_url:
                connection.base_url = normalized_url
                reset_status = True
        if payload.identifier is not None:
            normalized_identifier = payload.identifier.strip()
            if normalized_identifier != connection.identifier:
                connection.identifier = normalized_identifier
                reset_status = True
        if payload.api_key is not None:
            connection.encrypted_api_key = encrypt_secret(payload.api_key)
            reset_status = True

        if reset_status:
            connection.status = "untested"
            connection.last_tested_at = None

        await session.commit()
        await session.refresh(connection)
        return connection


@router.post("/{connection_id}/test", response_model=RedmineConnectionTestResponse)
async def test_connection(
    connection_id: int,
    _: User = Depends(require_admin),
):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RedmineConnection).where(RedmineConnection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        if not connection:
            raise HTTPException(status_code=404, detail="Redmine connection not found")

        now = datetime.now(timezone.utc)
        api_key = decrypt_secret(connection.encrypted_api_key)

        try:
            response = await fetch_redmine_account(connection.base_url, api_key)
        except httpx.TimeoutException:
            connection.status = "failed"
            connection.last_tested_at = now
            await session.commit()
            return JSONResponse(
                status_code=504,
                content={
                    "code": "REDMINE_TIMEOUT",
                    "message": "Timed out while connecting to Redmine",
                },
            )
        except httpx.HTTPError:
            connection.status = "failed"
            connection.last_tested_at = now
            await session.commit()
            return JSONResponse(
                status_code=502,
                content={
                    "code": "REDMINE_BAD_GATEWAY",
                    "message": "Could not reach Redmine",
                },
            )

        connection.last_tested_at = now

        if response.status_code == 200:
            payload = response.json()
            connection.status = "active"
            await session.commit()
            redmine_user = payload.get("user", {})
            return {
                "success": True,
                "message": "Connection successful",
                "status": connection.status,
                "redmine_user": {
                    "id": redmine_user.get("id"),
                    "login": redmine_user.get("login"),
                    "firstname": redmine_user.get("firstname"),
                },
                "last_tested_at": connection.last_tested_at,
            }

        connection.status = "failed"
        await session.commit()

        if response.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={
                    "code": "REDMINE_UNAUTHORIZED",
                    "message": "Invalid Redmine API key",
                },
            )
        if response.status_code == 403:
            return JSONResponse(
                status_code=403,
                content={
                    "code": "REDMINE_FORBIDDEN",
                    "message": "Redmine user does not have permission",
                },
            )

        return JSONResponse(
            status_code=502,
            content={
                "code": "REDMINE_BAD_GATEWAY",
                "message": f"Unexpected Redmine status: {response.status_code}",
            },
        )
