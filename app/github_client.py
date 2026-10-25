"""Call GitHub and translate upstream failures into predictable API responses."""

from urllib.parse import quote

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, HttpUrl

from app.config import Settings


class Repository(BaseModel):
    """The small repository summary returned by our API."""

    name: str
    stars: int = Field(ge=0, strict=True)
    forks: int = Field(ge=0, strict=True)
    url: HttpUrl


def create_github_client(settings: Settings) -> httpx.AsyncClient:
    """Create one connection pool, owned and closed by the application lifespan."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "fde-deployment-lab/1.0",
    }
    if settings.github_token and settings.github_token.get_secret_value():
        headers["Authorization"] = f"Bearer {settings.github_token.get_secret_value()}"

    return httpx.AsyncClient(
        base_url=str(settings.github_api_base).rstrip("/") + "/",
        headers=headers,
        timeout=httpx.Timeout(settings.outbound_timeout_s),
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        follow_redirects=False,
    )


def is_rate_limited(response: httpx.Response) -> bool:
    if response.status_code == 429:
        return True
    if response.status_code != 403:
        return False
    if response.headers.get("x-ratelimit-remaining") == "0" or "retry-after" in response.headers:
        return True
    try:
        body = response.json()
    except ValueError:
        return False
    return isinstance(body, dict) and "rate limit" in str(body.get("message", "")).lower()


async def fetch_repository(client: httpx.AsyncClient, owner: str, repo: str) -> Repository:
    """Fetch one repository; never return upstream response bodies or tokens on errors."""
    # Dot-only segments would change URL path semantics rather than name a repository.
    if owner in {".", ".."} or repo in {".", ".."}:
        raise HTTPException(status_code=422, detail="Invalid repository path")
    path = f"repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
    try:
        response = await client.get(path)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="GitHub upstream timeout") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="GitHub upstream unreachable") from exc

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Repository not found")
    if is_rate_limited(response):
        retry_after = response.headers.get("retry-after", "")
        headers = {"Retry-After": retry_after} if retry_after.isascii() and retry_after.isdecimal() else None
        raise HTTPException(status_code=503, detail="GitHub upstream rate limited", headers=headers)
    if response.status_code in {401, 403}:
        raise HTTPException(status_code=502, detail="GitHub upstream access denied")
    if response.status_code >= 500:
        raise HTTPException(status_code=502, detail="GitHub upstream server failure")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Unexpected GitHub upstream response")

    try:
        data = response.json()
        return Repository(
            name=data["full_name"],
            stars=data["stargazers_count"],
            forks=data["forks_count"],
            url=data["html_url"],
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Invalid GitHub upstream response") from exc
