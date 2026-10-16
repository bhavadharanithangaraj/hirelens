import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analysis, history
from app.config import get_settings
from app.database import Base, engine
from app.llm import LLMError
from app.schemas import HealthResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("hirelens")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Small project: create tables on startup. A larger one would use Alembic migrations.
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="HireLens API", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(LLMError)
    async def llm_error_handler(_: Request, exc: LLMError) -> JSONResponse:
        # The upstream model failed, not the client: 502 Bad Gateway.
        logger.error("LLM failure: %s", exc)
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": str(exc)})

    @app.get("/api/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", llm_provider=settings.llm_provider)

    app.include_router(analysis.router)
    app.include_router(history.router)
    return app


app = create_app()
