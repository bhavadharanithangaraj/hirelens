from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db, make_engine
from app.deps import get_llm_client
from app.llm import LLMClient, MockClient
from app.main import app

RESUME = """Jane Doe - Full-Stack Developer
Experience
- Built a customer dashboard in React and TypeScript used by 20k monthly users
- Designed REST APIs with FastAPI and PostgreSQL, cutting response times by 40%
- Containerised services with Docker and set up CI/CD with GitHub Actions
- Prototyped an LLM-powered support bot using prompt engineering and the OpenAI API
Skills: Python, React, TypeScript, FastAPI, PostgreSQL, Docker, Git
"""

JD = """Senior React + Python Developer (Gen AI)
We are hiring a developer to build AI-powered products.
Requirements:
- Strong React and TypeScript
- Python with FastAPI
- Experience with LLMs and RAG pipelines
- AWS and Kubernetes
Nice to have:
- LangChain
- Vector databases
"""


@pytest.fixture
def db_session_factory(tmp_path) -> sessionmaker[Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def llm_client() -> LLMClient:
    return MockClient()


@pytest.fixture
def client(db_session_factory, llm_client) -> Iterator[TestClient]:
    def override_db() -> Iterator[Session]:
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_llm_client] = lambda: llm_client
    # Not used as a context manager, so the lifespan (which touches the real DB) never runs.
    yield TestClient(app)
    app.dependency_overrides.clear()
