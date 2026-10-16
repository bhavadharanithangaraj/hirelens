from fastapi import APIRouter, HTTPException, Query, status

from app.deps import DbSession
from app.schemas import AnalysisResponse, HistoryItem
from app.services import repository

router = APIRouter(prefix="/api/history", tags=["history"])


# Sync handlers: FastAPI runs them in a threadpool, which suits blocking SQLAlchemy calls.
@router.get("", response_model=list[HistoryItem])
def list_history(db: DbSession, limit: int = Query(50, ge=1, le=200)) -> list[HistoryItem]:
    return [HistoryItem.model_validate(a) for a in repository.list_analyses(db, limit)]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_history_item(analysis_id: int, db: DbSession) -> AnalysisResponse:
    analysis = repository.get_analysis(db, analysis_id)
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Analysis {analysis_id} not found.")
    return repository.to_response(analysis)
