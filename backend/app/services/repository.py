"""Database access for analyses, kept out of the route handlers."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Analysis
from app.schemas import AnalysisResponse, AnalysisResult


def save_analysis(db: Session, resume_text: str, jd_text: str, result: AnalysisResult) -> Analysis:
    analysis = Analysis(
        role_title=result.role_title,
        match_score=result.match_score,
        resume_text=resume_text,
        jd_text=jd_text,
        result=result.model_dump(mode="json"),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def list_analyses(db: Session, limit: int = 50) -> list[Analysis]:
    stmt = select(Analysis).order_by(Analysis.created_at.desc(), Analysis.id.desc()).limit(limit)
    return list(db.scalars(stmt))


def get_analysis(db: Session, analysis_id: int) -> Analysis | None:
    return db.get(Analysis, analysis_id)


def to_response(analysis: Analysis) -> AnalysisResponse:
    return AnalysisResponse(id=analysis.id, created_at=analysis.created_at, **analysis.result)
