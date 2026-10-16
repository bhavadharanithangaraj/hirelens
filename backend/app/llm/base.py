import logging
import re
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class LLMError(Exception):
    """Raised when the model can't be reached or keeps returning unusable output."""


class LLMClient(Protocol):
    """Anything that turns a prompt into raw text. Gemini and the mock both satisfy this."""

    async def generate(self, prompt: str) -> str: ...


def _strip_code_fences(text: str) -> str:
    # Even in JSON mode, models occasionally wrap output in ```json fences.
    return _CODE_FENCE.sub("", text.strip())


async def complete_json(client: LLMClient, prompt: str, model: type[T], max_retries: int = 1) -> T:
    """Ask the LLM for JSON and validate it against a Pydantic model.

    On invalid output the prompt is re-sent once with the validation error appended,
    which usually lets the model correct itself. If it still fails, raise LLMError.
    """
    attempt_prompt = prompt
    last_error = ""

    for attempt in range(max_retries + 1):
        raw = await client.generate(attempt_prompt)
        try:
            return model.model_validate_json(_strip_code_fences(raw))
        except ValidationError as exc:
            last_error = str(exc)
            logger.warning("Invalid LLM JSON for %s (attempt %d): %s", model.__name__, attempt + 1, last_error)
            attempt_prompt = (
                f"{prompt}\n\n"
                "Your previous reply was not valid JSON for the required schema. "
                f"Validation errors:\n{last_error}\n"
                "Reply again with ONLY the corrected JSON object."
            )

    raise LLMError(f"The AI model returned an invalid response for {model.__name__} after {max_retries + 1} attempts.")
