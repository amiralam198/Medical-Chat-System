import re
from typing import List, Sequence, Tuple

from agents.schemas import RankedSource
from agents.source_verification import IDK_PHRASE


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
TOKEN_RE = re.compile(r"[a-z0-9]+")
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
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def build_extractive_answer(
    ranked_context: Sequence[RankedSource],
    query: str,
    target_words: int = 50,
    max_words: int = 100,
) -> Tuple[str, List[str]]:
    answer_parts = []
    used_ids = []

    pubmed_candidates = []
    for source in ranked_context:
        if source.source_kind != "PubMed":
            continue
        evidence_text = source.abstract.strip() or source.title.strip()
        sentence, sentence_score = select_evidence_sentence_with_score(evidence_text, query)
        if sentence_score <= 0:
            continue
        pubmed_candidates.append((sentence_score, source.combined_score, source, sentence))

    pubmed_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    pubmed_count = 0
    for _, _, source, sentence in pubmed_candidates:
        if pubmed_count >= 2:
            break
        marker = "[pmid:%s]" % source.pmid
        fitted = fit_text_with_marker(sentence, marker, max_words - word_count(" ".join(answer_parts)))
        if fitted:
            answer_parts.append(fitted)
            used_ids.append(source.source_id)
            pubmed_count += 1
        if word_count(" ".join(answer_parts)) >= target_words:
            break

    if word_count(" ".join(answer_parts)) < target_words:
        for source in ranked_context:
            if source.source_kind != "PDF" or source.source_id in used_ids:
                continue
            excerpt = select_evidence_sentence(source.chunk_text or "", query)
            prefix = "From your uploaded PDF (verbatim):"
            marker = "[user PDF]"
            remaining = max_words - word_count(" ".join(answer_parts))
            fitted_excerpt = fit_text_with_marker("%s %s" % (prefix, excerpt), marker, remaining)
            if fitted_excerpt:
                answer_parts.append(fitted_excerpt)
                used_ids.append(source.source_id)
            break

    answer = " ".join(part for part in answer_parts if part).strip()
    if not answer:
        return IDK_PHRASE, []
    return answer, used_ids


def select_evidence_sentence(text: str, query: str) -> str:
    sentence, _ = select_evidence_sentence_with_score(text, query)
    return sentence


def select_evidence_sentence_with_score(text: str, query: str) -> Tuple[str, int]:
    sentences = split_sentences(text)
    if not sentences:
        return "", 0
    query_tokens = evidence_tokens(query)
    scored = []
    for position, sentence in enumerate(sentences):
        sentence_tokens = evidence_tokens(sentence)
        score = len(query_tokens.intersection(sentence_tokens))
        scored.append((score, -position, sentence))
    scored.sort(reverse=True)
    return scored[0][2], scored[0][0]


def split_sentences(text: str) -> List[str]:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return []
    chunks = SENTENCE_SPLIT_RE.split(cleaned)
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) >= 8]


def fit_text_with_marker(text: str, marker: str, remaining_words: int) -> str:
    cleaned = " ".join((text or "").split())
    if not cleaned or remaining_words <= word_count(marker):
        return ""

    marker_words = word_count(marker)
    text_words = cleaned.split()
    if len(text_words) + marker_words <= remaining_words:
        return "%s %s" % (cleaned, marker)

    allowed_text_words = remaining_words - marker_words
    if allowed_text_words < 8:
        return ""
    return "%s %s" % (" ".join(text_words[:allowed_text_words]), marker)


def word_count(text: str) -> int:
    return len([token for token in (text or "").split() if token.strip()])


def evidence_tokens(text: str) -> set:
    return {
        token
        for token in TOKEN_RE.findall((text or "").lower())
        if token not in STOPWORDS and len(token) > 1
    }
