from urllib.parse import urlsplit, urlunsplit

import httpx

from app.core.config import settings


def _build_url(base_url: str, suffix: str) -> str:
    parts = urlsplit(base_url.rstrip("/"))
    normalized_path = parts.path.rstrip("/")
    target_path = f"{normalized_path}/{suffix}" if normalized_path else f"/{suffix}"
    return urlunsplit((parts.scheme, parts.netloc, target_path, "", ""))


def build_redmine_account_url(base_url: str) -> str:
    return _build_url(base_url, "my/account.json")


def build_redmine_projects_url(base_url: str) -> str:
    return _build_url(base_url, "projects.json")


def build_redmine_project_url(base_url: str, identifier: str) -> str:
    return _build_url(base_url, f"projects/{identifier}.json")


def build_redmine_issue_url(base_url: str, issue_id: int) -> str:
    return _build_url(base_url, f"issues/{issue_id}")


def build_redmine_issue_detail_url(base_url: str, issue_id: int) -> str:
    return _build_url(base_url, f"issues/{issue_id}.json")


async def fetch_redmine_account(base_url: str, api_key: str) -> httpx.Response:
    url = build_redmine_account_url(base_url)
    async with httpx.AsyncClient(timeout=settings.REDMINE_TIMEOUT_SECONDS) as client:
        return await client.get(
            url,
            headers={"X-Redmine-API-Key": api_key},
        )


async def fetch_redmine_projects(base_url: str, api_key: str) -> httpx.Response:
    url = build_redmine_projects_url(base_url)
    async with httpx.AsyncClient(timeout=settings.REDMINE_TIMEOUT_SECONDS) as client:
        return await client.get(
            url,
            headers={"X-Redmine-API-Key": api_key},
        )


async def fetch_redmine_project(base_url: str, api_key: str, identifier: str) -> httpx.Response:
    url = build_redmine_project_url(base_url, identifier)
    async with httpx.AsyncClient(timeout=settings.REDMINE_TIMEOUT_SECONDS) as client:
        return await client.get(
            url,
            headers={"X-Redmine-API-Key": api_key},
        )


async def fetch_redmine_issues(
    base_url: str,
    api_key: str,
    project_identifier: str,
    *,
    limit: int,
    offset: int,
) -> httpx.Response:
    url = _build_url(base_url, "issues.json")
    async with httpx.AsyncClient(timeout=settings.REDMINE_TIMEOUT_SECONDS) as client:
        return await client.get(
            url,
            params={
                "project_id": project_identifier,
                "status_id": "*",
                "limit": limit,
                "offset": offset,
            },
            headers={"X-Redmine-API-Key": api_key},
        )


async def fetch_redmine_issue_detail(
    base_url: str,
    api_key: str,
    issue_id: int,
    *,
    include: str | None = None,
) -> httpx.Response:
    url = build_redmine_issue_detail_url(base_url, issue_id)
    params = {"include": include} if include else None
    async with httpx.AsyncClient(timeout=settings.REDMINE_TIMEOUT_SECONDS) as client:
        return await client.get(
            url,
            params=params,
            headers={"X-Redmine-API-Key": api_key},
        )
