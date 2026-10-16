"""FastAPI dependencies. Tests swap these out via app.dependency_overrides."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.llm import LLMClient, build_llm_client


def get_llm_client(settings: Annotated[Settings, Depends(get_settings)]) -> LLMClient:
    return build_llm_client(settings)


DbSession = Annotated[Session, Depends(get_db)]
LLM = Annotated[LLMClient, Depends(get_llm_client)]
