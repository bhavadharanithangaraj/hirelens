from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator[datetime]):
    """SQLite drops tzinfo on read; re-attach UTC so the API always returns aware timestamps."""

    impl = DateTime
    cache_ok = True

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Analysis(Base):
    """One saved resume-vs-JD analysis.

    role_title and match_score are real columns so the history list can be queried
    cheaply; the full structured LLM output lives in a JSON column.
    """

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, index=True)
    role_title: Mapped[str] = mapped_column(String(200))
    match_score: Mapped[int] = mapped_column(Integer)
    resume_text: Mapped[str] = mapped_column(Text)
    jd_text: Mapped[str] = mapped_column(Text)
    result: Mapped[dict[str, Any]] = mapped_column(JSON)
