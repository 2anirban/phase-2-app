# Step 3: understand and run the tests

Run commands from `phase_2_app`, in PowerShell, using your global Python.

```powershell
python -m pytest tests/test_api.py::test_liveness -v
python -m pytest -v
```

The first command selects one test by file and function name. The second discovers
all `test_` functions under `tests/` and prints each result. Expected results are
`1 passed` and `29 passed`, respectively.

## Read the first test

```python
def test_liveness(application):
    with TestClient(application) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive", "version": "test-version"}
```

1. `application` is a fresh test application prepared by the fixture in this file.
2. `TestClient` sends requests directly to that app inside the Python process.
3. `with` runs startup before the requests and shutdown afterward.
4. The two `assert` statements check the HTTP status and response body.

An assertion is a statement that must be true. When it is false, pytest shows what
was expected and what actually happened. See the official
[pytest assertion explanation](https://docs.pytest.org/en/stable/how-to/assert.html).

## What is a fixture or a mock?

A **fixture** prepares a test's starting conditions. The `application` fixture
creates an app with explicit test settings, including version `test-version`, and
a simulated connection to GitHub. Each test gets fresh state.

A **mock** stands in for something external. Here, `httpx.MockTransport` supplies
known GitHub responses in memory. It can also raise a timeout immediately. This
makes success and failure cases repeatable without waiting for the real GitHub API.
See [HTTPX mock transports](https://www.python-httpx.org/advanced/transports/#mock-transports).

`monkeypatch` is pytest's mechanism for temporarily replacing a value or function.
The API tests replace the outgoing HTTP-client factory where `app.main` uses it.
The actual route and GitHub response-processing code still run. The replacement
is undone after each test. No application source file is rewritten.

## Why two test files?

| File | What it exercises |
|---|---|
| `test_api.py` | Requests to the app: health, readiness, version, repository output, request IDs, invalid input and a timeout response |
| `test_client.py` | The GitHub helper: response conversion, errors, rate limits, retry hints, invalid data and connection failures |

`@pytest.mark.parametrize` runs one test function with multiple input rows. Each row
counts as a separate test, which is why there are more test cases than functions.
`pytest.raises(HTTPException)` checks that a failure raises the expected exception;
the assertions underneath check the status and message. `asyncio.run` lets a normal
test run our asynchronous GitHub helper.

The guide's illustrative snippets use an earlier client structure. These saved
tests match the implemented shared HTTP client and startup/shutdown lifecycle.

## What passing tests establish

The suite verifies the specified behavior for controlled inputs. It requires no
running Uvicorn server, real GitHub token or AWS credentials. It does not prove that
the real GitHub service, Docker networking or AWS deployment works. Your browser
check exercised the real server and GitHub separately; later stages add deployment
checks. No helper scripts are involved in running this suite.

For a deliberate failure exercise, follow the project README: change one expected
health status, observe the failure and exit code, then restore it and rerun.
