# Phase 2 sprint workbook — from local Python to an AWS release

This is your step-by-step implementation workbook. One numbered guide stage is one
sprint. Read its explanation, create or inspect its files, run each command yourself,
look at the result in the relevant UI, and meet the exit check before moving on.
Sprint numbers follow the Phase 2 guide, including optional exercises and cleanup.

The actual project folder is **`phase_2_app`**, not `phase_two_app`. All file paths
below are relative to `phase_2_app`, which will be the root of its own Git repository.
This document describes future work; adding it does not deploy anything or enable CI.

## How we will work

- Your laptop: Windows PowerShell and global Python 3.12; no virtual environment.
- Your containers: Linux through Docker Desktop. You do not need to install Ubuntu.
- GitHub Actions: a separate hosted Ubuntu runner. Bash inside workflow `run:` blocks
  executes there, not in your Windows terminal.
- AWS: use the CLI to perform an operation, then inspect the same account and region
  in the Console. Some setup steps deliberately use the Console for a visual view.
- No custom setup/login/deployment wrapper scripts. Commands are visible here.
  Application code, tests and eventually CI workflows are explained before use.
- Run command blocks line by line. After a native command fails, stop and investigate;
  PowerShell does not automatically stop after every nonzero native exit code.
- `REPLACE_...` means a value you must supply. Do not run a block with those markers.
- Keep a record of generated IDs in `.aws/lab-notes.md` (already Git-ignored).
  Never record token values. All `$lab...` variables last only in the current terminal.
- JSON files should be saved as UTF-8. PowerShell examples that generate JSON use
  `.NET WriteAllText` to avoid Windows PowerShell 5's UTF-16 redirection default.
- Do not rerun resource-creation commands blindly. An existing name is a reason to
  inspect the resource, not delete it or create duplicates.

**Starting point, based on our session:** sprints 1–3 are verified; sprint 4 has a
running container, successful health response and non-root identity. Confirm its
GitHub route too. Sprint 5 has been explained but is not yet verified. Later sprints
are planned. The application/test listings below are the actual current source,
not the older illustrative snippets in the original guide.

| Sprint | Deliverable |
|---|---|
| [1](#sprint-1) | Windows tools, manual AWS login and project layout |
| [2](#sprint-2) | FastAPI app with a real GitHub integration |
| [3](#sprint-3) | Repeatable tests and lint checks |
| [4](#sprint-4) | Working Docker image and container |
| [5](#sprint-5) | Compose configuration and local health checks |
| [6](#sprint-6) | Git history and a GitHub repository |
| [7](#sprint-7) | First CI workflow: runners, jobs and gates |
| [8](#sprint-8) | Dependency lock, coverage, vulnerability scan and SBOM |
| [9](#sprint-9) | Understand the AWS deployment components |
| [10](#sprint-10) | Account, budget, region and resource inventory |
| [11](#sprint-11) | Immutable image in ECR |
| [12](#sprint-12) | ECS execution role and IAM boundaries |
| [13](#sprint-13) | Registered task definition and log group |
| [14](#sprint-14) | VPC, subnets, egress and security groups |
| [15](#sprint-15) | Application Load Balancer and target group |
| [16](#sprint-16) | ECS service with two Fargate tasks |
| [17](#sprint-17) | Logs, events, target health and alarms |
| [18](#sprint-18) | GitHub OIDC identity and scoped deploy permissions |
| [19](#sprint-19) | Deploy the tested image through GitHub Actions |
| [20](#sprint-20) | Verify the exact running release |
| [21](#sprint-21) | Rollback and graceful shutdown |
| [22](#sprint-22) | Optional GitHub token through Secrets Manager |
| [23](#sprint-23) | Diagnose failures using evidence |
| [24](#sprint-24) | Decide what to automate and what needs a gate |
| [25](#sprint-25) | Optional scaling and HTTPS extensions |
| [26](#sprint-26) | Capstone incident and recovery |
| [27](#sprint-27) | Final mastery and handover |
| [28](#sprint-28) | Cleanup and cost verification |
| [29](#sprint-29) | References and next-project boundaries |

<a id="sprint-1"></a>

## Sprint 1 — Prerequisites, manual sign-in and repository structure

**What and why:** prepare tools on your laptop. Installing AWS CLI lets PowerShell
send API requests to AWS; it does not run commands on a server or create infrastructure.

From `Networking_AWS`:

```powershell
cd .\phase_2_app
python --version
python -m pip --version
git --version
docker --version
docker compose version
aws --version
```

Expected: Python 3.12, AWS CLI v2 and version output for the other tools. If `aws`
is unrecognized, expose its existing installation in this terminal:

```powershell
$env:PATH = "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2;$env:PATH"
aws --version
```

Open Docker Desktop and wait for its engine, then:

```powershell
docker info --format '{{.OSType}}'
```

Expected: `linux`. This is Docker's engine type, not a change to your Windows OS.

Our earlier sign-in files are project-local. In each new terminal, from the project:

```powershell
New-Item -ItemType Directory -Force .aws | Out-Null
$env:AWS_CONFIG_FILE = "$PWD\.aws\config"
$env:AWS_SHARED_CREDENTIALS_FILE = "$PWD\.aws\credentials"
$env:AWS_LOGIN_CACHE_DIRECTORY = "$PWD\.aws\login\cache"
aws sts get-caller-identity --profile phase2-learning --region ap-south-1 --no-cli-pager
```

`$PWD` is your current folder. These variables select file locations; they do not
contain secret values. STS means **Security Token Service**. Its response identifies
your account and caller ARN (Amazon Resource Name). If the session expired:

```powershell
aws login --profile phase2-learning --region ap-south-1
aws sts get-caller-identity --profile phase2-learning --region ap-south-1 --no-cli-pager
```

Finish browser authorization before the second command. A Console homepage alone
does not prove CLI authorization; successful STS output does. Browser login uses
temporary credentials. See [AWS login](https://docs.aws.amazon.com/cli/latest/reference/login/).

**Console:** confirm your account and development identity in the top-right menu;
select Mumbai (`ap-south-1`) for this workbook. IAM is global, most lab services are regional.

Inspect settings without displaying credential files:

```powershell
aws configure get region --profile phase2-learning
aws configure get output --profile phase2-learning
```

If needed, set them explicitly:

```powershell
aws configure set region ap-south-1 --profile phase2-learning
aws configure set output json --profile phase2-learning
```

**Project layout as later sprints are completed:**

```text
phase_2_app/
  app/                       # Python application
  tests/                     # Test code and walkthrough
  infra/                     # IAM and ECS configuration JSON
  .github/workflows/         # CI/deployment YAML, added when taught
  .aws/                      # Ignored local login data and lab notes
  .tools/                    # Ignored local installers and temporary artifacts
  Dockerfile
  compose.yaml               # Sprint 5
  requirements.txt
  requirements-dev.txt
  requirements.lock          # Sprint 8
  pyproject.toml
  .gitignore
  .dockerignore
  README.md
  sprint_phase2.md
```

**Exit check:** tools respond, Docker reports Linux, and STS identifies the intended
account. No AWS resource creation is needed for this sprint. IAM provisioning rights
for later stages are separate from successful login.

<a id="sprint-2"></a>

## Sprint 2 — The FastAPI application

**What and why:** create an HTTP API that calls GitHub. This gives us a real outbound
dependency to test and diagnose after deployment. Requests flow through Uvicorn,
FastAPI and the shared HTTPX client, then back as a small JSON response.

These files already exist; inspect them rather than overwriting later improvements.
On a fresh copy, create the files at the paths shown with the full contents below.

**File: `requirements.txt`**

```text
# Install with: python -m pip install -r requirements.txt
# These ranges match the guide; they are not a full dependency lock file.
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
httpx>=0.27,<1
pydantic-settings>=2,<3
pydantic>=2,<3
```

**File: `app/__init__.py`**

```python
"""FastAPI application for the Phase 2 deployment lab."""
```

**File: `app/config.py`**

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

Settings are read at startup. Environment variables override `.env` values. The
timeout is positive and finite. `SecretStr` masks the token's usual representation;
it is not permission to print headers or secret values.

**File: `app/github_client.py`**

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

`create_github_client` defines a connection pool. `fetch_repository` makes one request
and validates the returned fields. It maps timeouts to 504, connection failures to
502, missing repositories to 404 and rate limits to 503. A generic 403 means access
denied unless rate-limit evidence is present. There are no automatic retries.

**File: `app/main.py`**

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

The lifespan context creates the shared client once and closes it at shutdown.
`/health/live` tests local response; `/health/ready` tests local startup state, not
GitHub availability. `/version` identifies the build/environment/host. Request logs
carry a request ID so one response can be matched to its log entry.

**File: `.env.example`**

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

You do not need a real `.env` or GitHub token for public repository requests.
If you create `.env`, keep it ignored and never overwrite existing settings blindly.

Run from `phase_2_app`:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Keep that terminal open; Ctrl+C stops this local server. In a second terminal:

```powershell
curl.exe http://127.0.0.1:8000/health/live
curl.exe http://127.0.0.1:8000/version
curl.exe http://127.0.0.1:8000/repos/octocat/Hello-World
```

**Visual check:** open `http://127.0.0.1:8000/docs`, use **Try it out**, then Execute.
Star counts change over time. There is no homepage at `/`.

**Exit check:** health and repository endpoints return 200. A timeout is an expected
failure mode to investigate, not proof that the whole server failed. Your global
Python already has unrelated dependency conflicts; do not freeze its entire package
list into this app. Sprint 8 resolves app dependencies in Linux separately.

<a id="sprint-3"></a>

## Sprint 3 — Tests, linting and formatting

**What and why:** save repeatable checks before deployment. An assertion states what
must be true. A mock supplies a controlled GitHub response without a network call.
A fixture creates fresh app state. These are testing tools, not AWS command wrappers.

**File: `requirements-dev.txt` — initial version**

```text
-r requirements.txt
# Versions already available in the global Python environment for step 3.
pytest==8.4.2
ruff==0.15.21
```

**File: `pyproject.toml`**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 110

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I"]
```

**File: `tests/test_api.py`**

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

**File: `tests/test_client.py`**

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

`TestClient` calls the app inside the test process. It does not test an actual port.
Using `with` exercises startup/shutdown. `monkeypatch` replaces the outgoing client
factory temporarily; the real route and response processing still run. Parameterized
tests run once for each row of inputs. `asyncio.run` executes the async helper.

Run one test, then all tests and code-quality checks:

```powershell
python -m pytest tests/test_api.py::test_liveness -v
python -m pytest -v
python -m ruff check app tests
python -m ruff format --check app tests
```

Expected baseline: 1 passed, then 29 passed. Ruff checks static rules and formatting;
it is not a type checker. These commands need neither a running server nor AWS login.

**Exercise:** temporarily change the expected health status in the test from `alive`
to `healthy`. Run that test and inspect `$LASTEXITCODE`: it should be 1. Restore
`alive`, rerun, and expect 0. Do not move forward with the intentional failure left in place.

**Exit check:** the 29 baseline cases and both Ruff commands pass. In-process tests
still need separate container and deployed-service checks later.

<a id="sprint-4"></a>

## Sprint 4 — Docker packaging and runtime verification

**What and why:** package Python, dependencies and application files into one image.
An image is a template; a container is a running instance of it. The Linux image
contains its own Python and does not use your laptop's global packages.

**File: `Dockerfile` — current learning version**

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

`FROM` selects the base image. `WORKDIR` sets the working folder. Copying requirements
first allows dependency installation to be cached when only source changes. `USER`
selects the non-root runtime identity. JSON-form `CMD` starts Uvicorn directly, and
`0.0.0.0` listens on the container's network interfaces. `EXPOSE` documents a port;
it does not publish it. `PORT=8000` is unused because CMD explicitly chooses 8000;
you may remove that variable while preserving valid ENV line continuations.

**File: `.dockerignore`**

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

**File: `.gitignore`**

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

Build from `phase_2_app`:

```powershell
docker build -t fde-api:dev .
docker image ls fde-api
docker run --rm -d --name fde-api -p 127.0.0.1:8001:8000 -e APP_VERSION=local-docker fde-api:dev
curl.exe http://127.0.0.1:8001/health/live
docker logs fde-api
docker inspect fde-api --format '{{.Config.User}}'
docker exec fde-api id
```

`-t` names the image. `--rm` removes the container after it stops, not the image.
`-d` runs in the background. `-p` maps laptop 8001 to container 8000 and binds it only
to your laptop's loopback address. `-e` supplies an environment variable to the app.
`logs` reads stdout/stderr; `inspect` reads configuration; `exec ... id` runs Linux's
identity command in the container. Expect `appuser`, UID 10001 and health version
`local-docker`. Laptop port 8001 avoids the earlier Uvicorn server on port 8000.

**Visual check:** Docker Desktop → Images shows `fde-api:dev`; Containers shows
`fde-api`. Open `http://127.0.0.1:8001/docs` and execute the GitHub endpoint.

When finished:

```powershell
docker stop fde-api
```

The container disappears because of `--rm`. That is expected.

**Exit check:** real container HTTP requests work, GitHub is reachable, and the process
runs as non-root. A successful image build alone does not prove those properties.

<a id="sprint-5"></a>

## Sprint 5 — Docker Compose for local parity

**What and why:** record the startup settings you just supplied manually. Compose
is optional for one container, but it lets you recreate those choices from a file.
It does not reproduce AWS IAM, networking or load balancing.

**File: `compose.yaml`**

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

| Field | What it does |
|---|---|
| `services.api` | Names this application service `api` |
| `build` | Selects the folder containing the Dockerfile |
| `ports` | Publishes the API on laptop port 8001 |
| `environment` | Supplies app settings at startup |
| `healthcheck.test` | Runs Python inside the container to check local HTTP |
| `interval`, `timeout` | Check schedule and maximum check duration |
| `retries`, `start_period` | Consecutive-failure threshold and startup grace period |
| `restart` | Restarts an exited container unless deliberately stopped |

An unhealthy status alone does not trigger this restart policy. See
[Compose service settings](https://docs.docker.com/reference/compose-file/services/).

If the manually started `fde-api` still occupies port 8001, stop it first. Then:

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl.exe http://127.0.0.1:8001/version
docker compose logs --tail=50 api
docker compose exec api id
```

`config --quiet` validates configuration. `up` builds and starts. `ps` shows status.
To follow new logs, add `-f`; Ctrl+C stops log-following, not the container.

**Visual check:** Docker Desktop → Containers → expand `phase_2_app` → select `api`.
Expect healthy, version `compose-v1`, environment `local-compose`. Run the repository
endpoint through `/docs` as well. When finished:

```powershell
docker compose down
```

This removes this Compose project's containers and default network. It does not
delete unrelated containers or the built image. **Exit check:** recreate it from the
file, see healthy status and explain every setting.

<a id="sprint-6"></a>

## Sprint 6 — Git history and the release artifact

**What and why:** a Git commit identifies source; an image digest identifies built
bytes. A tag is a readable label. We will trace all three rather than using `latest`.

The local repository is already initialized on `main`. Check it:

```powershell
git rev-parse --show-toplevel
git status --short
git check-ignore .aws/config .aws/login/cache/example.json .env
```

The top-level folder must be `phase_2_app`. Confirm local AWS files are ignored.
Review every staged path; add the application, tests, docs and configuration:

```powershell
git add .
git diff --cached --stat
git diff --cached --name-only
git commit -m "Build and test the Phase 2 API locally"
git rev-parse HEAD
```

If Git needs your author name/email, set them for this repository with `git config
user.name` and `git config user.email` using your chosen identity. Those settings
are not GitHub login credentials.

**GitHub web:** create an empty repository named `phase-2-app`, without generated
README/license files. Choose visibility deliberately. Add the remote once:

```powershell
git remote add origin https://github.com/REPLACE_OWNER/phase-2-app.git
git push -u origin main
```

Complete Git Credential Manager's browser login if prompted. If `origin` already
exists, inspect `git remote -v` before changing it. Later pushes use `git push`.

**Exit check:** GitHub shows `app/`, `tests/` and `.github/` at repository root,
not nested under a second `phase_2_app` directory. No `.aws`, `.env` or token files
are tracked. All following workflow paths assume this root layout.

<a id="sprint-7"></a>

## Sprint 7 — GitHub Actions fundamentals: runners, jobs and gates

**What and why:** repeat your manual checks on a GitHub-hosted computer when code
changes. A **runner** is that computer; a **job** is a sequence of steps on it; a
**gate** is a requirement that must pass before merging or deploying.

**File: `.github/workflows/ci.yml` — first version**

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
      - uses: actions/checkout@v7.0.1
      - uses: actions/setup-python@v7.1.0
        with:
          python-version: "3.12"
      - run: python -m pip install -r requirements-dev.txt
      - run: python -m ruff check app tests
      - run: python -m ruff format --check app tests
      - run: python -m pytest -v
      - run: docker build -t fde-api:ci .
```

`checkout` downloads the committed code; `setup-python` selects Python on the hosted
runner. Each `run` executes there. An unsuccessful step stops subsequent normal
steps and fails the job. No AWS credentials are needed for this workflow.

Commit and push this file. In GitHub → Actions, open the run and expand each step.
Create a branch/PR for the next change. In Settings → Rules/Rulesets or Branch
protection, require the CI check for `main` where your repository plan supports it.
Use the actual check name shown after the first run. Without a required-check rule,
a failing workflow by itself does not prevent an authorized user from merging.

Version tags make these examples readable. For a hardened repository, replace action
tags with reviewed full commit SHAs from their official releases, and update them
through reviewed dependency changes. Do not invent SHA values.

**Exit check:** a PR runs tests/build; a deliberate failed assertion produces a red
check; restore the assertion before merging. Ubuntu is on GitHub, not your laptop.

<a id="sprint-8"></a>

## Sprint 8 — Lock dependencies, measure coverage, scan and record an SBOM

**What and why:** coverage shows which lines tests execute; vulnerability scans find
known package issues; a **Software Bill of Materials (SBOM)** lists image contents.
None of these guarantees that the application is secure or correct.

First generate a Linux runtime dependency lock in a disposable Python container.
This avoids exporting unrelated packages from your shared global Python:

```powershell
docker run --rm --platform linux/amd64 --mount "type=bind,source=$PWD,target=/work" -w /work python:3.12-slim sh -c "python -m pip install pip-tools==7.6.2 && python -m piptools compile --generate-hashes --output-file=requirements.lock requirements.txt"
```

The bind mount lets the container write `requirements.lock` into this project.
`sh -c` runs the two visible commands in Linux inside the container. Review and
commit the generated file. Regenerate it deliberately when upgrading dependencies;
do not handwrite or invent package hashes.

This compiles for Linux/X86_64, the target used in CI and ECS. Do not install that
Linux lock into your Windows global environment; keep using the Windows development
requirements there. The hosted Linux CI checks the locked runtime separately.

**Replace `Dockerfile` with this locked-dependency version:**

```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock
COPY app ./app
RUN useradd --uid 10001 --create-home appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The base tag still moves. For a strict release base, pull/inspect it, copy its actual
repository digest into `FROM python:3.12-slim@sha256:...`, and commit that change.
Updating the digest is then an explicit maintenance task, not an automatic patch.

Add `pytest-cov==6.3.0` to `requirements-dev.txt`. It was already present in your
global Python; on another machine install it before this command:

```powershell
python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

80% is a learning threshold, not proof of adequate tests. Add meaningful cases if
needed rather than lowering it to hide missing behavior. CI installs the Linux
runtime lock plus test tools separately; your Windows environment remains global.

**Replace `.github/workflows/ci.yml` with this complete version:**

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
  workflow_call:
permissions:
  contents: read
jobs:
  checks:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    env:
      IMAGE_TAG: ${{ github.sha }}-${{ github.run_id }}-${{ github.run_attempt }}
      TRIVY_IMAGE: aquasec/trivy:0.76.1
    steps:
      - uses: actions/checkout@v7.0.1
      - uses: actions/setup-python@v7.1.0
        with:
          python-version: "3.12"
      - name: Install locked runtime and test tools
        run: |
          python -m pip install --require-hashes -r requirements.lock
          python -m pip install pytest==8.4.2 pytest-cov==6.3.0 ruff==0.15.21
          python -m pip check
      - run: python -m ruff check app tests
      - run: python -m ruff format --check app tests
      - run: python -m pytest --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=80
      - name: Build and save the Linux image once
        run: |
          docker build --platform linux/amd64 -t "fde-api:$IMAGE_TAG" .
          docker save "fde-api:$IMAGE_TAG" -o image.tar
      - name: Inventory image contents
        run: |
          docker run --rm -v "$PWD:/work" "$TRIVY_IMAGE" image --input /work/image.tar --format cyclonedx --output /work/sbom.cdx.json
      - name: Block known HIGH and CRITICAL vulnerabilities
        run: |
          docker run --rm -v "$PWD:/work" "$TRIVY_IMAGE" image --input /work/image.tar --scanners vuln --severity HIGH,CRITICAL --exit-code 1 --format json --output /work/trivy.json
      - name: Preserve reports even if the scan fails
        if: always()
        uses: actions/upload-artifact@v7.0.2
        with:
          name: reports-${{ github.run_id }}-${{ github.run_attempt }}
          path: |
            coverage.xml
            sbom.cdx.json
            trivy.json
          if-no-files-found: warn
          retention-days: 7
      - name: Preserve the image only after all gates pass
        uses: actions/upload-artifact@v7.0.2
        with:
          name: release-${{ github.run_id }}-${{ github.run_attempt }}
          path: image.tar
          compression-level: 0
          retention-days: 1
```

The scanner reads an image archive, so it does not need the Docker daemon socket.
Its vulnerability database requires internet access. Findings or a scan/database
failure block the image artifact; investigate the actual output. Upgrade affected
dependencies/base image and rescan. Do not blindly add `continue-on-error`.

`workflow_call` lets sprint 19 invoke these exact gates before deployment. The saved
image is the one we will push, avoiding a different rebuild after the scan. Tags
include run/attempt IDs so reruns do not overwrite immutable ECR tags. Runtime package
hashes are locked; the test tools and scanner are versioned but not a full supply-chain lock.

For a manual local scan after building, run each command yourself:

```powershell
New-Item -ItemType Directory -Force .tools | Out-Null
docker build --platform linux/amd64 -t fde-api:scan .
docker save fde-api:scan -o .tools/image.tar
docker run --rm --mount "type=bind,source=$PWD/.tools,target=/work" aquasec/trivy:0.76.1 image --input /work/image.tar --severity HIGH,CRITICAL --exit-code 1
docker run --rm --mount "type=bind,source=$PWD/.tools,target=/work" aquasec/trivy:0.76.1 image --input /work/image.tar --format cyclonedx --output /work/sbom.cdx.json
```

**Web check:** GitHub Actions → run → artifacts: inspect coverage, scan report and
SBOM. **Exit check:** a clean build passes the gates; a blocked build has a documented
reason and fix. No AWS deployment has happened yet.

<a id="sprint-9"></a>

## Sprint 9 — Place the AWS services in the complete request path

**What and why:** understand the pieces before creating them. This sprint has no
new application code or resource-creation command.

```text
Developer → GitHub checks → built image → ECR
                                      ↓
                          ECS task definition
                                      ↓
                     ECS service in an ECS cluster
                                      ↓
                       tasks on Fargate compute

Browser → ALB → healthy task IP:8000 → FastAPI → GitHub API
                          ↓
                    CloudWatch Logs
```

| Term and full name | Why we need it |
|---|---|
| ECR — Elastic Container Registry | Stores image bytes ECS must download |
| ECS — Elastic Container Service | Schedules tasks and maintains services |
| ECS cluster | Named scheduling/management boundary for related services; not an application server |
| Task definition | Versioned recipe: image, ports, CPU, memory, permissions and logs |
| Task | One launched copy of that recipe |
| Service | Keeps the desired number of tasks and replaces them during deployments |
| Fargate — product name, not an acronym | Supplies managed compute without you administering EC2 hosts |
| ALB — Application Load Balancer | Accepts HTTP(S) and routes requests to healthy task IPs |
| IAM — Identity and Access Management | Defines who may call which AWS APIs |
| Execution role | Gives ECS startup infrastructure permission to pull images and publish logs |
| Task role | Gives application code permissions if it calls AWS APIs; this app initially needs none |
| CloudWatch Logs | Collects application output from replaceable tasks |
| STS — Security Token Service | Issues temporary credentials and identifies callers |
| VPC — Virtual Private Cloud | Provides the network containing subnets, routes and security groups |
| NAT — Network Address Translation | Lets private-subnet tasks initiate outbound IPv4 internet connections |
| OIDC — OpenID Connect | Lets GitHub prove its workflow identity to AWS for temporary access |

**Console:** open ECR, ECS and EC2 Load Balancers in separate tabs. These may be empty
for this project. Explain why an image in ECR is not yet a running application.

**Exit check:** narrate a deployment and a customer request using the diagram.

<a id="sprint-10"></a>

## Sprint 10 — Account, budget and deployment inputs

**What and why:** choose one account/region and record every billable resource before
creating it. AWS Budgets sends alerts; it does not automatically stop spending.

**Console steps:** Billing and Cost Management → Budgets → create a monthly cost
budget using an amount you deliberately choose. Add actual and forecast notifications
to your email; verify the address. Check current Fargate, ALB, NAT gateway, public
IPv4 and CloudWatch pricing in Mumbai. These resources can cost money while idle.

From `phase_2_app`, repeat sprint 1's three AWS file-path assignments in a new terminal.
Then set these visible session values:

```powershell
$labRegion = 'ap-south-1'
$labProfile = 'phase2-learning'
$labApp = 'fde-api'
$labCluster = 'fde-lab'
$labService = 'fde-api-service'
$labAccount = aws sts get-caller-identity --profile $labProfile --region $labRegion --query Account --output text
if ($LASTEXITCODE -ne 0) { throw 'AWS identity check failed.' }
$labAccount = $labAccount.Trim()
$labRegistry = "$labAccount.dkr.ecr.$labRegion.amazonaws.com"
$labEcrUri = "$labRegistry/$labApp"
Write-Output "Account=$labAccount Region=$labRegion Repository=$labEcrUri"
New-Item -ItemType Directory -Force infra | Out-Null
```

These assignments create no AWS resources. Open `.aws/lab-notes.md` in your editor
and record names/IDs as you get them: account/region, image tag/digest, role ARN,
VPC/subnet/SG IDs, ALB/target/listener ARNs, service/task definition and previous good
release. Keep a separate list of resources you created vs anything shared.

**Permissions:** your CLI identity needs provisioning rights for the named lab
resources, including IAM role creation and passing the execution role to ECS. If an
API denies access, inspect its action/resource and have the account administrator
grant the needed scope. Successful STS login is not proof of provisioning permissions.

**Exit check:** account/region are correct, budget notifications exist, and you know
how to run sprint 28 cleanup. Do not leave NAT/ALB running between learning sessions
without choosing to pay for them.

<a id="sprint-11"></a>

## Sprint 11 — Publish an immutable image to ECR

**What and why:** Fargate cannot pull an image stored only on your laptop. ECR gives
the image an authenticated AWS registry address.

Create this project's private repository once:

```powershell
aws ecr create-repository --repository-name $labApp --image-tag-mutability IMMUTABLE --image-scanning-configuration scanOnPush=true --tags Key=Project,Value=fde-deploy-lab --profile $labProfile --region $labRegion
```

Authenticate Docker to that registry. The password travels through the pipeline,
not into the guide or your Git repository:

```powershell
aws ecr get-login-password --profile $labProfile --region $labRegion | docker login --username AWS --password-stdin $labRegistry
```

Commit your intended source first and require a clean working tree. Generate a
unique release tag using its commit and UTC timestamp:

```powershell
git status --short
if (git status --porcelain) { throw 'Commit or resolve working-tree changes before building a release.' }
$labSha = (git rev-parse HEAD).Trim()
$labTag = "$labSha-local-$([DateTime]::UtcNow.ToString('yyyyMMddHHmmss'))"
docker build --platform linux/amd64 -t "${labApp}:$labTag" .
if ($LASTEXITCODE -ne 0) { throw 'Image build failed.' }
New-Item -ItemType Directory -Force .tools | Out-Null
docker save "${labApp}:$labTag" -o .tools/release-image.tar
if ($LASTEXITCODE -ne 0) { throw 'Could not save the release image.' }
docker run --rm --mount "type=bind,source=$PWD/.tools,target=/work" aquasec/trivy:0.76.1 image --input /work/release-image.tar --scanners vuln --severity HIGH,CRITICAL --exit-code 1
if ($LASTEXITCODE -ne 0) { throw 'Image scan failed; investigate before pushing.' }
docker tag "${labApp}:$labTag" "${labEcrUri}:$labTag"
docker push "${labEcrUri}:$labTag"
if ($LASTEXITCODE -ne 0) { throw 'Image push failed.' }
$labDigest = aws ecr describe-images --repository-name $labApp --image-ids "imageTag=$labTag" --query 'imageDetails[0].imageDigest' --output text --profile $labProfile --region $labRegion
if ($LASTEXITCODE -ne 0 -or $labDigest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'No valid published image digest.' }
$labImage = "${labEcrUri}@$labDigest"
Write-Output $labImage
```

The scan checks this exact new image before publication, rather than relying on a
scan of an earlier build. `--platform linux/amd64` matches the X86_64 task definition
below. `tag` adds a name,
not a new build. `push` uploads. The digest identifies the published bytes; record
it with the source SHA. Never overwrite an immutable tag to make a rerun succeed.
If publishing again, choose a new tag and record the resulting digest deliberately.

**Console:** ECR → Private repositories → `fde-api` → Images. Compare tag/digest and
review scan results. Scan-on-push alone does not block a deployment.

**Exit check:** the exact image is visible in ECR, and sprint 8's scan gate passed
for your intended release. An ECR image still is not a running task.

<a id="sprint-12"></a>

## Sprint 12 — Create the ECS execution role

**What and why:** ECS needs permission to download your image and create log streams.
The application's own AWS permissions would belong in a separate task role. Our
Python app calls GitHub, so we initially omit a task role.

**File: `infra/task-execution-trust.json`**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

Trust answers **who may assume the role**. The permissions policy answers **what it
can do**. Create the dedicated lab role and attach AWS's execution policy:

```powershell
aws iam create-role --role-name fdeLabTaskExecutionRole --assume-role-policy-document file://infra/task-execution-trust.json --tags Key=Project,Value=fde-deploy-lab --profile $labProfile
aws iam attach-role-policy --role-name fdeLabTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy --profile $labProfile
$labExecutionRoleArn = aws iam get-role --role-name fdeLabTaskExecutionRole --query 'Role.Arn' --output text --profile $labProfile
```

**Console:** IAM → Roles → `fdeLabTaskExecutionRole`. Read both Trust relationships
and Permissions. Do not attach AdministratorAccess to fix an unexplained error.
The managed execution policy does not automatically allow arbitrary secrets; sprint
22 adds a scoped secret read if needed. See
[ECS execution roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html).

**Exit check:** record the role ARN and explain why GitHub cannot assume this role.
Allow IAM changes time to propagate before retrying a newly created role.

<a id="sprint-13"></a>

## Sprint 13 — Task definition and CloudWatch log group

**What and why:** translate your Docker runtime settings into an ECS recipe. Registering
a task definition creates a revision; it does not launch a running task.

Create the log destination once and set retention:

```powershell
aws logs create-log-group --log-group-name /ecs/fde-api --tags Project=fde-deploy-lab --profile $labProfile --region $labRegion
aws logs put-retention-policy --log-group-name /ecs/fde-api --retention-in-days 7 --profile $labProfile --region $labRegion
```

**File: `infra/ecs-task-definition.json` — reusable source template**

```json
{
  "family": "fde-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "runtimePlatform": {"cpuArchitecture": "X86_64", "operatingSystemFamily": "LINUX"},
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "REPLACE_EXECUTION_ROLE_ARN",
  "containerDefinitions": [{
    "name": "fde-api",
    "image": "REPLACE_IMAGE_DIGEST_URI",
    "essential": true,
    "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
    "environment": [
      {"name": "ENVIRONMENT", "value": "aws-lab"},
      {"name": "APP_VERSION", "value": "REPLACE_SOURCE_SHA"},
      {"name": "OUTBOUND_TIMEOUT_S", "value": "5"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/fde-api",
        "awslogs-region": "REPLACE_REGION",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "healthCheck": {
      "command": ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 30
    },
    "stopTimeout": 30
  }]
}
```

`awsvpc` gives each task its own network interface. CPU 256 is 0.25 vCPU; memory 512
is MiB. `essential` means this container is required. Port 8000 is the container
port; the laptop-only 8001 mapping does not carry into ECS.

Render a local copy using the values already obtained; the source template remains
portable for CI. These commands show each substitution explicitly:

```powershell
$labTask = Get-Content infra/ecs-task-definition.json -Raw | ConvertFrom-Json
$labTask.executionRoleArn = $labExecutionRoleArn
$labTask.containerDefinitions[0].image = $labImage
($labTask.containerDefinitions[0].environment | Where-Object name -eq APP_VERSION).value = $labSha
$labTask.containerDefinitions[0].logConfiguration.options.'awslogs-region' = $labRegion
$labTaskJson = $labTask | ConvertTo-Json -Depth 30
if ($labTaskJson -match 'REPLACE_') { throw 'Unresolved task-definition input.' }
[IO.File]::WriteAllText("$PWD/.aws/task-definition.json", $labTaskJson)
$labTaskArn = aws ecs register-task-definition --cli-input-json file://.aws/task-definition.json --query 'taskDefinition.taskDefinitionArn' --output text --profile $labProfile --region $labRegion
Write-Output $labTaskArn
```

Do not register the unrendered source template. **Console:** ECS → Task definitions
→ `fde-api` → revision → JSON; CloudWatch → Log groups → `/ecs/fde-api`. Streams
appear only after tasks start. **Exit check:** revision contains the intended digest,
role, source version and region. Record the full task-definition ARN.

<a id="sprint-14"></a>

## Sprint 14 — Networking for Fargate

**What and why:** ALB receives inbound traffic; private tasks need outbound access
to ECR, logs and GitHub. An ALB does not provide outbound internet access to tasks.

For a self-contained lab, create a **dedicated VPC** through the Console. Reusing
Phase 1 resources is optional, but then inspect routing/ownership and never include
shared resources in this workbook's cleanup.

**Console — VPC → Create VPC → VPC and more:**

1. Name prefix `fde-deploy-lab`; IPv4 CIDR `10.42.0.0/16`; no IPv6 for this exercise;
   default tenancy. If connecting to existing networks, choose a non-overlapping CIDR.
2. Two Availability Zones, two public subnets and two private subnets.
3. Public NAT gateways: one per AZ for this two-AZ topology. This incurs ongoing
   charges; create them when ready to deploy and remove them during cleanup. A single
   NAT is a cheaper lab tradeoff but adds a shared failure point/cross-AZ routing.
4. No VPC endpoints for this initial NAT-based exercise. Enable DNS resolution and
   DNS hostnames. Inspect the preview resource map before creating.
5. Wait until NAT gateways are available. Public routes must have `0.0.0.0/0 → igw`;
   private routes must have `0.0.0.0/0 → nat`. Verify actual route-table associations.

See [AWS VPC creation](https://docs.aws.amazon.com/vpc/latest/userguide/create-vpc.html).
These are explicit Console operations; no Terraform or hidden provisioning script.

Copy your real IDs from the resource map into PowerShell:

```powershell
$labVpc = 'REPLACE_VPC_ID'
$labPublicA = 'REPLACE_PUBLIC_SUBNET_A'
$labPublicB = 'REPLACE_PUBLIC_SUBNET_B'
$labPrivateA = 'REPLACE_PRIVATE_SUBNET_A'
$labPrivateB = 'REPLACE_PRIVATE_SUBNET_B'
aws ec2 describe-subnets --subnet-ids $labPublicA $labPublicB $labPrivateA $labPrivateB --query 'Subnets[*].[SubnetId,VpcId,AvailabilityZone,CidrBlock]' --output table --profile $labProfile --region $labRegion
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$labVpc" --profile $labProfile --region $labRegion
```

Create dedicated security groups and explicit inbound rules:

```powershell
$labAlbSg = aws ec2 create-security-group --group-name fde-alb-sg --description 'HTTP entry to the Phase 2 lab' --vpc-id $labVpc --query GroupId --output text --profile $labProfile --region $labRegion
$labTaskSg = aws ec2 create-security-group --group-name fde-task-sg --description 'API only from the lab ALB' --vpc-id $labVpc --query GroupId --output text --profile $labProfile --region $labRegion
aws ec2 authorize-security-group-ingress --group-id $labAlbSg --protocol tcp --port 80 --cidr 0.0.0.0/0 --profile $labProfile --region $labRegion
aws ec2 authorize-security-group-ingress --group-id $labTaskSg --protocol tcp --port 8000 --source-group $labAlbSg --profile $labProfile --region $labRegion
```

Restrict each new group's default IPv4 allow-all egress. First create the needed rules:

```powershell
$labAlbEgress = @(@{IpProtocol='tcp'; FromPort=8000; ToPort=8000; UserIdGroupPairs=@(@{GroupId=$labTaskSg})})
[IO.File]::WriteAllText("$PWD/.aws/alb-egress.json", (ConvertTo-Json -InputObject $labAlbEgress -Depth 10))
aws ec2 authorize-security-group-egress --group-id $labAlbSg --ip-permissions file://.aws/alb-egress.json --profile $labProfile --region $labRegion
$labTaskEgress = @(@{IpProtocol='tcp'; FromPort=443; ToPort=443; IpRanges=@(@{CidrIp='0.0.0.0/0'})})
[IO.File]::WriteAllText("$PWD/.aws/task-egress.json", (ConvertTo-Json -InputObject $labTaskEgress -Depth 10))
aws ec2 authorize-security-group-egress --group-id $labTaskSg --ip-permissions file://.aws/task-egress.json --profile $labProfile --region $labRegion
```

**Console:** Security Groups → each of these two dedicated groups → Outbound rules.
Delete only the default **All traffic / 0.0.0.0/0** rule. Keep ALB → task SG TCP 8000
and task → internet TCP 443. The VPC's Amazon-provided DNS resolver remains available.
No inbound 8000 rule should allow arbitrary internet sources.

Tasks will use private subnets with public IP disabled. NAT supplies their outbound
HTTPS path, including GitHub. AWS VPC endpoints alone would not provide GitHub access.

**Exit check:** both AZs have correct subnets/routes; SG rules match the two separate
traffic paths. Record IDs and NAT Elastic IP allocation IDs for cleanup.

<a id="sprint-15"></a>

## Sprint 15 — ALB, target group and listener

**What and why:** the load balancer is the public entry point. A listener accepts
requests on a port; a target group names the destination pool and health check.

```powershell
$labTgArn = aws elbv2 create-target-group --name fde-api-tg --protocol HTTP --port 8000 --vpc-id $labVpc --target-type ip --health-check-protocol HTTP --health-check-path /health/live --matcher HttpCode=200 --tags Key=Project,Value=fde-deploy-lab --query 'TargetGroups[0].TargetGroupArn' --output text --profile $labProfile --region $labRegion
$labAlbArn = aws elbv2 create-load-balancer --name fde-api-alb --type application --scheme internet-facing --subnets $labPublicA $labPublicB --security-groups $labAlbSg --tags Key=Project,Value=fde-deploy-lab --query 'LoadBalancers[0].LoadBalancerArn' --output text --profile $labProfile --region $labRegion
aws elbv2 wait load-balancer-available --load-balancer-arns $labAlbArn --profile $labProfile --region $labRegion
$labListenerArn = aws elbv2 create-listener --load-balancer-arn $labAlbArn --protocol HTTP --port 80 --default-actions "Type=forward,TargetGroupArn=$labTgArn" --query 'Listeners[0].ListenerArn' --output text --profile $labProfile --region $labRegion
$labAlbDns = aws elbv2 describe-load-balancers --load-balancer-arns $labAlbArn --query 'LoadBalancers[0].DNSName' --output text --profile $labProfile --region $labRegion
$labBaseUrl = "http://$labAlbDns"
Write-Output $labBaseUrl
```

Target type **ip** is necessary for this Fargate/awsvpc design. The listener forwards
to the target group; ECS will register task IPs later. An empty target group and
HTTP 503 at this moment are expected, not proof of a bad Docker image.

**Console:** EC2 → Load Balancers → `fde-api-alb`: inspect subnets, SG and listener.
EC2 → Target Groups → `fde-api-tg`: inspect IP target type, port and health path.
This initial HTTP lab carries no customer data or client secrets. Sprint 25 adds
HTTPS using your own domain and ACM certificate.

**Exit check:** ALB is active, listener references the right target group, and all
resources are in the same VPC/region. Record ARNs and DNS name.

<a id="sprint-16"></a>

## Sprint 16 — ECS cluster, service and two running tasks

**What and why:** a service maintains the desired task count and replaces tasks
during a rollout. The cluster groups that management; Fargate supplies compute.

```powershell
aws ecs create-cluster --cluster-name $labCluster --tags key=Project,value=fde-deploy-lab --profile $labProfile --region $labRegion
```

First-time accounts need the ECS service-linked role. Inspect it in IAM; if absent,
create it once with provisioning permissions:

```powershell
aws iam get-role --role-name AWSServiceRoleForECS --profile $labProfile
```

Only if that reports `NoSuchEntity`:

```powershell
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com --profile $labProfile
```

Create the service with the registered task revision, private networking and ALB:

```powershell
aws ecs create-service --cluster $labCluster --service-name $labService --task-definition $labTaskArn --desired-count 2 --launch-type FARGATE --platform-version LATEST --network-configuration "awsvpcConfiguration={subnets=[$labPrivateA,$labPrivateB],securityGroups=[$labTaskSg],assignPublicIp=DISABLED}" --load-balancers "targetGroupArn=$labTgArn,containerName=fde-api,containerPort=8000" --health-check-grace-period-seconds 60 --deployment-configuration 'minimumHealthyPercent=100,maximumPercent=200,deploymentCircuitBreaker={enable=true,rollback=true}' --tags key=Project,value=fde-deploy-lab --profile $labProfile --region $labRegion
aws ecs wait services-stable --cluster $labCluster --services $labService --profile $labProfile --region $labRegion
aws ecs describe-services --cluster $labCluster --services $labService --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount,deployments:deployments}' --profile $labProfile --region $labRegion
aws elbv2 describe-target-health --target-group-arn $labTgArn --profile $labProfile --region $labRegion
curl.exe "$labBaseUrl/health/live"
curl.exe "$labBaseUrl/version"
curl.exe "$labBaseUrl/repos/octocat/Hello-World"
```

The waiter can take minutes and can time out; inspect events instead of repeatedly
creating services. The circuit breaker can roll back to a previous completed deployment;
the first deployment has no known-good predecessor. A stable service alone does not
prove the requested revision won, so sprint 20 also checks its identity.

**Console:** ECS → `fde-lab` → Services → `fde-api-service`: read Deployments, Events
and Tasks. Open each task and its network interface; compare AZs. EC2 → Target group
→ Targets should show two healthy private IPs. ECS normally spreads tasks across AZs,
but verify actual placement rather than assuming it.

**Exit check:** two tasks running, both targets healthy, health/version/business
requests work. This is the first complete manual cloud deployment.

<a id="sprint-17"></a>

## Sprint 17 — Observe events, logs, task failures and an alarm

**What and why:** a response code alone cannot identify a failing layer. Collect
service events, task stop reasons, target-health reasons and application logs.

```powershell
aws ecs describe-services --cluster $labCluster --services $labService --query 'services[0].events[:10].[createdAt,message]' --output table --profile $labProfile --region $labRegion
aws logs tail /ecs/fde-api --since 15m --profile $labProfile --region $labRegion
$labTasks = (aws ecs list-tasks --cluster $labCluster --service-name $labService --desired-status RUNNING --query taskArns --output json --profile $labProfile --region $labRegion | ConvertFrom-Json)
if ($labTasks.Count -gt 0) { aws ecs describe-tasks --cluster $labCluster --tasks $labTasks --query 'tasks[*].{task:taskArn,status:lastStatus,health:healthStatus,definition:taskDefinitionArn,containers:containers}' --profile $labProfile --region $labRegion }
aws ecs list-tasks --cluster $labCluster --service-name $labService --desired-status STOPPED --profile $labProfile --region $labRegion
```

For a specific stopped task copy its ARN from the last result:

```powershell
$labStoppedTask = 'REPLACE_STOPPED_TASK_ARN'
aws ecs describe-tasks --cluster $labCluster --tasks $labStoppedTask --query 'tasks[0].{reason:stoppedReason,stopCode:stopCode,containers:containers}' --profile $labProfile --region $labRegion
```

**Console:** CloudWatch → Logs → `/ecs/fde-api` → stream. Find an `x-request-id`
from `curl.exe -i` in the application logs. ECS Events explains scheduling failures;
ALB target-health details explain failed routing eligibility.

Add a visible CPU alarm (observation only; no automatic scaling yet):

```powershell
aws cloudwatch put-metric-alarm --alarm-name fde-api-high-cpu --namespace AWS/ECS --metric-name CPUUtilization --dimensions "Name=ClusterName,Value=$labCluster" "Name=ServiceName,Value=$labService" --statistic Average --period 60 --evaluation-periods 3 --threshold 70 --comparison-operator GreaterThanThreshold --treat-missing-data missing --profile $labProfile --region $labRegion
```

**Console:** CloudWatch → Alarms → select this alarm. To receive email, create an
SNS Standard topic in SNS, add/confirm an email subscription, then edit the alarm's
notification action to use it. Record that topic ARN for cleanup. Without an action,
the alarm changes state but sends no email. Missing metrics may initially show
INSUFFICIENT_DATA. CPU alone is not a sufficient production monitoring strategy.

**Exit check:** explain where to find image-pull errors vs application errors vs
ALB health failures. The app logs to stdout, so logs survive task replacement in CloudWatch.

<a id="sprint-18"></a>

## Sprint 18 — GitHub OIDC and a scoped deployment role

**What and why:** give a trusted GitHub workflow temporary AWS access. This is separate
from your laptop's browser-login profile and ECS's execution role.

**GitHub web:** Settings → Environments → create `lab`. Limit deployment branches
to `main`. Add required reviewers if your plan supports them; avoid a self-review
requirement that nobody else can approve. The workflow below uses this environment.

**AWS Console:** IAM → Identity providers → add OpenID Connect provider:
URL `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
If it already exists, inspect/reuse it rather than recreating or deleting a shared provider.

Do not guess the OIDC `sub` string. Newer repositories can include immutable owner
and repository IDs; environment jobs also have a different subject from branch-only
jobs. See [GitHub's subject-format change](https://github.blog/changelog/2026-04-23-immutable-subject-claims-for-github-actions-oidc-tokens/).

**File: `.github/workflows/oidc-inspect.yml`**

```yaml
name: Inspect OIDC identity
on:
  workflow_dispatch:
permissions:
  contents: read
  id-token: write
jobs:
  identity:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: lab
    steps:
      - name: Print only the non-secret identity claims
        shell: python
        run: |
          import base64
          import json
          import os
          import urllib.request

          url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"] + "&audience=sts.amazonaws.com"
          request = urllib.request.Request(url, headers={
              "Authorization": "Bearer " + os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
          })
          with urllib.request.urlopen(request, timeout=15) as response:
              token = json.load(response)["value"]
          segment = token.split(".")[1]
          claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
          print(json.dumps({key: claims.get(key) for key in ("sub", "aud", "repository", "ref")}, indent=2))
```

Commit/push, then Actions → Inspect OIDC identity → Run workflow on main. This
decodes selected claims for inspection; it does not authenticate to AWS or validate
a JWT signature itself. AWS will validate the actual token when assuming the role.
Never print the whole token or its request-token environment variable.

**File: `infra/github-trust.json`** — replace account and the complete observed `sub`:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "arn:aws:iam::REPLACE_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {"StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "REPLACE_EXACT_OBSERVED_SUB"
    }}
  }]
}
```

Do not replace the subject condition with a wildcard. For this environment-based
subject, GitHub's `lab` environment branch restriction is essential.

**File: `infra/github-deploy-policy.json`** — replace account and region throughout:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*"},
    {"Effect": "Allow", "Action": [
      "ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload", "ecr:PutImage", "ecr:DescribeImages"
    ], "Resource": "arn:aws:ecr:REPLACE_REGION:REPLACE_ACCOUNT_ID:repository/fde-api"},
    {"Effect": "Allow", "Action": "ecs:RegisterTaskDefinition", "Resource": "*"},
    {"Effect": "Allow", "Action": ["ecs:UpdateService", "ecs:DescribeServices"],
      "Resource": "arn:aws:ecs:REPLACE_REGION:REPLACE_ACCOUNT_ID:service/fde-lab/fde-api-service"},
    {"Effect": "Allow", "Action": "ecs:ListTasks", "Resource": "*",
      "Condition": {"ArnEquals": {"ecs:cluster": "arn:aws:ecs:REPLACE_REGION:REPLACE_ACCOUNT_ID:cluster/fde-lab"}}},
    {"Effect": "Allow", "Action": "ecs:DescribeTasks",
      "Resource": "arn:aws:ecs:REPLACE_REGION:REPLACE_ACCOUNT_ID:task/fde-lab/*"},
    {"Effect": "Allow", "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::REPLACE_ACCOUNT_ID:role/fdeLabTaskExecutionRole",
      "Condition": {"StringEquals": {"iam:PassedToService": "ecs-tasks.amazonaws.com"}}}
  ]
}
```

Token retrieval and task registration require `Resource: *` for these actions;
repository pushes, service updates and role passing are scoped. This deploy role
cannot create arbitrary IAM roles or change VPCs. Role passing lets ECS use the
specific execution role; it does not let GitHub assume that role directly.

After editing the two JSON files and checking every placeholder:

```powershell
Select-String -Path infra/github-trust.json,infra/github-deploy-policy.json -Pattern REPLACE_
aws iam create-role --role-name fdeLabGitHubDeployRole --assume-role-policy-document file://infra/github-trust.json --tags Key=Project,Value=fde-deploy-lab --profile $labProfile
aws iam put-role-policy --role-name fdeLabGitHubDeployRole --policy-name fdeLabDeploy --policy-document file://infra/github-deploy-policy.json --profile $labProfile
aws iam get-role --role-name fdeLabGitHubDeployRole --query 'Role.Arn' --output text --profile $labProfile
```

`Select-String` must find no `REPLACE_` markers. In GitHub's `lab` environment add
**variables**, not access-key secrets:

| Variable | Value |
|---|---|
| `AWS_REGION` | `ap-south-1` |
| `AWS_ROLE_ARN` | Returned GitHub deploy role ARN |
| `EXECUTION_ROLE_ARN` | ECS execution role ARN |
| `ECR_REPOSITORY` | `fde-api` |
| `ECS_CLUSTER` | `fde-lab` |
| `ECS_SERVICE` | `fde-api-service` |
| `APP_BASE_URL` | `http://` plus your ALB DNS name, no trailing slash |

**Exit check:** exact trust subject and audience are configured; environment allows
main only; no long-lived AWS keys are stored in GitHub. Sprint 19 will test actual
role assumption. [GitHub OIDC guidance](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)

<a id="sprint-19"></a>

## Sprint 19 — Deploy the tested image through GitHub Actions

**What and why:** automate the manual deployment path only after you understand it.
CI builds/scans once; deployment downloads that image, pushes it to ECR, registers
a new task revision and updates the existing service. It does not create the VPC,
ALB, execution role or service for you.

Before adding this workflow, commit the source task-definition template from sprint
13, the reusable CI workflow from sprint 8, and the dependency lock. Finish sprint
18's environment variables and trust policy. The source template deliberately has
placeholders; the workflow replaces them before registration.

**File: `.github/workflows/deploy.yml`**

```yaml
name: Deploy lab
on:
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: phase2-lab-deployment
  cancel-in-progress: false
jobs:
  checks:
    if: github.ref == 'refs/heads/main'
    uses: ./.github/workflows/ci.yml
  deploy:
    needs: checks
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    timeout-minutes: 40
    environment: lab
    permissions:
      contents: read
      id-token: write
    env:
      AWS_REGION: ${{ vars.AWS_REGION }}
      AWS_PAGER: ""
      EXECUTION_ROLE_ARN: ${{ vars.EXECUTION_ROLE_ARN }}
      ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
      ECS_CLUSTER: ${{ vars.ECS_CLUSTER }}
      ECS_SERVICE: ${{ vars.ECS_SERVICE }}
      APP_BASE_URL: ${{ vars.APP_BASE_URL }}
      IMAGE_TAG: ${{ github.sha }}-${{ github.run_id }}-${{ github.run_attempt }}
    steps:
      - uses: actions/checkout@v7.0.1
      - uses: actions/setup-python@v7.1.0
        with:
          python-version: "3.12"
      - uses: actions/download-artifact@v8.0.2
        with:
          name: release-${{ github.run_id }}-${{ github.run_attempt }}
          path: artifact
      - name: Authenticate using GitHub OIDC
        uses: aws-actions/configure-aws-credentials@v6.3.0
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}
      - name: Push the already-tested image and record the previous revision
        shell: bash
        run: |
          set -euo pipefail
          ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
          REGISTRY="$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"
          aws ecr get-login-password | docker login --username AWS --password-stdin "$REGISTRY"
          docker load -i artifact/image.tar
          docker tag "fde-api:$IMAGE_TAG" "$REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"
          docker push "$REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"
          DIGEST=$(aws ecr describe-images --repository-name "$ECR_REPOSITORY" --image-ids "imageTag=$IMAGE_TAG" --query 'imageDetails[0].imageDigest' --output text)
          echo "IMAGE_URI=$REGISTRY/$ECR_REPOSITORY@$DIGEST" >> "$GITHUB_ENV"
          echo "IMAGE_DIGEST=$DIGEST" >> "$GITHUB_ENV"
          PREVIOUS=$(aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" --query 'services[0].taskDefinition' --output text)
          test "$PREVIOUS" != "None"
          echo "PREVIOUS_TASK_ARN=$PREVIOUS" >> "$GITHUB_ENV"
          echo "Previous task definition: $PREVIOUS" >> "$GITHUB_STEP_SUMMARY"
      - name: Render the task definition explicitly
        shell: python
        run: |
          import json
          import os
          from pathlib import Path

          task = json.loads(Path("infra/ecs-task-definition.json").read_text())
          task["executionRoleArn"] = os.environ["EXECUTION_ROLE_ARN"]
          container = next(c for c in task["containerDefinitions"] if c["name"] == "fde-api")
          container["image"] = os.environ["IMAGE_URI"]
          settings = {item["name"]: item["value"] for item in container.get("environment", [])}
          settings["APP_VERSION"] = os.environ["GITHUB_SHA"]
          container["environment"] = [{"name": k, "value": v} for k, v in settings.items()]
          container["logConfiguration"]["options"]["awslogs-region"] = os.environ["AWS_REGION"]
          rendered = json.dumps(task, indent=2)
          if "REPLACE_" in rendered:
              raise RuntimeError("Unresolved task-definition placeholder")
          Path("rendered-task.json").write_text(rendered)
      - name: Register, update and wait
        shell: bash
        run: |
          set -euo pipefail
          NEW_TASK=$(aws ecs register-task-definition --cli-input-json file://rendered-task.json --query 'taskDefinition.taskDefinitionArn' --output text)
          echo "NEW_TASK_ARN=$NEW_TASK" >> "$GITHUB_ENV"
          aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --task-definition "$NEW_TASK" > /dev/null
          aws ecs wait services-stable --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE"
      - name: Check the exact revision and every running task digest
        shell: bash
        run: |
          set -euo pipefail
          aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" > service.json
          TASKS=$(aws ecs list-tasks --cluster "$ECS_CLUSTER" --service-name "$ECS_SERVICE" --desired-status RUNNING --query taskArns --output text)
          test -n "$TASKS" && test "$TASKS" != "None"
          aws ecs describe-tasks --cluster "$ECS_CLUSTER" --tasks $TASKS > tasks.json
          python - <<'PY'
          import json
          import os
          from pathlib import Path

          service_response = json.loads(Path("service.json").read_text())
          assert not service_response.get("failures"), service_response.get("failures")
          service = service_response["services"][0]
          assert service["taskDefinition"] == os.environ["NEW_TASK_ARN"], "Service rolled back or revision differs"
          assert service["desiredCount"] > 0
          assert service["runningCount"] == service["desiredCount"]
          assert service["pendingCount"] == 0
          assert len(service["deployments"]) == 1
          assert service["deployments"][0]["rolloutState"] == "COMPLETED"
          task_response = json.loads(Path("tasks.json").read_text())
          assert not task_response.get("failures"), task_response.get("failures")
          tasks = task_response["tasks"]
          assert len(tasks) == service["desiredCount"]
          for task in tasks:
              assert task["lastStatus"] == "RUNNING"
              assert task["taskDefinitionArn"] == os.environ["NEW_TASK_ARN"]
              container = next(c for c in task["containers"] if c["name"] == "fde-api")
              assert container.get("imageDigest") == os.environ["IMAGE_DIGEST"]
          print("All running tasks match the intended revision and image digest.")
          PY
      - name: Verify the public application path
        shell: python
        run: |
          import json
          import os
          import time
          import urllib.error
          import urllib.request

          base = os.environ["APP_BASE_URL"].rstrip("/")
          def get(path):
              with urllib.request.urlopen(base + path, timeout=10) as response:
                  return json.load(response)

          for attempt in range(12):
              try:
                  assert get("/health/live")["status"] == "alive"
                  assert get("/version")["version"] == os.environ["GITHUB_SHA"]
                  break
              except (urllib.error.URLError, TimeoutError, ValueError, AssertionError, KeyError):
                  if attempt == 11:
                      raise
                  time.sleep(5)
          repo = get("/repos/octocat/Hello-World")
          assert repo["name"] == "octocat/Hello-World"
          assert isinstance(repo["stars"], int)
      - name: Record release identity
        shell: bash
        run: |
          printf 'Source: %s\nImage: %s\nTask: %s\nPrevious: %s\n' "$GITHUB_SHA" "$IMAGE_URI" "$NEW_TASK_ARN" "$PREVIOUS_TASK_ARN" >> "$GITHUB_STEP_SUMMARY"
      - name: Preserve non-secret deployment evidence
        if: always()
        uses: actions/upload-artifact@v7.0.2
        with:
          name: deployment-${{ github.run_id }}-${{ github.run_attempt }}
          path: |
            rendered-task.json
            service.json
            tasks.json
          if-no-files-found: warn
          retention-days: 7
```

The Python blocks are fully shown inline so you can inspect substitutions and
assertions. No boto3 helper hides the AWS operations. The shell steps call the same
AWS APIs you already used. This workflow targets standard GitHub.com hosted runners.

`needs: checks` is the deployment gate. Only the deploy job can request an OIDC
token. Environment protection is evaluated before deployment. `concurrency` avoids
two workflows updating the lab service simultaneously; it does not serialize manual
Console/CLI deployments, so avoid changing the service during a workflow rollout.

For the first run use GitHub → Actions → Deploy lab → Run workflow → main. Watch
each step, then inspect ECR and ECS in the Console. Re-run **all jobs**, rather than
only failed jobs, when creating another attempt: the artifact name intentionally
includes the attempt number and needs its matching CI build.

The final business-path check makes a real GitHub request. Rate limiting/outage can
fail that check even when the deployment itself is healthy. Diagnose before rolling
back. Workflow failure after service update does not automatically undo the update;
the circuit breaker only covers its configured startup/health conditions.

After one successful manual workflow run, you may add this trigger under `on`:

```yaml
push:
  branches: [main]
```

This is an insertion into the existing `on` mapping, not a second workflow. Retain
`workflow_dispatch`. CI will also run separately on pushes, which is redundant but
explicit; the deployment's own required check job is what guarantees it uses its
tested artifact. Keep deployment manual if that better suits the learning lab.

**Exit check:** a failed CI gate cannot deploy; a successful run records source SHA,
ECR digest, task revision and previous revision; all running tasks match. See
[AWS credentials action](https://github.com/aws-actions/configure-aws-credentials)
for OIDC options and [artifact downloads](https://github.com/actions/download-artifact)
for runner/artifact compatibility.

<a id="sprint-20"></a>

## Sprint 20 — Verify the release, not just a green status

**What and why:** healthy old tasks can still answer while new ones fail. Confirm
the intended source, task revision and image digest, not merely HTTP 200.

Read the workflow summary and set the expected values from it:

```powershell
$labExpectedTaskArn = 'REPLACE_TASK_DEFINITION_ARN_FROM_RELEASE'
$labExpectedDigest = 'REPLACE_SHA256_DIGEST_FROM_RELEASE'
$labExpectedSha = 'REPLACE_FULL_SOURCE_COMMIT_SHA'
aws ecs describe-services --cluster $labCluster --services $labService --query 'services[0].deployments[*].[status,taskDefinition,desiredCount,runningCount,pendingCount,rolloutState]' --output table --profile $labProfile --region $labRegion
$labTasks = (aws ecs list-tasks --cluster $labCluster --service-name $labService --desired-status RUNNING --query taskArns --output json --profile $labProfile --region $labRegion | ConvertFrom-Json)
aws ecs describe-tasks --cluster $labCluster --tasks $labTasks --query 'tasks[*].{task:taskArn,revision:taskDefinitionArn,containers:containers[*].{name:name,digest:imageDigest}}' --profile $labProfile --region $labRegion
aws elbv2 describe-target-health --target-group-arn $labTgArn --profile $labProfile --region $labRegion
$labVersion = Invoke-RestMethod "$labBaseUrl/version"
if ($labVersion.version -ne $labExpectedSha) { throw 'Wrong source version is serving traffic.' }
Invoke-RestMethod "$labBaseUrl/repos/octocat/Hello-World"
```

Compare **every task** against the expected revision and digest. One `/version`
response identifies only the task that served it; it does not prove every task
matches. Desired count must be positive, running equal desired, pending zero, one
completed deployment, and intended targets healthy. Autoscaling can change counts
during observation; capture a fresh consistent snapshot if it is active.

**Console:** compare ECS task image digest with ECR. Open CloudWatch logs and record
a request ID from a public request. In `.aws/lab-notes.md` write a release record:

```text
UTC time:
Source commit:
Workflow run:
Image digest:
Task definition ARN:
Previous known-good task ARN:
Desired/running tasks and AZs:
Health/version/business-path result:
Decision: verified / rolled back / unresolved
```

**Exit check:** evidence identifies the exact release. Mark the current revision
known-good only after business-path verification, not merely registration.

<a id="sprint-21"></a>

## Sprint 21 — Rolling updates, graceful shutdown and rollback

**What and why:** replacing a running service must allow new tasks to become healthy
and old requests to finish. Desired count 2 with 100/200 percentages aims to retain
two healthy tasks while allowing up to four during replacement.

In the locked Dockerfile, replace only the CMD line with:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "20"]
```

The task definition already has `stopTimeout: 30`; the app gets time to finish before
ECS can force termination. Configure the lab target group's draining separately:

```powershell
aws elbv2 modify-target-group-attributes --target-group-arn $labTgArn --attributes Key=deregistration_delay.timeout_seconds,Value=30 --profile $labProfile --region $labRegion
```

These values are a starting point for short requests, not universal production
settings. Test with representative long requests before setting real service limits.
Commit and deploy the Dockerfile change through the established gates.

Before any failure drill, capture the verified working revision:

```powershell
$labGoodTaskArn = aws ecs describe-services --cluster $labCluster --services $labService --query 'services[0].taskDefinition' --output text --profile $labProfile --region $labRegion
Write-Output $labGoodTaskArn
```

For a controlled **lab-only** startup failure, create a separate task-definition
revision with a nonexistent image tag. This leaves source and the good revision intact:

```powershell
$labBadTask = Get-Content .aws/task-definition.json -Raw | ConvertFrom-Json
$labBadTask.containerDefinitions[0].image = "${labEcrUri}:deliberately-missing-image"
[IO.File]::WriteAllText("$PWD/.aws/bad-task.json", ($labBadTask | ConvertTo-Json -Depth 30))
$labBadTaskArn = aws ecs register-task-definition --cli-input-json file://.aws/bad-task.json --query 'taskDefinition.taskDefinitionArn' --output text --profile $labProfile --region $labRegion
aws ecs update-service --cluster $labCluster --service $labService --task-definition $labBadTaskArn --profile $labProfile --region $labRegion
```

Watch Events, stopped tasks and deployment state. Do not deploy another workflow
while observing the drill. With a previously completed deployment, the circuit
breaker can roll back after its failure threshold. Without one it cannot invent
a working version. [ECS circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html)

To restore the recorded good revision manually:

```powershell
aws ecs update-service --cluster $labCluster --service $labService --task-definition $labGoodTaskArn --profile $labProfile --region $labRegion
aws ecs wait services-stable --cluster $labCluster --services $labService --profile $labProfile --region $labRegion
```

Repeat sprint 20 against the good release. **Exit check:** explain startup rollback
vs a business regression that passes health checks. Record recovery time and evidence.

<a id="sprint-22"></a>

## Sprint 22 — Optional secrets and startup configuration

**What and why:** public GitHub access works without a token. Add this sprint's secret
only if you need authenticated GitHub API access; otherwise record it as skipped.
The token must be retrieved at task startup, not copied into an image or repository.

**Console:** Secrets Manager → Store a new secret → Other type → Plaintext. Store
the raw GitHub token string (not a JSON object and not a quoted JSON string). Name it
`fde/github-token` in the same region. Use the default AWS-managed encryption key
for this exercise. Choose minimum GitHub permissions appropriate for the repositories
you need. Record only the secret ARN; never its value.

**File: `infra/read-github-secret.json`** — substitute the actual ARN:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "secretsmanager:GetSecretValue",
    "Resource": "REPLACE_EXACT_SECRET_ARN"
  }]
}
```

Grant the **execution role** permission to load that startup secret:

```powershell
aws iam put-role-policy --role-name fdeLabTaskExecutionRole --policy-name ReadGitHubSecret --policy-document file://infra/read-github-secret.json --profile $labProfile
```

In the `fde-api` container object of `infra/ecs-task-definition.json`, add this field
with a comma separating it from its neighboring JSON fields:

```json
"secrets": [
  {"name": "GITHUB_TOKEN", "valueFrom": "REPLACE_EXACT_SECRET_ARN"}
]
```

This is a JSON **fragment**, not a complete file. Remove the placeholder before
committing. The ARN is an identifier; the token is the secret. The workflow preserves
this field when rendering. With a customer-managed KMS key you also need scoped
`kms:Decrypt` and key-policy permissions; that is additional to this default-key lab.

Commit and deploy. **Console:** ECS task definition references the ARN; Secrets
Manager holds the value; CloudWatch should show normal requests without tokens.
Do not add a debug endpoint or print the token to prove injection worked.

When you rotate the token in Secrets Manager, existing task environments do not
change. Start replacement tasks and verify behavior:

```powershell
aws ecs update-service --cluster $labCluster --service $labService --force-new-deployment --profile $labProfile --region $labRegion
aws ecs wait services-stable --cluster $labCluster --services $labService --profile $labProfile --region $labRegion
```

**Exit check:** a fresh task can access the intended GitHub resource; no secret
appears in source, image, workflow artifact or app logs. If startup fails, inspect
resource initialization errors and execution-role permissions before Python code.

<a id="sprint-23"></a>

## Sprint 23 — Diagnose failures from evidence

**What and why:** find the failing layer instead of changing permissions and ports
at random. Use the commands from sprints 17 and 20; no new helper script is needed.

| Symptom | First evidence | Likely area to investigate |
|---|---|---|
| Tests pass, image build fails | Docker build step and requirements lock | Linux dependency/build mismatch |
| ALB returns 503 | Target health, ECS running count | No healthy registered targets |
| Task cannot pull image | Stopped reason, ECR digest, NAT routes | Image reference, execution role or egress |
| GitHub OIDC denied | Workflow claims, IAM trust | Wrong audience/subject/environment |
| Rollout never completes | ECS Events, quotas, health reasons | Capacity, startup, health or networking |
| Repository route returns 504 | Request ID and upstream timeout | GitHub path/latency, not necessarily ALB |
| Health is 200 but wrong version | Every task revision/digest plus `/version` | Old deployment still serving |
| Task exits under load | Exit code, memory graph, logs | Memory limit or app exception |
| CI can push but cannot deploy | Denied API action/resource | ECS scope or `iam:PassRole` |
| Health works, repository route fails | Business request and app logs | Downstream access/rate limit/credentials |

**Manual drill:** use the missing-image task from sprint 21, collect evidence, then
restore the good revision. For a local timeout experiment, use a small timeout in
Compose and recreate it; real-network timing is nondeterministic, while the unit
timeout test gives a repeatable example.

Record one incident as:

```text
Impact and start time:
Observed symptoms:
Hypothesis:
Evidence (command, timestamp, relevant result):
Confirmed cause:
Change made:
Recovery checks:
Prevention/test to add:
```

**Exit check:** distinguish facts from hypotheses and recover without broadening
access unnecessarily. Avoid deliberate failure experiments on shared workloads.

<a id="sprint-24"></a>

## Sprint 24 — CI/CD gates and deliberate automation choices

**What and why:** automation should repeat understood actions. Decide what is
automatic, what needs review, and what evidence establishes a successful release.

| Decision | This lab's default |
|---|---|
| PR checks | Tests, formatting, image build, coverage and vulnerability gate |
| Publish/deploy | Manual workflow on main initially; optional main push later |
| AWS authentication | OIDC and the restricted `lab` environment |
| Artifact | Deploy the image archive that passed the gate, then pin ECR digest |
| Rollback | Circuit breaker for startup/health; deliberate rollback for business regression |
| Secrets | Startup injection; replace tasks after rotation |
| Terraform/Kubernetes | Outside Phase 2 |

**GitHub web exercise:** verify required CI checks and main-branch rules. If your
plan supports environment approvals, observe a deployment waiting for its reviewer
before AWS credentials are requested. Do not claim an approval exists if your plan
does not provide that feature. Keep manual workflow dispatch as an explicit release
decision in that case.

**Exit check:** explain why a red business smoke test can leave a new service running,
why ECR scan-on-push is not automatically a gate, and why a green workflow from a
different commit is insufficient. No additional code is required for this decision sprint.

<a id="sprint-25"></a>

## Sprint 25 — Optional extensions: scaling and HTTPS

These extend the completed deployment. Record each as completed or deliberately
skipped; they are not prerequisites for the basic deployment lab.

### A. Make desired task count respond to load

**What and why:** ECS service desired count is fixed until something changes it.
Fargate supplies compute but does not automatically choose your application's replica count.

Register a range of 2–4 tasks:

```powershell
aws application-autoscaling register-scalable-target --service-namespace ecs --resource-id "service/$labCluster/$labService" --scalable-dimension ecs:service:DesiredCount --min-capacity 2 --max-capacity 4 --profile $labProfile --region $labRegion
```

**File: `infra/cpu-scaling.json`**

```json
{
  "TargetValue": 60.0,
  "PredefinedMetricSpecification": {"PredefinedMetricType": "ECSServiceAverageCPUUtilization"},
  "ScaleOutCooldown": 60,
  "ScaleInCooldown": 120
}
```

```powershell
aws application-autoscaling put-scaling-policy --policy-name fde-api-cpu --service-namespace ecs --resource-id "service/$labCluster/$labService" --scalable-dimension ecs:service:DesiredCount --policy-type TargetTrackingScaling --target-tracking-scaling-policy-configuration file://infra/cpu-scaling.json --profile $labProfile --region $labRegion
aws application-autoscaling describe-scaling-activities --service-namespace ecs --resource-id "service/$labCluster/$labService" --scalable-dimension ecs:service:DesiredCount --profile $labProfile --region $labRegion
```

The provisioning identity may need permission to create the Application Auto Scaling
service-linked role on first use. **Console:** ECS service → Auto Scaling, and
CloudWatch metrics/alarms. Low CPU does not demonstrate a scale-out event; do not
claim load testing from this configuration alone. CPU may be a weak signal for an
I/O-bound API; request rate/latency and downstream limits matter too. Limit tests to
your own lab's health route rather than hammering GitHub. Auto-scaling can change
task counts during sprint 20 verification. See
[target-tracking policy API](https://docs.aws.amazon.com/cli/latest/reference/application-autoscaling/put-scaling-policy.html).

### B. Serve HTTPS using your own domain

**Prerequisite:** a domain you control. Do not invent a certificate for the ALB's
AWS-owned DNS name. Domain registration/hosted zones can have separate costs.

1. ACM Console in `ap-south-1` → request a public certificate for your chosen API
   hostname, such as `api.your-domain.example`. Use DNS validation.
2. Add the provided validation CNAME at your DNS provider; wait for **Issued**.
3. ALB Console → Listeners → add HTTPS 443, select that certificate and an appropriate
   current TLS policy, forward to `fde-api-tg`.
4. ALB SG → add inbound TCP 443 from intended clients. For a public service and the
   hosted-runner smoke check, that means the public client population.
5. Route 53: create an alias record for the API hostname to the ALB. With another DNS
   provider, use its supported subdomain CNAME configuration pointing at ALB DNS.
6. Change HTTP 80 listener to redirect to HTTPS 443 (301). Validate both paths.
7. Change GitHub `APP_BASE_URL` to the new `https://` hostname and your local
   `$labBaseUrl` accordingly. Re-run release checks through HTTPS.

**Exit check:** valid certificate, correct hostname, HTTPS response and intentional
HTTP redirect. Record DNS records/certificate ARN for cleanup. Do not remove shared
domain registrations or hosted zones when cleaning up this lab.

Other advanced topics in the original guide—test matrices, canary routing, a database
or Redis—are separate optional projects. Do not add them merely to make this lab
appear complex; define their independent acceptance tests first.

<a id="sprint-26"></a>

## Sprint 26 — Capstone: diagnose and recover a failed release

**What and why:** combine deployment, observation and recovery without a prepared
answer. Use the dedicated lab and a recorded good release.

1. Capture source SHA, task ARN, image digest, target health and business response.
2. Introduce the missing-image task revision from sprint 21. Predict the failure
   before launching it: the new process cannot start because no image exists.
3. Collect ECS Events and stopped-task details. Observe whether the circuit breaker
   restores the previous revision. Do not just wait for the ALB to return any 200.
4. Restore the known-good revision manually if needed, then verify every task's
   digest and task definition, target health and the public business endpoint.
5. Write the incident report from sprint 23 with exact evidence and elapsed recovery time.
6. Propose a prevention: verify intended ECR digest exists before task registration,
   as the deployment workflow already does after push. Explain which failure types
   that does not prevent (for example, a permission or NAT outage).

**Exit check:** service recovered to the identified good release; evidence is saved;
no intentional bad task definition is still selected by the service. Do not leave a
temporary failure branch as the future deployment source.

<a id="sprint-27"></a>

## Sprint 27 — Final mastery checks and handover

This is a review sprint, not another infrastructure build. A sprint is complete when
its exit check is demonstrated, not when a prescribed number of days has passed.

| Group | Suggested learning sessions |
|---|---|
| Sprints 1–5 | Local API, tests, Docker and Compose |
| Sprints 6–8 | Source history and CI evidence |
| Sprints 9–17 | AWS model and one manual deployment |
| Sprints 18–22 | Controlled automated releases and rollback |
| Sprints 23–29 | Diagnosis, optional extensions, handover and cleanup |

Explain without copying a definition:

- Why an ECR repository is not an ECS cluster, and a task definition is not a task.
- Why the execution role differs from a task role and the GitHub deploy role.
- Where a private task gets internet access and where an ALB sends customer traffic.
- Which values differ between laptop port mapping, task port and ALB listener port.
- Why localhost inside a container is different from localhost on your laptop.
- What coverage, vulnerability findings and an SBOM each do and do not demonstrate.
- How to identify a running release by source, image digest and task revision.
- Which failures trigger automatic rollback and which need business-level checks.

Save a short handover in the repository README: architecture, startup commands,
workflow names, where to find logs, rollback procedure and cleanup ownership. Keep
personal account IDs/resource inventory in the ignored notes if you prefer; never
include secrets. Record optional features as skipped rather than claiming them done.

**Exit check:** another learner can run local tests and explain the deployment from
the repository. The application is an educational deployment; production readiness
still depends on requirements, load tests, data/security needs and operating procedures.

<a id="sprint-28"></a>

## Sprint 28 — Cleanup in dependency order

**What and why:** stopping tasks does not stop ALB/NAT charges. Cleanup must include
the supporting resources you created. These commands are destructive: run them only
when finished with this dedicated lab and after checking names against your inventory.

First disable the Deploy lab workflow in GitHub Actions (and any automatic push
deployment trigger). Ensure no deployment is running. Re-establish sprint 1/10
session variables and restore exact resource IDs from `.aws/lab-notes.md`; do not
guess identifiers or enumerate/delete resources account-wide.

If you enabled scaling, remove the scalable target first so it cannot restore tasks:

```powershell
aws application-autoscaling deregister-scalable-target --service-namespace ecs --resource-id "service/$labCluster/$labService" --scalable-dimension ecs:service:DesiredCount --profile $labProfile --region $labRegion
```

This also removes policies for that scalable target. Skip if scaling was never enabled.
Scale down and delete the lab service, then wait until it is inactive:

```powershell
aws ecs update-service --cluster $labCluster --service $labService --desired-count 0 --profile $labProfile --region $labRegion
aws ecs wait services-stable --cluster $labCluster --services $labService --profile $labProfile --region $labRegion
aws ecs delete-service --cluster $labCluster --service $labService --profile $labProfile --region $labRegion
aws ecs wait services-inactive --cluster $labCluster --services $labService --profile $labProfile --region $labRegion
aws ecs list-tasks --cluster $labCluster --desired-status RUNNING --profile $labProfile --region $labRegion
```

Confirm no lab tasks remain. If other workloads appear, do not delete their cluster.
Delete the dedicated ALB; its listeners are removed with it. Wait before removing
the target group and SGs to allow references/network interfaces to release:

```powershell
aws elbv2 delete-load-balancer --load-balancer-arn $labAlbArn --profile $labProfile --region $labRegion
aws elbv2 wait load-balancers-deleted --load-balancer-arns $labAlbArn --profile $labProfile --region $labRegion
aws elbv2 delete-target-group --target-group-arn $labTgArn --profile $labProfile --region $labRegion
aws ecs delete-cluster --cluster $labCluster --profile $labProfile --region $labRegion
```

The ALB deletion does not delete targets by itself; that is why tasks were removed
first. [ALB deletion semantics](https://docs.aws.amazon.com/cli/latest/reference/elbv2/delete-load-balancer.html)

Save any needed evidence before deleting logs and images:

```powershell
aws cloudwatch delete-alarms --alarm-names fde-api-high-cpu --profile $labProfile --region $labRegion
aws logs delete-log-group --log-group-name /ecs/fde-api --profile $labProfile --region $labRegion
aws ecr delete-repository --repository-name $labApp --force --profile $labProfile --region $labRegion
```

`--force` deletes the repository's images too. Use it only for the dedicated lab
repository, after deciding you no longer need those release artifacts.

**Console cleanup — dedicated VPC only:**

1. In both dedicated SGs, remove the ALB↔task cross-group rules, then delete the two
   SGs after ALB/task network interfaces have gone. Do not delete the default SG.
2. VPC → NAT Gateways: delete the NAT gateways recorded for this lab. Wait for Deleted.
3. VPC/EC2 → Elastic IPs: release the lab NAT allocation IDs after disassociation.
   Deleting a NAT gateway does not itself release its Elastic IP allocation.
4. If you created any VPC endpoints, remove those dedicated to the lab.
5. VPC → Your VPCs → select the exact `fde-deploy-lab` VPC → Delete VPC. Review the
   listed subnets, route tables and internet gateway. Resolve remaining dependencies
   through the Console; do not remove resources belonging to other projects.
6. Verify the VPC, its subnets, NAT gateways and EIPs are gone. If you reused Phase 1
   networking, retain it and document remaining costs instead of deleting it.

**IAM cleanup:** only after tasks/deployments are finished:

```powershell
aws iam delete-role-policy --role-name fdeLabGitHubDeployRole --policy-name fdeLabDeploy --profile $labProfile
aws iam delete-role --role-name fdeLabGitHubDeployRole --profile $labProfile
```

If sprint 22 was used, remove its inline policy first:

```powershell
aws iam delete-role-policy --role-name fdeLabTaskExecutionRole --policy-name ReadGitHubSecret --profile $labProfile
```

Then remove the execution role's managed policy attachment and role:

```powershell
aws iam detach-role-policy --role-name fdeLabTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy --profile $labProfile
aws iam delete-role --role-name fdeLabTaskExecutionRole --profile $labProfile
```

Retain shared service-linked roles and a shared GitHub OIDC provider. If the provider
was created solely for this lab and no other roles use it, delete that exact provider
in IAM. Remove the `lab` environment's stale variables/role reference in GitHub.

**Remaining optional resources:**

- Secrets Manager: schedule deletion of only `fde/github-token` with a recovery
  window; revoke the lab GitHub token at GitHub. Do not force-delete shared secrets.
- SNS: delete the dedicated alarm topic/subscription if created.
- Route 53/DNS: remove only the API record you added. Delete the dedicated ACM
  certificate after detaching its listener; retain shared domains/zones/certificates.
- ECS task definitions: in the Console, deregister the lab's active revisions, then
  delete inactive revisions if you want the inventory removed. Do not delete other families.
- Local Compose: from `phase_2_app`, `docker compose down`. Remove named lab images
  through Docker Desktop if desired; do not use a global prune against other projects.
- GitHub: retain source/evidence as needed; delete large image artifacts if no longer needed.

**Exit check:** no lab tasks, ALB, NAT gateways or allocated EIPs remain; check ECR,
logs, secrets and optional resources against the inventory. Billing/Cost Explorer
data can lag; check again later. Keep the budget alert active if the account remains
in use. Record retained resources and their expected costs explicitly.

<a id="sprint-29"></a>

## Sprint 29 — References and the project's end condition

The core project is complete when you have demonstrated a local app, reproducible
tests/builds, one verified AWS deployment, an OIDC-based gated release, a recovery
drill, and cleanup or a deliberate funded operating plan. Optional scaling/HTTPS
should be recorded honestly as completed or skipped.

Use primary documentation when a command or UI changes:

- [AWS CLI browser login](https://docs.aws.amazon.com/cli/latest/reference/login/)
- [AWS CLI environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)
- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [Docker Compose services](https://docs.docker.com/reference/compose-file/services/)
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)
- [HTTPX mock transports](https://www.python-httpx.org/advanced/transports/#mock-transports)
- [pytest assertions](https://docs.pytest.org/en/stable/how-to/assert.html)
- [pip-tools dependency compilation](https://pip-tools.readthedocs.io/en/stable/)
- [Trivy documentation](https://trivy.dev/latest/docs/)
- [Trivy release used in examples](https://github.com/aquasecurity/trivy/releases/tag/v0.76.1)
- [VPC creation](https://docs.aws.amazon.com/vpc/latest/userguide/create-vpc.html)
- [ECS task-definition parameters](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html)
- [ECS create-service CLI](https://docs.aws.amazon.com/cli/latest/reference/ecs/create-service.html)
- [ECS execution-role permissions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)
- [GitHub OIDC with AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [OIDC subject-format changes](https://github.blog/changelog/2026-04-23-immutable-subject-claims-for-github-actions-oidc-tokens/)
- [AWS credentials action](https://github.com/aws-actions/configure-aws-credentials)
- [Checkout releases](https://github.com/actions/checkout/releases)
- [Python setup releases](https://github.com/actions/setup-python/releases)
- [Artifact upload releases](https://github.com/actions/upload-artifact/releases)
- [Artifact download releases](https://github.com/actions/download-artifact/releases)
- [ECS circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html)
- [Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [VPC pricing, including NAT/public IPv4](https://aws.amazon.com/vpc/pricing/)
- [Load balancing pricing](https://aws.amazon.com/elasticloadbalancing/pricing/)

The original [Phase 2 guide](../Phase_2_Deployment_and_Automation_FDE_Guide.md) remains
the broader conceptual reference. This workbook adapts its path to your actual
Windows/global-Python project and manual-first learning preference. The optional
extensions are selected exercises, not an implementation of every advanced idea in
that guide. Kubernetes/EKS, Terraform, databases, queues, disaster recovery and
production SLO design belong to a deliberately scoped follow-up project.

**Document validation:** the embedded source and structured snippets can be checked
locally; AWS/GitHub execution still requires your real IDs, permissions and account
state. Writing this workbook does not mean those future sprints have been executed.
