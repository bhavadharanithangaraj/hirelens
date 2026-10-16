import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence

import httpx

from app.llm.base import LLMError

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# Overloaded or rate-limited: worth retrying after a short pause.
RETRYABLE_STATUS = {429, 500, 503}
RETRY_DELAYS_SECONDS = (1.0, 3.0)


class GeminiClient:
    """Minimal async client for the Gemini generateContent REST endpoint.

    Using httpx directly (instead of the SDK) keeps the dependency footprint small and
    makes the request/response shape explicit. Busy responses (429/5xx) are retried with
    a short backoff, then the next model in `fallback_models` is tried.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.8-flash",
        timeout: float = 60.0,
        http_client: httpx.AsyncClient | None = None,
        fallback_models: Sequence[str] = (),
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._api_key = api_key
        self._models = [model, *(m for m in fallback_models if m and m != model)]
        self._timeout = timeout
        self._http_client = http_client
        self._sleep = sleep

    async def generate(self, prompt: str) -> str:
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                # JSON mode: the model is constrained to emit a JSON document.
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }

        first_error: LLMError | None = None
        for index, model in enumerate(self._models):
            try:
                return await self._generate_with_retries(model, payload)
            except LLMError as exc:
                first_error = first_error or exc
                if index + 1 < len(self._models):
                    logger.warning("Gemini model %s failed (%s); falling back to %s", model, exc, self._models[index + 1])
        # Report the primary model's error: a fallback's "not found" would only confuse.
        assert first_error is not None
        raise first_error

    async def _generate_with_retries(self, model: str, payload: dict) -> str:
        for attempt in range(len(RETRY_DELAYS_SECONDS) + 1):
            response = await self._post(model, payload)
            if response.status_code == 200:
                return _extract_text(response.json())
            error = LLMError(f"The AI model returned HTTP {response.status_code}: {_error_message(response)}")
            if response.status_code not in RETRYABLE_STATUS or attempt == len(RETRY_DELAYS_SECONDS):
                raise error
            logger.warning("Gemini %s returned %d; retrying", model, response.status_code)
            await self._sleep(RETRY_DELAYS_SECONDS[attempt])
        raise AssertionError("unreachable")

    async def _post(self, model: str, payload: dict) -> httpx.Response:
        url = f"{GEMINI_BASE_URL}/models/{model}:generateContent"
        headers = {"x-goog-api-key": self._api_key}
        try:
            if self._http_client is not None:
                return await self._http_client.post(url, json=payload, headers=headers, timeout=self._timeout)
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                return await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise LLMError("The AI model timed out. Please try again.") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not reach the AI model: {exc.__class__.__name__}") from exc


def _error_message(response: httpx.Response) -> str:
    try:
        return response.json()["error"]["message"]
    except (ValueError, KeyError, TypeError):
        return response.text[:200]


def _extract_text(data: dict) -> str:
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts)
    except (KeyError, IndexError, TypeError) as exc:
        reason = data.get("promptFeedback", {}).get("blockReason") if isinstance(data, dict) else None
        detail = f" (blocked: {reason})" if reason else ""
        raise LLMError(f"The AI model returned no content{detail}.") from exc
