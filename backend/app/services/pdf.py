from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PDFExtractionError(Exception):
    pass


def extract_pdf_text(data: bytes) -> tuple[str, int]:
    """Return (text, page_count). Raises PDFExtractionError for unreadable or image-only PDFs."""
    try:
        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except (PdfReadError, ValueError, KeyError) as exc:
        raise PDFExtractionError("The file could not be read as a PDF.") from exc

    # Normalise whitespace per line but keep line breaks - bullets depend on them.
    lines = (" ".join(line.split()) for page in pages for line in page.splitlines())
    text = "\n".join(line for line in lines if line)
    if not text:
        raise PDFExtractionError("No text found in this PDF. It may be a scanned image.")
    return text, len(pages)
