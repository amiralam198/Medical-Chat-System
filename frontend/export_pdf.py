from io import BytesIO
from typing import Dict, Iterable, List

from fpdf import FPDF


def build_transcript_pdf(history: Iterable[Dict[str, object]]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 9, _safe_text("Reliable Medical Chat System for Doctors"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    _write_multicell(
        pdf,
        6,
        "Extractive answers only. PubMed citations are from retrieved metadata and abstracts.",
    )
    pdf.ln(2)

    for index, item in enumerate(history, start=1):
        question = str(item.get("question", ""))
        response = item.get("response", {}) or {}
        if not isinstance(response, dict):
            response = {}
        answer = str(response.get("answer", ""))
        confidence = str(response.get("confidence", ""))
        sources = response.get("sources", []) or []

        pdf.set_font("Helvetica", "B", 11)
        _write_multicell(pdf, 7, "Question %s" % index)
        pdf.set_font("Helvetica", "", 10)
        _write_multicell(pdf, 6, question)
        pdf.ln(1)

        pdf.set_font("Helvetica", "B", 11)
        _write_multicell(pdf, 7, "Answer")
        pdf.set_font("Helvetica", "", 10)
        _write_multicell(pdf, 6, answer)
        _write_multicell(pdf, 6, "Confidence: %s" % confidence)

        if sources:
            pdf.set_font("Helvetica", "B", 10)
            _write_multicell(pdf, 6, "Sources")
            pdf.set_font("Helvetica", "", 9)
            for source in sources:
                if isinstance(source, dict):
                    citation = _format_source(source)
                    _write_multicell(pdf, 5, citation)
        pdf.ln(4)

    output = pdf.output(dest="S")
    if isinstance(output, bytearray):
        return bytes(output)
    if isinstance(output, bytes):
        return output
    return str(output).encode("latin-1", errors="replace")


def _format_source(source: Dict[str, object]) -> str:
    pieces: List[str] = []
    pmid = source.get("pmid")
    if pmid:
        pieces.append("PMID %s" % pmid)
    title = source.get("title")
    if title:
        pieces.append(str(title))
    journal = source.get("journal")
    year = source.get("year")
    if journal or year:
        pieces.append("%s %s" % (journal or "", year or ""))
    url = source.get("url")
    if url:
        pieces.append(str(url))
    return " | ".join(piece.strip() for piece in pieces if piece)


def _safe_text(value: str) -> str:
    return value.encode("latin-1", errors="replace").decode("latin-1")


def _write_multicell(pdf: FPDF, height: float, text: str) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, height, _safe_text(text))
