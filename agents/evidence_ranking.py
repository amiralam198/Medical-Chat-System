import datetime as dt
import logging
import re
from typing import Dict, Iterable, List, Optional, Sequence, Set

import numpy as np

from agents.evidence_types import evidence_label
from agents.schemas import PubMedRecord, RankedSource
from retrieval.trusted_journals import journal_tier_score


LOGGER = logging.getLogger(__name__)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


def rank_pubmed_records(
    records: Sequence[PubMedRecord],
    query: str,
    embeddings: Optional[object] = None,
) -> List[RankedSource]:
    texts = ["%s %s" % (record.title, record.abstract) for record in records]
    embedding_scores = _embedding_scores(query, texts, embeddings)
    ranked = []
    for index, record in enumerate(records):
        relevance = (
            embedding_scores[index]
            if embedding_scores is not None
            else jaccard_overlap(query, texts[index])
        )
        recency = recency_score(record.year)
        journal_score = journal_tier_score(record.journal)
        combined = 0.48 * relevance + 0.32 * recency + 0.20 * journal_score
        ranked.append(
            RankedSource(
                source_id="pmid:%s" % record.pmid,
                source_kind="PubMed",
                pmid=record.pmid,
                title=record.title,
                journal=record.journal,
                year=record.year,
                url=record.url,
                doi=record.doi,
                evidence_label=evidence_label(record.publication_types),
                relevance_score=round(float(relevance), 4),
                recency_score=round(float(recency), 4),
                journal_score=round(float(journal_score), 4),
                combined_score=round(float(combined), 4),
                abstract=record.abstract,
            )
        )
    return sorted(ranked, key=lambda item: item.combined_score, reverse=True)


def rank_pdf_chunks(
    chunks: List[Dict[str, str]],
    query: str,
    embeddings: Optional[object] = None,
    top_k: int = 3,
) -> List[RankedSource]:
    if not chunks:
        return []

    if embeddings is not None:
        try:
            from vectorstore.chroma_manager import rank_chunks_with_chroma

            chroma_hits = rank_chunks_with_chroma(chunks, query, embeddings, top_k=top_k)
            if chroma_hits:
                return [_pdf_ranked_source(hit) for hit in chroma_hits]
        except Exception as exc:
            LOGGER.warning("Chroma PDF ranking failed; using lexical ranking: %s", exc)

    return lexical_pdf_chunk_search(chunks, query, top_k=top_k)


def lexical_pdf_chunk_search(
    chunks: List[Dict[str, str]],
    query: str,
    top_k: int = 3,
) -> List[RankedSource]:
    scored = []
    for chunk in chunks:
        score = jaccard_overlap(query, chunk.get("text", ""))
        if score <= 0:
            continue
        scored.append(
            RankedSource(
                source_id="pdf:%s" % chunk["chunk_id"],
                source_kind="PDF",
                title=chunk.get("source_name", "Uploaded PDF"),
                journal="User-provided PDF",
                evidence_label="User-provided PDF",
                relevance_score=round(float(score), 4),
                recency_score=0.0,
                journal_score=0.0,
                combined_score=round(float(score), 4),
                chunk_text=chunk.get("text", ""),
            )
        )
    return sorted(scored, key=lambda item: item.combined_score, reverse=True)[:top_k]


def merge_pdf_hits(
    pubmed_ranked: List[RankedSource],
    pdf_ranked: List[RankedSource],
    max_context_sources: int = 6,
) -> List[RankedSource]:
    merged = list(pubmed_ranked) + list(pdf_ranked)
    merged.sort(key=lambda item: item.combined_score, reverse=True)
    return merged[:max_context_sources]


def recency_score(year: Optional[int]) -> float:
    if not year:
        return 0.0
    age_years = max(0, dt.datetime.now().year - int(year))
    return max(0.0, 1.0 - (float(age_years) / 18.0))


def jaccard_overlap(query: str, document: str) -> float:
    query_tokens = _token_set(query)
    document_tokens = _token_set(document)
    if not query_tokens or not document_tokens:
        return 0.0
    intersection = len(query_tokens.intersection(document_tokens))
    union = len(query_tokens.union(document_tokens))
    return float(intersection) / float(union) if union else 0.0


def _token_set(text: str) -> Set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if token not in STOPWORDS and len(token) > 1
    }


def _embedding_scores(
    query: str,
    documents: Sequence[str],
    embeddings: Optional[object],
) -> Optional[List[float]]:
    if embeddings is None or not documents:
        return None
    try:
        query_vector = np.asarray(embeddings.embed_query(query), dtype=float)
        doc_vectors = np.asarray(embeddings.embed_documents(list(documents)), dtype=float)
        query_norm = np.linalg.norm(query_vector)
        doc_norms = np.linalg.norm(doc_vectors, axis=1)
        denominator = np.maximum(doc_norms * query_norm, 1e-12)
        cosine = np.dot(doc_vectors, query_vector) / denominator
        return [float(max(0.0, min(1.0, value))) for value in cosine]
    except Exception as exc:
        LOGGER.warning("Embedding relevance failed; using lexical relevance: %s", exc)
        return None


def _pdf_ranked_source(hit: Dict[str, object]) -> RankedSource:
    score = float(hit.get("score", 0.0))
    return RankedSource(
        source_id="pdf:%s" % hit.get("chunk_id"),
        source_kind="PDF",
        title=str(hit.get("source_name") or "Uploaded PDF"),
        journal="User-provided PDF",
        evidence_label="User-provided PDF",
        relevance_score=round(score, 4),
        recency_score=0.0,
        journal_score=0.0,
        combined_score=round(score, 4),
        chunk_text=str(hit.get("text") or ""),
    )
