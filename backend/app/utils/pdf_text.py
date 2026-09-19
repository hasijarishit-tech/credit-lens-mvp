"""Extracts text from a native-text PDF (not scanned/image-based — OCR is
explicitly out of scope for this MVP, see README roadmap)."""
from pypdf import PdfReader
from io import BytesIO


class PdfTextExtractionError(Exception):
    pass


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
        pages_text = [page.extract_text() or "" for page in reader.pages]
    except Exception as e:
        raise PdfTextExtractionError(f"Could not read this PDF: {e}") from e

    text = "\n".join(pages_text).strip()
    if len(text) < 50:
        raise PdfTextExtractionError(
            "This PDF doesn't contain readable text (it may be a scanned image). "
            "OCR isn't supported in this MVP — please try manual entry instead."
        )
    return text
