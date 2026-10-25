# Phase 2 execution record — what we have completed so far

**Recorded through 26 October 2026, Asia/Calcutta.** This is the execution companion
to [sprint_phase2.md](sprint_phase2.md). The sprint workbook describes the whole
project; this file records the work completed so far, its code, commands, explanations,
observed results and troubleshooting. It is not a claim that future AWS stages ran.

Our project lives at:

```text
C:\Users\user\Desktop\Project_Imp_All_FDE\Networking_AWS\phase_2_app
```

Our GitHub repository is [2anirban/phase-2-app](https://github.com/2anirban/phase-2-app).
It was created as a public repository. No application deployment to AWS has occurred.

## How to read this record

- Each completed stage has the same sprint number as the workbook: goal, what we
  did, file contents, commands and their meanings, evidence and completion status.
- **Observed** means supported by terminal output, screenshots, inspected files,
  Git history or implementation checks from this session.
- **Repeat/reference** means an equivalent command supplied for understanding or
  repeating the work. It is not presented as an exact historical command transcript.
  Early prerequisite work used helpers before we changed to manual commands.
- **Pending** means proposed or documented, with no evidence it was completed.
- Commands are learning references, not a script to rerun from top to bottom.
  `git init`, adding a remote, creating branches and starting named containers can
  fail or conflict if their setup already exists.
- Local command blocks are PowerShell. Workflow `run:` commands run on GitHub's
  Linux runner. Your laptop stays on Windows with global Python and no virtual environment.
- Python/configuration listings are snapshots of the actual project files at this
  checkpoint. Later changes to those files should be recorded as a new execution update.
- AWS credential/token values are deliberately absent. Account sign-in success was
  checked during setup; it does not establish that the temporary session is still valid today.

## Progress at this checkpoint

| Stage | Status | Evidence |
|---|---|---|
| [Sprint 1 — Setup](#execution-1) | Completed | Tools checked; AWS CLI installed and initial browser sign-in verified |
| [Sprint 2 — API](#execution-2) | Completed | Local API and real GitHub repository request succeeded |
| [Sprint 3 — Tests](#execution-3) | Completed | 29 tests passed; lint/format checks passed |
| [Sprint 4 — Docker](#execution-4) | Completed | Image built; container health response and UID 10001 observed |
| [Sprint 5 — Compose](#execution-5) | Completed | Healthy container; `compose-v1` response; real GitHub request succeeded |
| [Sprint 6 — Git/GitHub](#execution-6) | Completed | First commit `e8a5582` pushed to GitHub |
| [Sprint 7 — CI/PR](#execution-7) | CI completed; protection rule created | PR #1 passed CI and merged; screenshot confirms a rule for `main` |
| [Sprint 8 — stronger CI](#execution-8) | Not implemented | One local coverage measurement only; no lock/scan/SBOM workflow yet |
| Sprints 9–29 | Remaining workbook stages | AWS concepts discussed, but no Phase 2 ECR/ECS/ALB provisioning or deployment |

The branch-protection screenshot confirms the rule exists and applies to `main`.
It does not display every checkbox, so the exact required-check/bypass settings and
a deliberately blocked merge have not been independently verified in this record.

## The system we have actually built

```text
YOUR WINDOWS LAPTOP
  Global Python → Uvicorn → FastAPI → GitHub API

  Dockerfile → image → container → FastAPI → GitHub API
                 ↑
       compose.yaml records local runtime settings
       laptop 127.0.0.1:8001 → container port 8000

GITHUB
  local commit → pushed branch → pull request
                                  ↓
                         temporary Ubuntu runner
                         dependencies → lint → format → tests → image build
                                  ↓
                         successful check → merge to main

AWS
  CLI installed and initial sign-in verified
  ECR/ECS/Fargate/ALB deployment: not yet executed
```

Docker packaging reduces differences between environments. A successful local
container does not prove future AWS permissions, routing, capacity or load-balancer
configuration. Those still require their own checks.

<a id="execution-1"></a>

## Sprint 1 — Prerequisites, Windows setup and manual AWS CLI access

### Goal and what we did

We prepared `phase_2_app` as the implementation workspace, used your existing global
Python, checked Git and Docker, installed AWS CLI v2 for your Windows user, and
completed an AWS browser sign-in. We did not install a separate Ubuntu distribution
or create a Python virtual environment.

Observed setup versions, recorded on 25 October 2026:

| Tool | Recorded result |
|---|---|
| Python | 3.12.6 at `C:\Program Files\Python312\python.exe` |
| pip | 26.2.1 for that Python |
| Git | 2.51.1.windows.1 |
| Docker client/engine | 28.5.1; Linux containers through Docker Desktop |
| Docker Compose | v2.40.0-desktop.1 |
| AWS CLI | 2.38.5; installed for the current Windows user |
| AWS profile | `phase2-learning`; initial STS identity check passed |
| Project AWS region | `ap-south-1` (Mumbai) |

The AWS installer was obtained from the official source and its signature checked.
Its local installer/log artifacts are under ignored `.tools/`. No installer command
needs to be repeated now. Docker Desktop's existing WSL2 backend supplies Linux for
containers; a GitHub-hosted Ubuntu runner later supplies a separate CI environment.

### Commands for locating and checking the tools

From the parent `Networking_AWS` folder:

```powershell
cd .\phase_2_app
python --version
python -m pip --version
git --version
docker --version
docker compose version
aws --version
docker info --format '{{.OSType}}'
```

These are the direct equivalents of the prerequisite checks, which were initially
performed through a helper. They can be run individually to inspect the tools.

| Command | Meaning |
|---|---|
| `cd .\phase_2_app` | Changes the terminal's current folder to the application |
| `python --version` | Shows the Python selected by your terminal |
| `python -m pip --version` | Shows pip belonging to that Python interpreter |
| `git --version` | Confirms the Git executable is installed |
| `docker --version` | Shows the Docker client version; does not prove the engine is running |
| `docker compose version` | Checks the Compose command-line plugin |
| `aws --version` | Checks the AWS command-line program |
| `docker info --format '{{.OSType}}'` | Queries the Docker engine and prints its operating-system type; expected `linux` |

If an already-open terminal cannot find the installed AWS executable, the documented
session-only PATH fix is:

```powershell
$env:PATH = "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2;$env:PATH"
aws --version
```

`PATH` is the list of directories searched for commands. This prepends the existing
AWS installation directory; it does not reinstall AWS or change Python.

### AWS CLI sign-in and file locations

Our initial setup stored AWS configuration and browser-login cache under this
project's ignored `.aws/` directory. From `phase_2_app`, the manual equivalents are:

```powershell
$env:AWS_CONFIG_FILE = "$PWD\.aws\config"
$env:AWS_SHARED_CREDENTIALS_FILE = "$PWD\.aws\credentials"
$env:AWS_LOGIN_CACHE_DIRECTORY = "$PWD\.aws\login\cache"
```

| Setting | Meaning |
|---|---|
| `$env:...` | Sets an environment variable for the current PowerShell session and child commands |
| `$PWD` | The current directory, which must be `phase_2_app` here |
| `AWS_CONFIG_FILE` | Selects the file containing profiles and AWS configuration |
| `AWS_SHARED_CREDENTIALS_FILE` | Selects the credentials-file location; this browser-login flow does not require manually writing permanent keys into it |
| `AWS_LOGIN_CACHE_DIRECTORY` | Selects the cache for temporary browser-login credentials and refresh data |

Set or inspect the profile settings with these direct commands:

```powershell
aws configure set region ap-south-1 --profile phase2-learning
aws configure set output json --profile phase2-learning
aws configure get region --profile phase2-learning
aws configure get output --profile phase2-learning
```

`configure set` writes a local setting; `configure get` reads it. Neither creates an
AWS resource. `--profile` selects the named local AWS configuration.

The sign-in and verification operations performed during setup correspond to:

```powershell
aws login --profile phase2-learning --region ap-south-1
aws sts get-caller-identity --profile phase2-learning --region ap-south-1 --no-cli-pager
```

| Part | Meaning |
|---|---|
| `aws login` | Opens browser authorization for local CLI access |
| `sts` | Selects AWS Security Token Service |
| `get-caller-identity` | Asks AWS which identity is making the request |
| `--region ap-south-1` | Explicitly chooses the Mumbai region for the command |
| `--no-cli-pager` | Prints directly in the terminal rather than opening a pager |

**Observed:** the first browser landing was the normal AWS Console homepage, which
did not establish completed CLI authorization. A later browser page reported that
credentials had been shared successfully, and the CLI identity check passed.
Temporary sessions expire; run the manual login again when necessary. Signing into
the Console and authorizing local CLI access are related but distinct steps.

### Why we removed the helper scripts

The initial setup included `Enter-Project.ps1`, `Login-Aws.ps1` and
`Check-Prerequisites.ps1`. You clarified that learning the actual commands was the
objective, so the three helpers were removed and the README was changed to manual
PowerShell/AWS commands. An empty `scripts` folder may remain locally; it is not part
of the committed workflow. No helper is required to run this application.

We use the CLI and Console together: the CLI makes operations explicit; the Console
provides a visual view of the same account's resources. Only sign-in/setup occurred
in AWS at this stage. No ECR repository, ECS service or ALB was created.

### Completion evidence

Tools passed prerequisite checks; Docker's Linux engine worked; AWS CLI identity was
verified during setup. Global Python was retained. The initial global `pip check`
also showed pre-existing conflicts involving `langchain-openai`/`openai` and
`tp-market-research-agent`/FastAPI/Uvicorn. We did not repair unrelated projects or
claim that the entire shared environment was dependency-clean.

<a id="execution-2"></a>

## Sprint 2 — Build and run the FastAPI application

### Goal and what we did

We built a real API that returns health/version information and fetches a GitHub
repository summary. This gives later deployment work a real application and an
outbound dependency to exercise.

| Endpoint | Purpose |
|---|---|
| `/health/live` | Confirms the application responds without calling GitHub |
| `/health/ready` | Confirms local startup and shared HTTP-client initialization |
| `/version` | Returns configured version/environment and the current hostname |
| `/repos/{owner}/{repo}` | Requests GitHub data and returns name, stars, forks and URL |
| `/docs` | Interactive browser interface for trying the API |

### Files we implemented — complete source at this checkpoint

**`requirements.txt`**

```text
# Install with: python -m pip install -r requirements.txt
# These ranges match the guide; they are not a full dependency lock file.
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
httpx>=0.27,<1
pydantic-settings>=2,<3
pydantic>=2,<3
```

This declares acceptable versions of the runtime libraries. It is a range-based
dependency list, not an exact lock file. The local installation found the runtime
requirements already satisfied; no global package upgrade was needed in that step.

**`app/__init__.py`**

```python
"""FastAPI application for the Phase 2 deployment lab."""
```

**`app/config.py`**

```python
"""Load settings from the environment and the optional project-root .env file."""

from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PowerShell environment variables override values in .env and these defaults.
    environment: str = Field(default="local", min_length=1)
    app_version: str = Field(default="dev", min_length=1)
    github_token: SecretStr | None = None
    github_api_base: AnyHttpUrl = AnyHttpUrl("https://api.github.com")
    outbound_timeout_s: float = Field(default=5.0, gt=0, allow_inf_nan=False)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

This reads settings at startup. Environment variables override optional `.env`
values. Defaults allow public GitHub queries without a token. The timeout must be
positive and finite. `SecretStr` masks the usual representation of a token; it does
not make deliberately printing its value safe.

**`app/github_client.py`**

```python
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
```

This file creates the outgoing connection pool, requests GitHub data, validates the
response and translates errors. Timeout → 504, connection failure → 502, missing
repository → 404, rate limit → 503. A non-rate-limit access denial becomes 502.
The helper does not automatically retry or follow redirects.

**`app/main.py`**

```python
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
```

`create_app` assembles the API. The lifespan context opens one HTTP client at startup
and closes it at shutdown. Routes share that client. Middleware adds a request ID
and logs method, route, status and elapsed time. It avoids logging upstream bodies
or raw exception messages that might reveal sensitive details.

**`.env.example`**

```dotenv
# Optional: copy this to .env. Your real .env is ignored by Git and Docker.
ENVIRONMENT=local
APP_VERSION=dev
GITHUB_API_BASE=https://api.github.com
OUTBOUND_TIMEOUT_S=5

# Public repositories work without a token, subject to GitHub rate limits.
# If needed, set your token only in .env or your current shell; never commit it.
GITHUB_TOKEN=
```

This is a safe template, not the real `.env`. No real GitHub token is included.

### Commands and what they mean

From `phase_2_app`:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

| Part | Meaning |
|---|---|
| `python -m pip` | Runs pip belonging to your selected global Python |
| `install -r requirements.txt` | Installs packages described by that requirements file |
| `python -m uvicorn` | Starts the Uvicorn web server using that Python |
| `app.main:app` | Loads the `app` object from `app/main.py` |
| `--host 127.0.0.1` | Listens on this laptop's loopback interface |
| `--port 8000` | Chooses local listening port 8000 |
| `--reload` | Restarts the development server when source files change |

We also used a server without `--reload` for implementation-time verification and
stopped that temporary verification process afterward. Your manual development
server stays open in its terminal until Ctrl+C.

The direct HTTP checks discussed and used in verification were:

```powershell
curl.exe http://127.0.0.1:8000/health/live
curl.exe http://127.0.0.1:8000/version
curl.exe http://127.0.0.1:8000/repos/octocat/Hello-World
```

`curl.exe` sends an HTTP request; it does not build or start the server. The `.exe`
spelling avoids Windows PowerShell's `curl` alias. `Invoke-RestMethod` is another
PowerShell option that parses the JSON response into an object.

### Visual verification and observed results

You opened `http://127.0.0.1:8000/docs`, selected the repository endpoint and supplied
owner `octocat`, repository `Hello-World`. The screenshot showed HTTP 200 and a JSON
summary with repository name, stars, forks and URL. Counts are time-dependent, so
they are not fixed acceptance values.

Implementation verification covered health, readiness, version, API docs/schema,
a real GitHub repository and a nonexistent repository. There were also 27 controlled
checks during implementation. Those temporary checks are separate from the later
saved 29-case pytest suite.

**Status:** local application and live GitHub integration verified. No AWS host or
container was needed for this first local run.

<a id="execution-3"></a>

## Sprint 3 — Saved automated tests, linting and formatting

### Goal and what we did

We saved tests that can be rerun after changes. They simulate GitHub responses so
errors such as rate limits and timeouts are repeatable without real API calls.
We also configured Ruff to check code issues and formatting.

**`requirements-dev.txt`**

```text
-r requirements.txt
# Versions already available in the global Python environment for step 3.
pytest==8.4.2
ruff==0.15.21
```

The first line includes runtime requirements; the other lines name the testing and
lint tools. pytest and Ruff were already present globally at the recorded versions.

**`pyproject.toml`**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 110

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I"]
```

This tells pytest where to find tests and tells Ruff which Python target, line length
and rules to use. Ruff is not a dedicated type checker.

**`tests/test_api.py`**

```python
"""Check the HTTP API with a simulated GitHub server; no real network calls."""

import uuid

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def application(monkeypatch):
    # A fixture prepares a fresh application for each test that asks for it.
    settings = Settings(
        _env_file=None,
        environment="test",
        app_version="test-version",
        github_token=None,
        github_api_base="https://github.test",
        outbound_timeout_s=5,
    )

    def github_response(request):
        assert request.method == "GET"
        assert request.url.path == "/repos/example/demo"
        return httpx.Response(
            200,
            json={
                "full_name": "example/demo",
                "stargazers_count": 7,
                "forks_count": 2,
                "html_url": "https://github.com/example/demo",
            },
        )

    def test_client_factory(config):
        return httpx.AsyncClient(
            base_url=str(config.github_api_base),
            transport=httpx.MockTransport(github_response),
        )

    # Replace only the outgoing connection factory, keeping the real API/helper.
    monkeypatch.setattr("app.main.create_github_client", test_client_factory)
    return create_app(settings)


def test_liveness(application):
    # Entering the context runs startup; leaving it runs shutdown.
    with TestClient(application) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive", "version": "test-version"}


def test_readiness_and_client_cleanup(application):
    with TestClient(application) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
        outgoing_client = application.state.github_client
        assert not outgoing_client.is_closed
    assert outgoing_client.is_closed
    assert application.state.ready is False


def test_not_ready_before_startup(application):
    # Deliberately omit the context manager to exercise the pre-startup response.
    client = TestClient(application)
    try:
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Application is not ready"}
    finally:
        client.close()


def test_version_includes_environment(application):
    with TestClient(application) as client:
        response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"] == "test-version"
    assert response.json()["environment"] == "test"
    assert response.json()["hostname"]


def test_repository_summary(application):
    with TestClient(application) as client:
        response = client.get("/repos/example/demo")
    assert response.status_code == 200
    assert response.json() == {
        "name": "example/demo",
        "stars": 7,
        "forks": 2,
        "url": "https://github.com/example/demo",
    }


def test_request_id_is_returned(application):
    with TestClient(application) as client:
        response = client.get("/health/live", headers={"x-request-id": "learning-123"})
    assert response.headers["x-request-id"] == "learning-123"


@pytest.mark.parametrize("supplied_id", ["", "contains spaces", "x" * 65])
def test_invalid_request_id_is_replaced(application, supplied_id):
    with TestClient(application) as client:
        response = client.get("/health/live", headers={"x-request-id": supplied_id})
    assert str(uuid.UUID(response.headers["x-request-id"])) == response.headers["x-request-id"]


def test_invalid_owner_is_rejected(application):
    with TestClient(application) as client:
        response = client.get("/repos/invalid_owner/demo")
    assert response.status_code == 422


def test_timeout_reaches_http_response(application, monkeypatch):
    def timeout(request):
        raise httpx.ReadTimeout("simulated slow GitHub", request=request)

    monkeypatch.setattr(
        "app.main.create_github_client",
        lambda config: httpx.AsyncClient(
            base_url=str(config.github_api_base), transport=httpx.MockTransport(timeout)
        ),
    )
    with TestClient(application) as client:
        response = client.get("/repos/example/demo")
        assert response.status_code == 504
        assert response.json() == {"detail": "GitHub upstream timeout"}
        assert "x-request-id" in response.headers
        # A downstream outage must not fail the application's liveness check.
        assert client.get("/health/live").status_code == 200
```

**`tests/test_client.py`**

```python
"""Check how the GitHub helper translates responses and connection failures."""

import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.github_client import fetch_repository


def fetch_with_simulated_github(handler):
    # MockTransport supplies responses in memory instead of contacting GitHub.
    async def run():
        async with httpx.AsyncClient(
            base_url="https://github.test", transport=httpx.MockTransport(handler)
        ) as client:
            return await fetch_repository(client, "example", "demo")

    # The helper is asynchronous; asyncio.run lets a normal test call it.
    return asyncio.run(run())


def test_github_success():
    def response(request):
        assert request.url.path == "/repos/example/demo"
        return httpx.Response(
            200,
            json={
                "full_name": "example/demo",
                "stargazers_count": 4,
                "forks_count": 1,
                "html_url": "https://github.com/example/demo",
            },
        )

    result = fetch_with_simulated_github(response)
    assert result.name == "example/demo"
    assert result.stars == 4
    assert result.forks == 1
    assert str(result.url) == "https://github.com/example/demo"


@pytest.mark.parametrize(
    "github_status, expected_status, expected_detail",
    [
        (404, 404, "Repository not found"),
        (401, 502, "GitHub upstream access denied"),
        (403, 502, "GitHub upstream access denied"),
        (429, 503, "GitHub upstream rate limited"),
        (500, 502, "GitHub upstream server failure"),
        (301, 502, "Unexpected GitHub upstream response"),
    ],
)
def test_error_status_translation(github_status, expected_status, expected_detail):
    # pytest runs this test once for each row above.
    with pytest.raises(HTTPException) as error:
        fetch_with_simulated_github(
            lambda request: httpx.Response(github_status, json={"message": "private upstream details"})
        )
    assert error.value.status_code == expected_status
    assert error.value.detail == expected_detail


@pytest.mark.parametrize(
    "headers, message",
    [
        ({"x-ratelimit-remaining": "0"}, "API limit exceeded"),
        ({"retry-after": "30"}, "Please wait"),
        ({}, "You have exceeded a secondary rate limit"),
    ],
)
def test_403_rate_limit_is_distinguished_from_access_denied(headers, message):
    with pytest.raises(HTTPException) as error:
        fetch_with_simulated_github(
            lambda request: httpx.Response(403, headers=headers, json={"message": message})
        )
    assert error.value.status_code == 503
    assert error.value.detail == "GitHub upstream rate limited"


@pytest.mark.parametrize("retry_after, expected_headers", [("30", {"Retry-After": "30"}), ("invalid", None)])
def test_retry_after_header(retry_after, expected_headers):
    with pytest.raises(HTTPException) as error:
        fetch_with_simulated_github(lambda request: httpx.Response(429, headers={"Retry-After": retry_after}))
    assert error.value.headers == expected_headers


@pytest.mark.parametrize(
    "exception_type, expected_status, expected_detail",
    [
        (httpx.ReadTimeout, 504, "GitHub upstream timeout"),
        (httpx.ConnectError, 502, "GitHub upstream unreachable"),
    ],
)
def test_connection_failure(exception_type, expected_status, expected_detail):
    def fail(request):
        raise exception_type("simulated failure", request=request)

    with pytest.raises(HTTPException) as error:
        fetch_with_simulated_github(fail)
    assert error.value.status_code == expected_status
    assert error.value.detail == expected_detail


@pytest.mark.parametrize("body", [b"not JSON", b"{}", b"[]"])
def test_invalid_upstream_body(body):
    with pytest.raises(HTTPException) as error:
        fetch_with_simulated_github(lambda request: httpx.Response(200, content=body))
    assert error.value.status_code == 502
    assert error.value.detail == "Invalid GitHub upstream response"


def test_invalid_star_count():
    with pytest.raises(HTTPException) as error:
        fetch_with_simulated_github(
            lambda request: httpx.Response(
                200,
                json={
                    "full_name": "example/demo",
                    "stargazers_count": "not a number",
                    "forks_count": 1,
                    "html_url": "https://github.com/example/demo",
                },
            )
        )
    assert error.value.status_code == 502
    assert error.value.detail == "Invalid GitHub upstream response"
```

| Testing term | Meaning in our implementation |
|---|---|
| Assertion | A statement such as `assert response.status_code == 200` that must hold |
| Fixture | Prepares a fresh test application with controlled settings |
| `TestClient` | Calls the application within the test process, without opening a server port |
| `with TestClient(...)` | Runs application startup and shutdown around requests |
| `MockTransport` | Supplies simulated GitHub responses or failures in memory |
| `monkeypatch` | Temporarily replaces the client factory used by the application |
| `parametrize` | Runs the same test function for multiple input cases |
| `pytest.raises` | Checks that a specified exception occurs |

### Commands and meanings

```powershell
python -m pytest tests/test_api.py::test_liveness -v
python -m pytest -v
python -m pytest -q
python -m ruff check app tests
python -m ruff format --check app tests
```

| Command or option | Meaning |
|---|---|
| `python -m pytest` | Runs pytest using your global Python |
| `tests/test_api.py::test_liveness` | Selects one test function in one file |
| `-v` | Shows individual test names and outcomes |
| `-q` | Gives concise output; an alternative to `-v`, not another type of test |
| `ruff check app tests` | Checks configured rules in application and test code |
| `ruff format --check app tests` | Checks formatting without rewriting files |

During test-file implementation, one formatting check reported that `test_client.py`
needed formatting. The correction was:

```powershell
python -m ruff format tests/test_client.py
```

Without `--check`, this command rewrites formatting. The subsequent checks passed.

### Problem encountered: pytest run from the parent directory

You first ran the selected-test command from `Networking_AWS`, which produced:

```text
collected 0 items
ERROR: file or directory not found: tests/test_api.py::test_liveness
```

The test had not failed; pytest could not locate the file relative to that directory.
The correction was:

```powershell
cd .\phase_2_app
python -m pytest tests/test_api.py::test_liveness -v
python -m pytest -v
```

### Observed results

Your terminal showed **29 passed in 0.90s** for the full suite. Implementation checks
also passed Ruff linting and formatting. The tests covered API responses, request
IDs, startup/shutdown, input validation, GitHub success/error handling, timeouts,
rate limits, retry hints and invalid upstream bodies.

They do not prove an actual listening port, Docker networking or AWS deployment
works. That is why we performed the separate container checks next.

**Additional measurement, not Sprint 8 implementation:** during preparation of the
sprint workbook, the assistant ran:

```powershell
python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

| Option | Meaning |
|---|---|
| `--cov=app` | Measures execution coverage of application code |
| `--cov-report=term-missing` | Lists unexecuted lines in terminal output |
| `--cov-fail-under=80` | Fails the command if coverage is below 80% |

Observed: all 29 tests passed, **110 of 120 statements covered (91.67%)**. The globally
installed `pytest-cov` made that command available. It has not yet been added to
`requirements-dev.txt`, and coverage is not yet a CI gate. The example of deliberately
breaking an assertion was proposed as a learning exercise; its execution was not shown.

**Status:** the saved 29-test suite and Ruff checks are implemented and verified.

<a id="execution-4"></a>

## Sprint 4 — Docker image and manually started container

### Goal and what we did

We packaged Python, dependencies and application files so the app could run inside
a Linux container. You created the Dockerfile, it was reviewed, then built and run.

The distinctions we established were:

```text
Dockerfile = build recipe
Image      = package produced by following the recipe
Container  = an instance of the image, running the application when started
Compose    = file-based configuration for running local services
```

**Current `Dockerfile`**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --uid 10001 --create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Instruction | What it does and why |
|---|---|
| `FROM python:3.12-slim` | Starts with a Linux image containing Python 3.12 |
| `PYTHONDONTWRITEBYTECODE=1` | Disables creation of Python bytecode cache files |
| `PYTHONUNBUFFERED=1` | Makes Python output appear promptly in container logs |
| `PORT=8000` | Stores an environment value; currently unused because CMD explicitly specifies 8000 |
| `WORKDIR /app` | Sets the working directory inside the image/container |
| `COPY requirements.txt ./` | Copies dependency declarations before source, allowing installation-layer reuse |
| `RUN pip install ...` | Installs runtime dependencies into the image, not your laptop |
| `COPY app ./app` | Copies the application package into `/app/app` |
| `RUN useradd ...` | Creates `appuser` with UID 10001 |
| `USER appuser` | Runs the container application under that non-root identity |
| `EXPOSE 8000` | Documents the container port; does not publish it on the laptop |
| `CMD [...]` | Defines the default Uvicorn startup command without a shell wrapper |
| `--host 0.0.0.0` in CMD | Listens on the container's interfaces so published-port requests can reach it |

The unused `PORT` setting was noted during review, but is still present in the actual
file. The image base tag and dependency ranges remain moving references. The locked
Dockerfile shown in Sprint 8 of the workbook has not replaced this one.

**`.dockerignore`**

```text
.git
.github
.aws
.tools
.env
.env.*
*.pem
*.key
.venv
venv
__pycache__
.pytest_cache
.ruff_cache
*.pyc
*.log
tests
docs
```

This excludes local secrets, AWS configuration, installers, caches and tests from
the build context. The Dockerfile also copies only requirements and `app/`.

### Commands used along the build/run/check path

```powershell
docker build -t fde-api:dev .
docker image ls fde-api
docker run --rm -d --name fde-api -p 127.0.0.1:8001:8000 -e APP_VERSION=local-docker fde-api:dev
curl.exe http://localhost:8001/health/live
docker logs fde-api
docker inspect fde-api --format '{{.Config.User}}'
docker exec fde-api id
```

These were the manual commands provided. The image's presence, running container,
health request, logs and `id` output were observed; not every command above has a
separate pasted user transcript. Port 8001 is the actual laptop mapping used for
this project, even though the original guide also showed `8000:8000`.

| Command/part | Meaning |
|---|---|
| `docker build` | Reads the Dockerfile and assembles an image |
| `-t fde-api:dev` | Gives the image repository name `fde-api` and tag `dev` |
| `.` | Uses the current directory as the build context |
| `docker image ls fde-api` | Lists matching local images; does not list running containers |
| `docker run` | Creates and starts a container from the named image |
| `--rm` | Removes that container after it stops; keeps the image |
| `-d` | Runs in the background, returning control to PowerShell |
| `--name fde-api` | Gives the container a convenient name for later commands |
| `-p 127.0.0.1:8001:8000` | Publishes laptop loopback port 8001 to container port 8000 |
| `-e APP_VERSION=local-docker` | Sets the application version environment variable inside this container |
| `docker logs fde-api` | Reads the application's standard output/error |
| `docker inspect ... --format ...` | Reads only the configured runtime-user field |
| `docker exec fde-api id` | Runs Linux's `id` command inside the running container |

### Visual checks and observed results

Initially, Docker Desktop's Containers page did not show `fde-api`. Inspection found
that `fde-api:dev` existed as an image but no container had been created. Building
produces an entry under **Images**; running produces one under **Containers**.

Later, your logs showed:

```text
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
GET /health/live HTTP/1.1 200 OK
```

Your identity check showed:

```text
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)
```

That verifies startup, a real HTTP response and the non-root runtime user. The later
Compose run also proved the containerized API could reach GitHub.

To stop the standalone container, we used/instructed:

```powershell
docker stop fde-api
```

It requests application shutdown. Because `--rm` was used at creation, the container
is removed afterward, explaining why it disappears from Docker Desktop. The image
remains reusable.

**Status:** Docker packaging and runtime behavior verified. Images have not been
uploaded to ECR or deployed to AWS.

<a id="execution-5"></a>

## Sprint 5 — Compose configuration, port conflict and verified local service

### Goal and what we did

We moved the local run settings into `compose.yaml` so the application could be
started consistently. Dockerfile specifies how to build; Compose specifies how to
build/run the local service, including ports, environment and health checking.

**`compose.yaml`**

```yaml
services:
  api:
    build: .
    ports:
      - "127.0.0.1:8001:8000"
    environment:
      ENVIRONMENT: local-compose
      APP_VERSION: compose-v1
      OUTBOUND_TIMEOUT_S: "5"
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 10s
    restart: unless-stopped
```

| Setting | Meaning |
|---|---|
| `services.api` | Declares one service named `api` |
| `build: .` | Uses the current project's Dockerfile/build context |
| `ports` | Publishes laptop port 8001 to container port 8000 |
| `ENVIRONMENT` | Labels the app environment as `local-compose` |
| `APP_VERSION` | Makes `/version` report `compose-v1` |
| `OUTBOUND_TIMEOUT_S` | Sets the outgoing GitHub operation timeout |
| `healthcheck.test` | Runs a Python HTTP check inside the container |
| `interval: 15s` | Sets the normal interval between health checks |
| `timeout: 3s` | Limits the check process duration |
| `retries: 3` | Consecutive counted failures needed to mark unhealthy |
| `start_period: 10s` | Gives startup failures an initial grace period |
| `restart: unless-stopped` | Restarts an exited container unless deliberately stopped |

Health-check status and process restarts are different: becoming unhealthy alone
does not trigger this restart policy. The health check calls container-local port
8000; a browser on the laptop uses published port 8001.

### Commands and meanings

The initial validation/start instructions were:

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail=50 -f api
docker compose exec api id
```

| Command | Meaning |
|---|---|
| `config --quiet` | Validates Compose configuration; success normally prints nothing |
| `up --build -d` | Builds the image, creates project resources and starts in the background |
| `up -d` | Creates/starts the service without explicitly requesting another build |
| `ps` | Shows this Compose project's running service containers |
| `ps -a` | Also includes containers that are created/stopped rather than running |
| `logs --tail=50` | Prints the last 50 log lines per selected container |
| `-f api` on logs | Follows new logs for service `api`; Ctrl+C exits log-following |
| `exec api id` | Checks the runtime user through the Compose service name |

The transcript confirms the build/start attempts, status and log commands; validation
and the Compose-form `exec` were also provided as checks. The earlier standalone
`docker exec fde-api id` had already confirmed the image's user.

### Problem encountered: port 8001 was already allocated

The image built and the Compose network was created, but container startup failed:

```text
Bind for 127.0.0.1:8001 failed: port is already allocated
```

Inspection showed the earlier standalone `fde-api` still publishing port 8001.
The new Compose container remained in **Created** state. It had not started Uvicorn,
which explained the empty application logs.

The diagnostic commands were:

```powershell
docker ps --filter publish=8001
docker compose ps -a
```

The first identifies running Docker containers publishing the port. The second
reveals the Compose container even when the normal running-container list is empty.
During read-only troubleshooting, formatted `docker ps` output showed:

```text
fde-api | fde-api:dev | 127.0.0.1:8001->8000/tcp
```

The correction sequence was to stop that standalone container and then retry
Compose. Rebuilding the image was unnecessary for this port conflict:

```powershell
docker stop fde-api
docker ps --filter publish=8001
docker compose up -d
docker compose ps
```

The stop command's user output was not pasted, but a subsequent read-only check
found no running container publishing 8001, and your later Compose startup succeeded.

### Observed successful verification

You ran:

```powershell
docker compose ps
curl.exe http://localhost:8001/version
curl.exe http://localhost:8001/repos/octocat/Hello-World
```

Status showed:

```text
phase_2_app-api-1   phase_2_app-api   Up 9 seconds (healthy)   127.0.0.1:8001->8000/tcp
```

Version response:

```json
{"version":"compose-v1","environment":"local-compose","hostname":"85630e6f33e2"}
```

Repository response at that time:

```json
{"name":"octocat/Hello-World","stars":3863,"forks":7196,"url":"https://github.com/octocat/Hello-World"}
```

The hostname identifies this particular container and will change on recreation.
Stars/forks also change. We checked response shape and success, not permanent counts.

**Visual equivalent:** Docker Desktop → Containers → expand `phase_2_app` → `api`.
The same API is available at `http://localhost:8001/docs`.

**Reference cleanup command, not a claim it ran at this checkpoint:**

```powershell
docker compose down
```

It removes this Compose project's containers/default network and normally keeps the
image. It does not remove unrelated Docker workloads.

**Status:** Sprint 5 complete. Healthy startup, configuration and real GitHub access
were all demonstrated by your terminal output.

<a id="execution-6"></a>

## Sprint 6 — Git history, first commit and GitHub publication

### Goal and what we did

We saved the working project as a local Git commit and uploaded it to a new GitHub
repository. The repository root is `phase_2_app`, not its parent `Networking_AWS`.
This matters because GitHub expects workflows at the repository's `.github/workflows` path.

A local repository on branch `main` was initialized during setup. An equivalent
fresh-project initialization is shown only for reference:

```powershell
git init -b main
```

Do not run that again as a required step; initialization is already complete.

**`.gitignore`**

```text
# Python and local tooling
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.venv/
venv/

# Local secrets, AWS profiles/tokens and downloaded installers
.env
.env.*
!.env.example
.aws/
.tools/
*.pem
*.key

# Generated build and diagnostic output
build/
dist/
*.egg-info/
*.log

# Editor/OS files
.idea/
.DS_Store
Thumbs.db
```

It keeps credentials, local AWS files, real `.env` files, caches, installers and build
artifacts out of Git. `.env.example` is intentionally allowed as a template.

**`.gitattributes`**

```text
* text=auto
*.py text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.sh text eol=lf
*.ps1 text eol=crlf
Dockerfile text eol=lf
```

This normalizes text and explicitly selects LF line endings for Python, workflow
YAML and Dockerfile, with CRLF for PowerShell scripts if present.

### Check, stage and review commands

You ran from `phase_2_app`:

```powershell
git status --short
git check-ignore .aws/config .env
git add .
git diff --cached --stat
git --no-pager diff --cached --name-only
```

| Command | Meaning |
|---|---|
| `git status --short` | Lists files differing from Git's current recorded state; `??` means untracked |
| `git check-ignore ...` | Shows which specified paths are excluded by ignore rules |
| `git add .` | Stages changes under the current folder for the next commit; uploads nothing |
| `git diff --cached --stat` | Summarizes staged file changes and line counts |
| `git --no-pager ...` | Prints directly rather than opening Git's output viewer |
| `--name-only` | Shows staged paths without full content diffs |

Observed ignored paths:

```text
.aws/config
.env
```

The staging summary showed 20 files, including app/test code, Dockerfile, Compose,
requirements, README, sprint workbook and placeholder README files under `infra`
and `.github/workflows`. Real AWS credentials and `.env` were not listed.

**Line-ending warnings:** Git warned that LF/CRLF conversions would occur according
to its settings. These were not staging failures. They described Windows/Linux text
line-ending handling.

**Output viewer:** after `git diff --cached --stat`, the `:` prompt indicated Git's
pager. Pressing **q** returns to PowerShell. `--no-pager` avoids that viewer.

### First commit and verification

```powershell
git commit -m "Complete local API, tests, Docker and Compose setup"
git log -1 --oneline
git status --short
```

| Command/part | Meaning |
|---|---|
| `git commit` | Records the staged snapshot in local history |
| `-m` | Supplies the commit message |
| `git log -1 --oneline` | Shows the newest commit's abbreviated ID and message |
| Empty `git status --short` output | No pending tracked/untracked changes visible to Git |

Observed:

```text
e8a5582 (HEAD -> main) Complete local API, tests, Docker and Compose setup
```

The working tree was clean. `create mode 100644 ...` in the commit output simply
reported newly recorded normal files. At that point the commit was still local.

### GitHub web step and the remote-URL correction

You created an empty repository at `https://github.com/2anirban/phase-2-app`, leaving
the initialization options unchecked so local files could be pushed directly.

The first remote used the example placeholder literally. This historical command
is shown to explain the error, **not as a command to run now**:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/phase-2-app.git
git push -u origin main
```

The server reported **Repository not found** because `YOUR_USERNAME` had not been
replaced. Your screenshot supplied the actual owner name, `2anirban`. The correction:

```powershell
git remote set-url origin https://github.com/2anirban/phase-2-app.git
git remote -v
git push -u origin main
```

| Command | Meaning |
|---|---|
| `remote add origin URL` | Creates a named remote connection once |
| `remote set-url origin URL` | Changes the URL of an existing remote |
| `remote -v` | Shows configured fetch/push URLs |
| `push -u origin main` | Uploads local `main` and records its upstream tracking branch |
| `origin` | Conventional name for the remote, not an AWS or GitHub credential |

You completed browser authentication. Successful output included:

```text
To https://github.com/2anirban/phase-2-app.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

The GitHub page then displayed the project files and first commit.

**Status:** local source history and remote publication completed. Future simple
pushes on that tracking branch can use `git push`, subject to later branch rules.

<a id="execution-7"></a>

## Sprint 7 — First CI workflow, pull request, merge and protection rule

### Goal and what we did

We added a workflow that checks a proposed change on GitHub before merging. A runner
is the temporary computer, a job groups steps, and a required status check can make
the result a merge gate.

We made the change on `add-ci`, leaving `main` intact until the pull request was
reviewed and passed CI. The assistant created the file locally; you committed,
pushed, opened the PR and merged through GitHub.

**`.github/workflows/ci.yml` — actual implemented workflow**

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  checks:
    runs-on: ubuntu-latest

    steps:
      - name: Download repository code
        uses: actions/checkout@v7.0.1

      - name: Set up Python
        uses: actions/setup-python@v7.1.0
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: python -m pip install -r requirements-dev.txt

      - name: Check code quality
        run: python -m ruff check app tests

      - name: Check formatting
        run: python -m ruff format --check app tests

      - name: Run tests
        run: python -m pytest -v

      - name: Build Docker image
        run: docker build -t fde-api:ci .
```

### What the workflow does

| Configuration | Meaning |
|---|---|
| `name: CI` | Display name in GitHub Actions |
| `on.pull_request` | Runs for the default relevant PR events such as opening/updating a PR |
| `on.push.branches: [main]` | Also runs when a push updates `main`, including a merge |
| `permissions.contents: read` | Gives the workflow token repository-read access |
| `jobs.checks` | Names the job `checks`, also used when selecting required checks |
| `runs-on: ubuntu-latest` | Selects a hosted Linux runner; does not change your Windows laptop |
| `uses: actions/checkout...` | Checks out the code to be tested onto the runner |
| `uses: actions/setup-python...` | Makes Python 3.12 available on that runner |

The PR checkout tests the proposed combined version by default. It is not running
the code directly from your Windows folder. The file must be committed/pushed before
GitHub can use it; creating it locally alone does not trigger anything.

| Workflow command | What it checks |
|---|---|
| `python -m pip install -r requirements-dev.txt` | A fresh runner can install declared runtime and test dependencies |
| `python -m ruff check app tests` | Configured static code rules pass |
| `python -m ruff format --check app tests` | Formatting matches the configuration |
| `python -m pytest -v` | The saved test suite passes in the runner's environment |
| `docker build -t fde-api:ci .` | The Dockerfile can produce an image there |

These commands run in order. A failing normal step fails the job and skips subsequent
normal steps. The tests simulate GitHub; the workflow does not test the public API.
It builds an image but does not run that image, save it as an artifact, push it to
ECR or deploy it to AWS. The image is temporary runner-local output.

### Branch, commit and push commands

```powershell
git switch -c add-ci
git add .github/workflows/ci.yml
git commit -m "Add GitHub Actions checks"
git push -u origin add-ci
```

| Command | Meaning |
|---|---|
| `switch -c add-ci` | Creates and selects a branch starting from the current commit |
| `add .github/workflows/ci.yml` | Stages only the new workflow file |
| `commit -m ...` | Saves that change locally on the branch |
| `push -u origin add-ci` | Publishes the branch and sets tracking; does not merge into `main` |

Inspection confirmed branch `add-ci`, then commit **`d39f396` — Add GitHub Actions checks**.
Pushing this branch alone was not a trigger under our workflow; opening the PR was.

### GitHub UI steps executed

1. Opened the repository and selected **Compare & pull request**.
2. Confirmed **base: main**, **compare: add-ci**.
3. Kept title **Add GitHub Actions checks** and created PR **#1**.
4. Observed **CI / checks (pull_request)** in progress, then successful.
5. Selected **Merge pull request** and confirmed the merge after checks passed.

A description was suggested during guidance, but the later PR screenshot showed
**No description provided**. This record does not claim the suggested description
was saved. PR discussion and code-review fields are separate from automated checks.

**Observed CI evidence:** GitHub showed **All checks have passed**, one successful
check, `CI / checks (pull_request)`, successful in **26 seconds**. The workflow has
one job containing several steps, so “one successful check” does not mean only one
test was run. The screenshot does not provide a full per-step log transcript.

**No conflicts with base branch** meant Git could combine the branches. It did not
mean tests had passed; the separate green CI status supplied that result.

### Synchronize local main after the merge

The commands provided for synchronizing were:

```powershell
git switch main
git pull --ff-only origin main
git status --short
```

| Command | Meaning |
|---|---|
| `git switch main` | Selects your local main branch |
| `git pull --ff-only origin main` | Fetches and updates it only if it can fast-forward without a new local merge |
| `git status --short` | Confirms the remaining working-tree changes |

The user's exact pull output was not pasted. Subsequent inspection confirmed local
`main` matched remote `main`, the working tree was clean, and the history contained:

```text
9ea41d1 Merge pull request #1 from 2anirban/add-ci
d39f396 Add GitHub Actions checks
e8a5582 Complete local API, tests, Docker and Compose setup
```

Read-only verification commands used by the assistant included:

```powershell
git branch --show-current
git log -3 --oneline
git remote -v
git ls-remote origin refs/heads/main
```

`ls-remote` reads the remote branch's commit ID without merging local files. The full
remote main ID was `9ea41d1c90f57b7fe86f3b721744b89e50f19e4e` at verification.

The merge updates `main` and therefore triggers the workflow's push event too.
We have explicit evidence of the PR check succeeding; we have not separately recorded
the merged-main workflow run result here.

### Branch protection: turn the check into a requirement

We then used **GitHub → Settings → Branches → Add classic branch protection rule**.
The guidance was to configure:

| Setting | Intended effect |
|---|---|
| Branch name pattern `main` | Targets the main branch |
| Require a pull request before merging | Sends changes through a PR |
| Require approvals left unchecked | Avoids requiring another reviewer for this solo exercise |
| Require status checks to pass before merging | Makes selected checks mandatory |
| Select `checks` | Requires the CI job we implemented |
| Require branches to be up to date before merging | Checks against the latest base-branch state |
| Do not allow bypassing the above settings | Applies the protection to privileged users too |

Your screenshot showed **Branch protection rule created**, a `main` rule, and
**Currently applies to 1 branch**. Those facts are confirmed. The screenshot did
not expose the saved checkbox values; we have not yet inspected the saved form or
demonstrated a failing PR being blocked. Do not confuse the existence of a rule
with independent verification of every intended setting.

**Status:** first CI workflow successfully exercised and merged. A protection rule
exists; checking its saved configuration and observing enforcement remain useful
verification steps before treating the gate as fully demonstrated.

<a id="execution-8"></a>

## Sprint 8 — What has and has not happened yet

The next planned sprint adds coverage gating, dependency locking, vulnerability
scanning and an SBOM (Software Bill of Materials). The full future instructions and
code are in [Sprint 8 of the workbook](sprint_phase2.md#sprint-8).

| Item | Actual state at this checkpoint |
|---|---|
| Local coverage measurement | Ran once during workbook preparation: 91.67%, 29 tests passed |
| Coverage in `requirements-dev.txt` | Not added yet |
| Coverage command/gate in CI | Not added yet |
| `requirements.lock` | Not created |
| Locked Dockerfile installation | Not implemented; current Dockerfile still reads `requirements.txt` |
| Vulnerability scan | Not executed as part of this project's completed work |
| SBOM | Not generated |
| CI image/report artifact uploads | Not implemented |
| `improve-ci` branch | Proposed, but current inspection still shows `main`; no executed branch switch recorded |

The following sequence was suggested as the next action, but is **pending**, not a
completed command block:

```powershell
git switch main
git pull --ff-only origin main
git switch -c improve-ci
```

It would start new work from updated main and create a separate branch for CI
improvements. This execution record was requested before beginning that work.

## Remaining project scope — not executed yet

| Workbook stage | Remaining work |
|---|---|
| 9 | Formal AWS service vocabulary walkthrough; some concepts already discussed |
| 10 | Budget, provisioning plan and resource inventory |
| 11 | Create ECR repository and publish an image |
| 12 | Create ECS execution role and inspect IAM permissions |
| 13 | Create log group and register a task definition |
| 14 | Configure/verify AWS networking for the lab |
| 15 | Create ALB, target group and listener |
| 16 | Launch an ECS service on Fargate |
| 17 | Inspect cloud logs, events, target health and alarms |
| 18 | Configure GitHub OIDC and an AWS deployment role |
| 19 | Implement the AWS deployment workflow |
| 20 | Verify exact running cloud release identity |
| 21 | Demonstrate cloud rollback and shutdown behavior |
| 22 | Optional Secrets Manager token injection |
| 23–24 | Cloud incident drills and CI/CD decision exercises |
| 25 | Optional autoscaling and HTTPS |
| 26–27 | Capstone recovery and handover |
| 28 | Remove billable lab resources after they have been created/used |
| 29 | Final review and references |

No future policy, task-definition or deployment-workflow code from those sections
is presented here as an executed artifact. The workbook remains the place to find
that planned code. We have not provisioned Phase 2 cloud infrastructure simply by
signing in to AWS or by merging the first CI workflow.

## Troubleshooting lessons collected so far

| What happened | What it meant | Resolution/evidence |
|---|---|---|
| AWS browser showed the Console homepage | Console sign-in alone did not prove CLI authorization | Finished the authorization flow; initial STS check passed |
| pytest could not find `tests/test_api.py` | Command was run from the parent folder | Changed into `phase_2_app`; 29 tests passed |
| Docker Desktop had an image but no `fde-api` container | Build had not produced a running instance | Ran the image; container logs/health/identity succeeded |
| Compose port 8001 was allocated | Standalone `fde-api` already owned the host port | Removed that conflict and started the Compose service |
| Compose logs were empty | Container failed before Uvicorn started | Investigated Docker port allocation rather than Python logs |
| Git showed LF/CRLF warnings | Text line-ending normalization | Staging and commit still succeeded |
| Git output ended at `:` | The pager was active | Pressed/was instructed to press q; used `--no-pager` output |
| Push reported repository not found | Remote URL still contained `YOUR_USERNAME` | Corrected it with `remote set-url` to `2anirban` |
| PR said no conflicts while CI was yellow | Mergeability and test success are separate | Waited for the green CI result before merging |

## Files, documentation and evidence location

```text
phase_2_app/
  app/__init__.py
  app/config.py
  app/github_client.py
  app/main.py
  tests/test_api.py
  tests/test_client.py
  tests/README.md
  .github/workflows/ci.yml
  .github/workflows/README.md
  infra/README.md
  Dockerfile
  compose.yaml
  requirements.txt
  requirements-dev.txt
  pyproject.toml
  .env.example
  .gitignore
  .dockerignore
  .gitattributes
  README.md
  sprint_phase2.md
  phase2_execution.md
```

`.aws/`, `.tools/`, coverage/cache files and other ignored local artifacts are not
included in the repository listing. `infra/` currently contains a planning README,
not deployed infrastructure definitions. Some earlier README text still describes
later work as future; use inspected files and the dated evidence here for this checkpoint.

We also added explanations verbatim to the parent
[Phase 2 conceptual guide](../Phase_2_Deployment_and_Automation_FDE_Guide.md), including
Docker, command meanings, CI behavior and pull requests. That parent guide is outside
the `phase_2_app` Git repository and was not uploaded by this repository's `git push`.

**This file's own publication state:** creating `phase2_execution.md` creates a local
document only. It is not included in the earlier commits listed above, and no commit
or push of this record is implied. With main protection configured, a future update
should follow the branch → commit → push → PR → checks → merge process we learned.

## Repeatable checkpoints for future updates

For the next execution update, record the real command/result or UI evidence under
its sprint instead of marking a step complete just because code exists in a guide:

```text
Date and sprint:
Goal:
Files created/changed:
Commands actually run:
Meaning of each command/flag:
Console or GitHub UI actions:
Observed result:
Errors and corrections:
Commit/PR/workflow reference:
Completed / partially verified / pending:
```

At this checkpoint we have a working local containerized API, repeatable tests,
a published Git repository and a successful CI pull request. The next implementation
work is Sprint 8; AWS application deployment remains later in the project.
