import httpx

from app.llm.base import LLMError

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    """Minimal async client for the Gemini generateContent REST endpoint.

    Using httpx directly (instead of the SDK) keeps the dependency footprint small and
    makes the request/response shape explicit.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        timeout: float = 60.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._http_client = http_client

    async def generate(self, prompt: str) -> str:
        url = f"{GEMINI_BASE_URL}/models/{self._model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                # JSON mode: the model is constrained to emit a JSON document.
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }
        headers = {"x-goog-api-key": self._api_key}

        try:
            if self._http_client is not None:
                response = await self._http_client.post(url, json=payload, headers=headers, timeout=self._timeout)
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise LLMError("The AI model timed out. Please try again.") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not reach the AI model: {exc.__class__.__name__}") from exc

        if response.status_code != 200:
            raise LLMError(f"The AI model returned HTTP {response.status_code}: {_error_message(response)}")

        return _extract_text(response.json())


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
