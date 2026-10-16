import asyncio

import pytest

from app.deps import get_llm_client
from app.llm import LLMError, MockClient, complete_json
from app.main import app
from app.schemas import JDRequirements
from tests.conftest import JD, RESUME


class ScriptedClient:
    """Returns pre-set responses in order and records every prompt it receives."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.responses.pop(0)


class FlakyClient(MockClient):
    """Behaves like the mock, but the first reply is broken JSON."""

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return "Sure! Here is your JSON: {oops"
        return await super().generate(prompt)


VALID = '{"role_title": "Dev", "required_skills": ["Python", "python", " "], "nice_to_have_skills": []}'


def test_complete_json_parses_and_cleans():
    client = ScriptedClient([f"```json\n{VALID}\n```"])
    result = asyncio.run(complete_json(client, "prompt", JDRequirements))
    assert result.required_skills == ["Python"]  # code fence stripped, duplicates/blanks removed


def test_complete_json_retries_once_then_succeeds():
    client = ScriptedClient(["not json", VALID])
    result = asyncio.run(complete_json(client, "prompt", JDRequirements))

    assert result.role_title == "Dev"
    assert len(client.prompts) == 2
    assert "not valid JSON" in client.prompts[1]  # retry includes the validation feedback


def test_complete_json_raises_after_retry():
    client = ScriptedClient(["not json", '{"role_title": ""}'])
    with pytest.raises(LLMError):
        asyncio.run(complete_json(client, "prompt", JDRequirements))
    assert len(client.prompts) == 2


def test_analyze_recovers_from_one_bad_response(client):
    flaky = FlakyClient()
    app.dependency_overrides[get_llm_client] = lambda: flaky

    response = client.post("/api/analyze", json={"resume_text": RESUME, "jd_text": JD})

    assert response.status_code == 201
    assert flaky.calls == 4  # step 1 twice (retry) + steps 2 and 3


def test_analyze_returns_502_when_llm_keeps_failing(client):
    app.dependency_overrides[get_llm_client] = lambda: ScriptedClient(["garbage", "still garbage"])

    response = client.post("/api/analyze", json={"resume_text": RESUME, "jd_text": JD})

    assert response.status_code == 502
    assert "invalid response" in response.json()["detail"]
    assert client.get("/api/history").json() == []  # nothing saved on failure
