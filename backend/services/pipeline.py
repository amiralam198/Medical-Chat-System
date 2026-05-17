import logging
from typing import Optional

from agents.citation_agent import package_sources
from agents.confidence import estimate_confidence
from agents.evidence_ranking import merge_pdf_hits, rank_pdf_chunks, rank_pubmed_records
from agents.extractive_answer import build_extractive_answer
from agents.query_understanding import build_query_intent
from agents.schemas import ChatResponseModel
from agents.source_verification import IDK_PHRASE
from agents.trusted_retrieval import retrieve_pubmed
from pdf_pipeline.chunk import chunk_pdf_text
from pdf_pipeline.extract import PDFExtractionError, extract_pdf_text


LOGGER = logging.getLogger(__name__)


async def run_chat_pipeline(
    message: str,
    session_id: Optional[str],
    recency_years: Optional[int],
    pdf_bytes: Optional[bytes],
    pdf_filename: Optional[str],
    embeddings: Optional[object],
    settings: object,
) -> ChatResponseModel:
    clean_message = " ".join((message or "").split())
    query_intent = build_query_intent(clean_message)
    if "broad_condition" in query_intent.intents:
        return ChatResponseModel(
            answer=IDK_PHRASE,
            confidence="Low",
            sources=[],
            pubmed_query=query_intent.expanded_search_query,
            retrieval_note="The question is too broad; specify the disease subtype, stage, or clinical setting.",
            query_intent=query_intent,
            evidence_context_ids=[],
        )

    effective_recency_years = recency_years
    latest_note = ""
    if "latest_treatment" in query_intent.intents and effective_recency_years is None:
        effective_recency_years = 5
        latest_note = "Latest-treatment query used a 5-year recency filter."

    pubmed_records, pubmed_query, retrieval_note = await retrieve_pubmed(
        query_intent=query_intent,
        settings=settings,
        recency_years=effective_recency_years,
    )

    pdf_chunks = []
    pdf_note = ""
    if pdf_bytes:
        try:
            pdf_text = extract_pdf_text(pdf_bytes)
            pdf_chunks = chunk_pdf_text(pdf_text, source_name=pdf_filename or "Uploaded PDF")
            if not pdf_chunks:
                pdf_note = "Uploaded PDF had no extractable text."
        except PDFExtractionError as exc:
            LOGGER.warning("PDF extraction failed: %s", exc)
            pdf_note = str(exc)

    ranking_query = query_intent.expanded_search_query
    pubmed_ranked = rank_pubmed_records(pubmed_records, ranking_query, embeddings=embeddings)
    pdf_ranked = rank_pdf_chunks(pdf_chunks, ranking_query, embeddings=embeddings)
    ranked_context = merge_pdf_hits(
        pubmed_ranked=pubmed_ranked,
        pdf_ranked=pdf_ranked,
        max_context_sources=settings.max_context_sources,
    )

    answer, used_ids = build_extractive_answer(
        ranked_context,
        query_intent.expanded_search_query,
    )
    confidence = estimate_confidence(answer, ranked_context, used_ids)
    sources = [] if answer == IDK_PHRASE else package_sources(ranked_context, used_ids)

    notes = [note for note in [latest_note, retrieval_note, pdf_note] if note]
    if embeddings is None:
        notes.append("Embeddings unavailable; lexical ranking was used.")

    return ChatResponseModel(
        answer=answer,
        confidence=confidence,
        sources=sources,
        pubmed_query=pubmed_query,
        retrieval_note=" ".join(notes),
        query_intent=query_intent,
        evidence_context_ids=used_ids,
    )
