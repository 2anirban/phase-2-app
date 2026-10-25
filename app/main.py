"""HTTP routes and request logging. Start with: python -m uvicorn app.main:app"""

import logging
import re
import socket
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.responses import JSONResponse

from app.config import Settings
from app.github_client import Repository, create_github_client, fetch_repository

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("fde-api")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an application; explicit settings also make later tests independent."""
    config = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        # Reuse outgoing connections across requests and close them on shutdown.
        async with create_github_client(config) as client:
            application.state.github_client = client
            application.state.ready = True
            try:
                yield
            finally:
                application.state.ready = False

    application = FastAPI(title="FDE Deployment Lab", version=config.app_version, lifespan=lifespan)
    application.state.ready = False

    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        supplied_id = request.headers.get("x-request-id", "")
        request_id = supplied_id if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", supplied_id) else str(uuid.uuid4())
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log the error type, not exception text that might contain credentials.
            logger.error("request_failed type=%s request_id=%s", type(exc).__name__, request_id)
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
        response.headers["x-request-id"] = request_id
        route = request.scope.get("route")
        logger.info(
            "method=%s route=%s status=%s latency_ms=%.1f request_id=%s",
            request.method,
            getattr(route, "path", "unmatched"),
            response.status_code,
            (time.perf_counter() - start) * 1000,
            request_id,
        )
        return response

    @application.get("/health/live", summary="Check that the application responds")
    async def live() -> dict[str, str]:
        # Liveness does not call GitHub, the database or AWS.
        return {"status": "alive", "version": config.app_version}

    @application.get("/health/ready", summary="Check that local application startup completed")
    async def ready() -> dict[str, str]:
        if not application.state.ready:
            raise HTTPException(status_code=503, detail="Application is not ready")
        return {"status": "ready"}

    @application.get("/version", summary="Identify the application version and environment")
    async def version() -> dict[str, str]:
        return {
            "version": config.app_version,
            "environment": config.environment,
            "hostname": socket.gethostname(),
        }

    @application.get("/repos/{owner}/{repo}", response_model=Repository, summary="Get a GitHub repository")
    async def repository(
        request: Request,
        owner: Annotated[str, Path(min_length=1, max_length=39, pattern=r"^[A-Za-z0-9-]+$")],
        repo: Annotated[str, Path(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")],
    ) -> Repository:
        return await fetch_repository(request.app.state.github_client, owner, repo)

    return application


app = create_app()
