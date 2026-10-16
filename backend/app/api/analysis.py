from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.deps import LLM, DbSession
from app.schemas import AnalysisResponse, AnalyzeRequest, ExtractTextResponse
from app.services import repository
from app.services.pdf import PDFExtractionError, extract_pdf_text
from app.services.pipeline import run_analysis

router = APIRouter(prefix="/api", tags=["analysis"])

MAX_PDF_BYTES = 5 * 1024 * 1024


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze(payload: AnalyzeRequest, llm: LLM, db: DbSession) -> AnalysisResponse:
    """Run the 3-step pipeline and persist the result. LLMError is mapped to 502 in main.py."""
    result = await run_analysis(llm, payload.resume_text, payload.jd_text)
    saved = await run_in_threadpool(repository.save_analysis, db, payload.resume_text, payload.jd_text, result)
    return repository.to_response(saved)


@router.post("/extract-text", response_model=ExtractTextResponse)
async def extract_text(file: UploadFile) -> ExtractTextResponse:
    filename = file.filename or "upload.pdf"
    if file.content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Please upload a PDF file.")

    data = await file.read(MAX_PDF_BYTES + 1)
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "PDF must be 5 MB or smaller.")

    try:
        # PDF parsing is CPU-bound; keep it off the event loop.
        text, pages = await run_in_threadpool(extract_pdf_text, data)
    except PDFExtractionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    return ExtractTextResponse(filename=filename, pages=pages, text=text)
