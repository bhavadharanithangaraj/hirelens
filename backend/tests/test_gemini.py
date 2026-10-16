import asyncio

import httpx
import pytest

from app.llm import LLMError
from app.llm.gemini import GeminiClient


def ok(text: str) -> httpx.Response:
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})


def busy() -> httpx.Response:
    return httpx.Response(503, json={"error": {"message": "This model is currently experiencing high demand."}})


def make_client(replies: dict[str, list[httpx.Response]], **kwargs) -> tuple[GeminiClient, list[str], list[float]]:
    """Fake Gemini API: each model returns its scripted replies in order."""
    calls: list[str] = []
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        model = request.url.path.split("/models/")[1].split(":")[0]
        calls.append(model)
        return replies[model].pop(0)

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GeminiClient(api_key="k", model="main", http_client=http, sleep=fake_sleep, **kwargs), calls, sleeps


def test_retries_busy_model_then_succeeds():
    client, calls, sleeps = make_client({"main": [busy(), busy(), ok("{}")]})

    assert asyncio.run(client.generate("p")) == "{}"
    assert calls == ["main", "main", "main"]
    assert sleeps == [1.0, 3.0]


def test_falls_back_when_main_model_stays_busy():
    client, calls, _ = make_client({"main": [busy()] * 3, "lite": [ok('{"a": 1}')]}, fallback_models=["lite"])

    assert asyncio.run(client.generate("p")) == '{"a": 1}'
    assert calls == ["main", "main", "main", "lite"]


def test_reports_main_model_error_when_all_models_fail():
    not_found = httpx.Response(404, json={"error": {"message": "models/lite is not found"}})
    client, _, _ = make_client({"main": [busy()] * 3, "lite": [not_found]}, fallback_models=["lite"])

    with pytest.raises(LLMError, match="HTTP 503: This model is currently experiencing high demand"):
        asyncio.run(client.generate("p"))


def test_client_errors_are_not_retried():
    bad_key = httpx.Response(400, json={"error": {"message": "API key not valid."}})
    client, calls, sleeps = make_client({"main": [bad_key]})

    with pytest.raises(LLMError, match="HTTP 400: API key not valid"):
        asyncio.run(client.generate("p"))
    assert calls == ["main"]
    assert sleeps == []
