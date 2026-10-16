from app.config import Settings
from app.llm.base import LLMClient, LLMError, complete_json
from app.llm.gemini import GeminiClient
from app.llm.mock import MockClient

__all__ = ["LLMClient", "LLMError", "complete_json", "GeminiClient", "MockClient", "build_llm_client"]


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "gemini":
        return GeminiClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            timeout=settings.llm_timeout_seconds,
            fallback_models=[m.strip() for m in settings.gemini_fallback_models.split(",")],
        )
    return MockClient()
