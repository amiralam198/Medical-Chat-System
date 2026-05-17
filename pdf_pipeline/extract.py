import logging


LOGGER = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    pass


def extract_pdf_text(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        return ""
    try:
        import fitz
    except Exception as exc:
        raise PDFExtractionError("PyMuPDF is not available: %s" % exc)

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            page_text = [page.get_text("text") for page in document]
    except Exception as exc:
        LOGGER.exception("PDF extraction failed")
        raise PDFExtractionError("Could not extract text from PDF: %s" % exc)

    return "\n".join(text for text in page_text if text)
