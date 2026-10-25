# Phase 2 application — Windows setup and FastAPI

This folder is the implementation workspace for the Phase 2 guide. Steps 1 and 2
are complete: the Windows setup and initial AWS CLI sign-in were verified, and the
FastAPI application was implemented and checked locally on 2026-10-25. Step 3's
automated test suite is now implemented and verified; run it yourself using the
instructions below. No AWS infrastructure has been deployed.

## Your environment

- Use **Windows PowerShell or PowerShell 7** for local commands.
- Use your **globally installed Python 3.12**. No virtual environment is created.
- Python, pip and Git were already installed. Step 2's dependency installation found
  all requirements already satisfied, so no global package upgrades were needed.
- Docker Desktop and Compose were already installed. Its existing WSL2 backend runs
  Linux containers; you do **not** need a separate Ubuntu distribution or terminal.
- AWS CLI v2 was installed for the current Windows user using the official,
  signature-verified installer. AWS CLI includes its own Python runtime; that does
  not replace the global Python used for this application.

Docker Desktop must be running when working with containers. Open it from the
Start menu after a restart and wait for the engine to be ready.

Validated on 2026-10-25 using both Windows PowerShell 5.1 and PowerShell 7:

| Prerequisite | Observed result |
|---|---|
| Global Python | 3.12.6; no virtual environment |
| pip for that Python | 26.2.1 |
| Git | 2.51.1.windows.1; local repository on `main` |
| Docker client and engine | 28.5.1; engine running in Linux-container mode |
| Docker Compose | v2.40.0-desktop.1 |
| AWS CLI | 2.38.5, installed for the current Windows user |
| AWS identity | PASS: browser sign-in completed; STS verified `phase2-learning` on 2026-10-25 |

## Start here in PowerShell

Run these commands yourself, one block at a time. The AWS learning steps use direct
CLI commands, with an explanation of their purpose and expected output.

From the parent `Networking_AWS` directory, enter the project:

```powershell
cd .\phase_2_app
```

### Check the installed tools manually

```powershell
python --version
python -m pip --version
git --version
docker --version
docker compose version
aws --version
```

Each command prints the installed version. `python -m pip` uses pip belonging to
the Python interpreter you selected. AWS should report `aws-cli/2...`.

If PowerShell says `aws` is not recognized, add the installation directory to this
terminal's search path, then try again:

```powershell
$env:PATH = "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2;$env:PATH"
aws --version
```

`PATH` is the list of folders Windows searches for executable commands. This line
adds the directory where AWS CLI was installed on your laptop. It affects this
terminal only; it does not install AWS CLI again.

To check whether Docker's engine is running, open Docker Desktop and then run:

```powershell
docker info --format '{{.OSType}}'
```

Expected output: `linux`. A connection error means Docker's engine is unavailable;
wait for Docker Desktop to finish starting. Printing the Docker version alone
checks the client, not whether the engine works. Docker is needed for later container
steps, not for running AWS CLI.

### Tell AWS CLI where this project's existing sign-in files live

Run the following while your current directory is `phase_2_app`, in each new
PowerShell terminal where you want to use this project's AWS sign-in:

```powershell
$env:AWS_CONFIG_FILE = "$PWD\.aws\config"
$env:AWS_SHARED_CREDENTIALS_FILE = "$PWD\.aws\credentials"
$env:AWS_LOGIN_CACHE_DIRECTORY = "$PWD\.aws\login\cache"
```

`$env:NAME = ...` sets an environment variable for this terminal and commands launched
from it. `$PWD` is the current directory. These assignments point to the existing
project-local AWS files; they do not sign you in or create AWS resources.

| Variable | Why it is set here |
|---|---|
| `AWS_CONFIG_FILE` | Locates the file containing named profiles and settings |
| `AWS_SHARED_CREDENTIALS_FILE` | Selects the separate credentials-file location; browser login does not require you to create permanent access keys in it |
| `AWS_LOGIN_CACHE_DIRECTORY` | Locates the temporary credentials and refresh-token cache created by browser login |

Normally AWS CLI uses files under your Windows user folder. Our earlier setup used
`phase_2_app/.aws/` to keep project setup here, so these paths let the CLI reuse that
sign-in. The directory is ignored by Git and Docker. The path settings are temporary;
the files remain after you close PowerShell. See the official
[AWS environment-variable documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html).

### Verify your existing AWS session

```powershell
aws sts get-caller-identity --profile phase2-learning --region ap-south-1 --no-cli-pager
```

Read this command as follows:

| Part | Meaning |
|---|---|
| `aws` | Run AWS CLI on your laptop |
| `sts` | Contact AWS Security Token Service |
| `get-caller-identity` | Ask AWS which identity this request is using |
| `--profile phase2-learning` | Select the named set of local settings and sign-in information |
| `--region ap-south-1` | Select Mumbai explicitly for this command |
| `--no-cli-pager` | Print the result directly in the terminal |

Expected output is JSON with `UserId`, `Account` and `Arn`. An ARN (Amazon Resource
Name) identifies the IAM user or assumed role making the request. This verifies
authentication; it does not prove permission to deploy every service. The request
creates no cloud resources. If the session expired, use the manual sign-in section
below, then retry this command.

## Run the application — step 2

From `phase_2_app` in PowerShell:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Keep that terminal open. Uvicorn serves the application and prints request logs;
`--reload` restarts the development server after source changes. Press **Ctrl+C**
in that terminal to stop it. There is no virtual-environment activation step.
The local API does not need AWS credentials, Docker or a GitHub token to access
public repositories. It does need internet connectivity for the GitHub route.

Open **http://127.0.0.1:8000/docs** in your browser. This interactive API page lets
you expand an endpoint, select **Try it out**, enter parameters and select **Execute**.
The root URL `/` has no route; use `/docs` or an endpoint below.

In a second PowerShell terminal, you can also call:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/live
Invoke-RestMethod http://127.0.0.1:8000/health/ready
Invoke-RestMethod http://127.0.0.1:8000/version
Invoke-RestMethod http://127.0.0.1:8000/repos/octocat/Hello-World
```

| Endpoint | What happens | Expected result |
|---|---|---|
| `/health/live` | Checks that the application can respond without contacting dependencies | `status: alive`, with the configured version |
| `/health/ready` | Checks that local startup completed and the HTTP client is initialized | `status: ready`; it does not check GitHub availability |
| `/version` | Returns startup configuration and machine identity | Version `dev`, environment `local`, and your hostname by default |
| `/repos/{owner}/{repo}` | Makes an outgoing GitHub API request and selects four response fields | Repository name, stars, forks and URL |

Star and fork counts change over time. Every response includes an `x-request-id`
header; the corresponding application log includes the ID, route, status and latency.
Use `curl.exe -i http://127.0.0.1:8000/health/live` to see response headers.

### What each application file does

`app/config.py` reads configuration at startup. Environment variables override the
optional project-root `.env` file; defaults make the local app work without either.
The timeout must be a positive finite number, and the optional token is represented
as a secret value rather than an ordinary printable setting.

`app/github_client.py` makes the outgoing HTTPS request. It uses a bounded connection
pool and explicit timeouts, then maps GitHub's response into `name`, `stars`, `forks`
and `url`. It returns controlled API errors rather than exposing upstream bodies or
credentials. There are no automatic retries in this stage.

`app/main.py` creates the FastAPI app, registers routes and logs requests. Its lifespan
function creates one shared HTTP client when the server starts and closes it when
the server stops. This reuses connections across requests rather than creating a
new HTTP client for every request. `create_app()` also lets later tests supply settings.

```text
Browser / PowerShell request
    -> Uvicorn -> FastAPI route
    -> shared HTTPX client -> GitHub API
    -> validated repository summary -> HTTP response
```

The health/version routes skip the GitHub part of this path. A GitHub outage can
therefore fail the repository route while the live endpoint still responds.

### Configuration and error behavior

The optional `.env.example` documents defaults. If you want a local configuration
file, copy it once to `.env` and edit that ignored file. Do not overwrite an existing
`.env` that contains your settings.

For a temporary PowerShell override, set a value **before starting Uvicorn**:

```powershell
$env:APP_VERSION = 'local-step2'
$env:ENVIRONMENT = 'development'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Restart the server after changing environment variables or `.env`; a source-file
reloader does not guarantee that it reloads configuration-file changes. Remove a
temporary override with `Remove-Item Env:APP_VERSION` or `Remove-Item Env:ENVIRONMENT`.

| Situation | API status |
|---|---|
| GitHub returns repository not found | 404 |
| Invalid owner/repository input | 422 |
| GitHub request times out | 504 |
| Connection failure, denied upstream access or upstream server failure | 502 |
| GitHub rate limit | 503; preserves a numeric `Retry-After` header when supplied |
| Unexpected status, redirect or invalid upstream JSON/fields | 502 |

A generic upstream 403 is distinguished from a rate-limit response. Redirects are
not followed in this stage; use the current owner/name of a renamed repository.
HTTPX timeouts apply to connection/read/write/pool operations rather than one overall
wall-clock deadline. `OUTBOUND_TIMEOUT_S=0.001` can demonstrate timeout behavior, but
use a simulated timeout when you need a deterministic result.

For public repositories, leave `GITHUB_TOKEN` empty. If needed later, supply a token
through the ignored `.env` file or the current shell. Do not put it in source or logs.

## Step 2 validation

- Ruff lint and formatting checks passed for all application files.
- 27 controlled checks covered routes/configuration, upstream success and failure
  responses, request IDs, readiness and HTTP-client cleanup.
- Real HTTP requests to Uvicorn verified health, readiness, version, API docs/schema,
  a live GitHub repository response and a missing-repository response.
- These step 2 checks were implementation-time verification. Step 3 now supplies
  the saved pytest suite described below.

The global environment already had three dependency conflicts before step 2:
`langchain-openai` requires an OpenAI version below the installed one, and
`tp-market-research-agent` requires newer FastAPI and Uvicorn versions. No packages
were changed by this step, and these pre-existing conflicts were not repaired.
The application checks above pass, but `python -m pip check` for the entire shared
environment is not clean. Dependency ranges in `requirements.txt` are not a full lock
file; production dependency locking and scanning belong to later packaging/CI work.

## Run and understand the tests — step 3

Your browser check confirmed a real request worked. Saved tests let you repeat
checks after every code change and exercise failures without waiting for an actual
GitHub outage. From `phase_2_app`, run this command yourself in PowerShell:

```powershell
python -m pytest tests/test_api.py::test_liveness -v
```

Start with this one test. `python -m pytest` runs the test runner through your global
Python. The file path and `::test_liveness` select one test; `-v` shows its name and
result. Expected: `test_liveness PASSED` and `1 passed`.

Open `tests/test_api.py` and find `test_liveness`. It asks the application for
`/health/live`, checks for HTTP 200, then compares the body with the expected status
and version. Each `assert` says "this must be true"; pytest reports a failure if it
is false. The test uses version `test-version` so it does not depend on your local
development version. Now run the whole suite:

```powershell
python -m pytest -v
```

Expected: **29 passed**. `test_api.py` checks the HTTP routes, response bodies,
request IDs, readiness and shutdown. `test_client.py` checks the GitHub helper's
handling of successful responses, errors, rate limits and invalid data. See
[the testing walkthrough](tests/README.md) for the fixtures and simulated responses.

The suite does not require Uvicorn to be running, AWS sign-in or real GitHub
credentials. It calls the app inside the test process and simulates GitHub using
HTTPX's mock transport. It does not verify Docker, an actual listening network port
or AWS deployment; those need checks in their own stages.

The required pytest and Ruff versions were already installed globally. Their
versions are recorded in `requirements-dev.txt`. If preparing another Python
installation, `python -m pip install -r requirements-dev.txt` installs the listed
dependencies; there is no virtual-environment step.

Run the remaining code-quality checks individually:

```powershell
python -m ruff check app tests
python -m ruff format --check app tests
```

The first checks rules such as unused imports and undefined names. The second checks
formatting without changing files. Both should pass. `python -m pytest -q` is the
shorter test output option after you are familiar with the test names.

### Optional learning exercise: see a test fail

In `test_liveness`, temporarily change the expected `"status": "alive"` to
`"status": "healthy"`. Run only that test again. It should fail and display the
expected/actual difference. Immediately after the test command, run
`$LASTEXITCODE` in PowerShell: a test failure produces `1`, while a successful run
produces `0`. Restore `alive` and rerun the test to get a pass. This is the signal
that a later CI workflow will use to block deployment when a test fails.

## AWS sign-in — renewing your session

The `phase2-learning` profile has been configured and its current session verified.
When the session expires, use the browser sign-in supported by the installed CLI;
you do not need to paste permanent access keys here. Successful sign-in verifies
identity, not permission for every future ECR/ECS operation. No cloud resources
were created during step 1.

First set the three AWS file-location environment variables shown in "Start here
in PowerShell". Then run this command yourself:

```powershell
aws login --profile phase2-learning --region ap-south-1
```

`login` opens your browser to authorize AWS CLI. Select your development IAM user
or role and finish the local-development authorization. AWS CLI stores temporary
credentials and a refresh token locally. It can renew the credentials while the
refresh token remains valid. See the official
[`aws login` reference](https://docs.aws.amazon.com/cli/latest/reference/login/).

Wait for the terminal to report success, then verify the identity separately:

```powershell
aws sts get-caller-identity --profile phase2-learning --region ap-south-1 --no-cli-pager
```

If you land on the normal AWS Console homepage, console sign-in has succeeded but
CLI authorization may still be pending. Return to the original CLI authorization
tab or the URL printed by the running login command, select your development
session and finish authorization. Keep the login command running until the browser
redirects back and the terminal reports success. If the link expires, rerun
the `aws login` command and use the new link. CLI setup is verified when
`get-caller-identity` succeeds, not merely when the Console homepage opens.

This flow requires permission to sign in for local development. If an IAM user/role
gets AccessDenied, your AWS account administrator must provide the appropriate
`SignInLocalDevelopmentAccess` policy. That policy enables sign-in; it does not
automatically grant future ECR/ECS deployment permissions. If you only have the root
account login, set up an appropriate development identity before the deployment labs;
do not create root access keys. If your organization instead uses IAM Identity Center,
use its SSO setup and administrator-provided portal details.

### Inspect or change the profile settings manually

The region and output format were configured during step 1. Inspect them:

```powershell
aws configure get region --profile phase2-learning
aws configure get output --profile phase2-learning
```

Expected values are `ap-south-1` and `json`. To set those values yourself:

```powershell
aws configure set region ap-south-1 --profile phase2-learning
aws configure set output json --profile phase2-learning
```

`configure get` reads a setting; `configure set` writes it to the selected local
configuration file. These commands neither sign you in nor create cloud resources.
The explicit `--profile` and `--region` flags in our service commands keep the chosen
profile and region visible as you learn. A command-line region overrides the saved
region setting. Mumbai matches the guide; your browser Console's region selection
is independent of these CLI settings.

## Repository structure

```text
phase_2_app/
  app/
    __init__.py
    main.py                 # FastAPI routes, lifespan and request logging
    config.py               # Application settings
    github_client.py        # GitHub integration and response validation
  tests/
    test_api.py             # API responses, readiness and request IDs
    test_client.py          # GitHub success/failure handling
    README.md               # How to run and understand the tests
  infra/
    README.md               # Later: ECS/IAM configuration templates
  .github/workflows/
    README.md               # Later: CI and deployment workflows
  .gitignore
  .dockerignore
  .gitattributes
  .env.example              # Optional configuration template; no real credentials
  pyproject.toml
  requirements.txt          # Runtime dependencies for the implemented API
  requirements-dev.txt      # Development dependency list
  README.md
  .aws/                     # Ignored local AWS configuration/session cache
  .tools/                   # Ignored downloaded installer and install log
```

The Dockerfile, Compose file and AWS workflow YAML belong to
their corresponding stages. Learn and run the underlying commands manually before
introducing automation in the CI/CD stages. Empty YAML
workflows and nonfunctional Dockerfiles have not been created. The local Git repository
starts on `main`; no remote, commit or GitHub publication is configured yet.

## Translating the guide's Ubuntu commands

| Guide uses Bash | Use in this Windows project |
|---|---|
| `python3` | `python` |
| `python3 -m venv .venv` and `source ...` | Skip: you requested global Python |
| `pip install ...` | `python -m pip install ...` |
| `export AWS_REGION=ap-south-1` | `$env:AWS_REGION = 'ap-south-1'` |
| `export AWS_PROFILE=learning` | Use `--profile phase2-learning` explicitly on AWS commands |
| `$AWS_REGION` in shell commands | `$env:AWS_REGION` |
| `curl` | `curl.exe` to avoid Windows PowerShell's alias |
| Bash `\` line continuations / heredocs | Use the PowerShell instructions supplied for each stage |

Docker commands such as `docker version` and `docker compose version` work directly
from PowerShell. The project's future container still uses Linux internally. CI can
also use a GitHub-hosted Linux runner independently of your laptop's operating system.

## References

- [AWS CLI installation for Windows](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [AWS CLI browser sign-in and required permissions](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html)
- [AWS login cache configuration](https://docs.aws.amazon.com/cli/latest/reference/login/)
- [Docker Desktop WSL2 backend](https://docs.docker.com/desktop/features/wsl/)
- [FastAPI lifespan and startup/shutdown](https://fastapi.tiangolo.com/advanced/events/)
- [HTTPX asynchronous clients and connection reuse](https://www.python-httpx.org/async/)
- [GitHub API error and rate-limit behavior](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api)
