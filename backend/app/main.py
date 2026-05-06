import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text

from app.core.config import settings
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.dashboard_health_config import DashboardHealthConfig
from app.models.dashboard_health_snapshot import DashboardHealthSnapshot
from app.models.issue import Issue
from app.models.issue_status_transition import IssueStatusTransition
from app.models.issue_sync_log import IssueSyncLog
from app.models.project import Project
from app.models.project_sync_log import ProjectSyncLog
from app.models.redmine_connection import RedmineConnection
from app.models.user import User
from app.routes import auth, dashboard, health, issues, projects, redmine_connections
from app.services.dashboard_health import ensure_default_health_config

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["set-cookie"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(
    redmine_connections.router,
    prefix="/api/redmine/connections",
    tags=["redmine-connections"],
)
app.include_router(
    projects.router,
    prefix="/api/projects",
    tags=["projects"],
)
app.include_router(
    issues.router,
    prefix="/api/issues",
    tags=["issues"],
)
app.include_router(
    dashboard.router,
    prefix="/api/dashboard",
    tags=["dashboard"],
)


def _has_column(sync_conn, table_name: str, column_name: str) -> bool:
    inspector = inspect(sync_conn)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        has_is_admin = await conn.run_sync(_has_column, "users", "is_admin")
        if not has_is_admin:
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE")
            )
        has_identifier = await conn.run_sync(_has_column, "redmine_connections", "identifier")
        if not has_identifier:
            await conn.execute(
                text("ALTER TABLE redmine_connections ADD COLUMN identifier VARCHAR(255) NOT NULL DEFAULT ''")
            )

    async with AsyncSessionLocal() as session:
        await ensure_default_health_config(session)
        result = await session.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()
        if admin_user is None:
            hashed = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("utf-8")
            session.add(
                User(
                    username="admin",
                    password=hashed,
                    is_active=True,
                    is_admin=True,
                )
            )
        else:
            if not admin_user.is_admin:
                admin_user.is_admin = True
        await session.commit()


@app.get("/")
async def root():
    return {"message": "Redmine Simple Starter API"}
