import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture
def make_client(monkeypatch):
    def _make(**env: str) -> TestClient:
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        get_settings.cache_clear()
        return TestClient(create_app())

    yield _make
    get_settings.cache_clear()


def preflight(client: TestClient, origin: str):
    return client.options(
        "/api/health",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )


def test_listed_origin_is_allowed(make_client):
    client = make_client(CORS_ORIGINS="https://hirelens.onrender.com")
    response = preflight(client, "https://hirelens.onrender.com")
    assert response.headers.get("access-control-allow-origin") == "https://hirelens.onrender.com"


def test_origin_regex_allows_matching_origins_only(make_client):
    client = make_client(
        CORS_ORIGINS="http://localhost:5173",
        CORS_ORIGIN_REGEX=r"https://hirelens[a-z0-9-]*\.onrender\.com",
    )

    allowed = preflight(client, "https://hirelens-x1y2.onrender.com")
    assert allowed.headers.get("access-control-allow-origin") == "https://hirelens-x1y2.onrender.com"

    blocked = preflight(client, "https://evil.example.com")
    assert "access-control-allow-origin" not in blocked.headers
