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
