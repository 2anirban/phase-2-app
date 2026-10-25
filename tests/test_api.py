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
