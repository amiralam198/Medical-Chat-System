import re
from typing import List, Sequence, Tuple

from agents.schemas import RankedSource
from agents.source_verification import IDK_PHRASE


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
TOKEN_RE = re.compile(r"[a-z0-9]+")
SECTION_PREFIX_RE = re.compile(
    r"^(background|objective|objectives|importance|methods|results|conclusions?|findings|summary)[:\s-]+",
    re.IGNORECASE,
)
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
TREATMENT_QUERY_TERMS = {
    "biguanide",
    "diabetes",
    "treat",
    "treatment",
    "therapy",
    "therapies",
    "management",
    "drug",
    "dose",
    "prevent",
    "prevention",
    "prophylaxis",
    "vaccine",
    "immunoglobulin",
    "mechanism",
    "metformin",
    "guideline",
    "glucose",
    "glycemic",
    "glycaemic",
    "purpose",
    "trial",
    "use",
    "used",
}
DRUG_PURPOSE_QUERY_TERMS = {
    "biguanide",
    "glucose",
    "glycemic",
    "glycaemic",
    "hepatic",
    "insulin",
    "mechanism",
    "metformin",
    "pharmacology",
}
DIRECT_DRUG_PURPOSE_TERMS = {
    "antihyperglycemic",
    "antihyperglycaemic",
    "biguanide",
    "clinical",
    "first-line",
    "glucose",
    "glycemic",
    "glycaemic",
    "hepatic",
    "insulin",
    "lower",
    "lowering",
    "lowers",
    "mechanism",
    "pharmacology",
    "reduce",
    "reduced",
    "reduces",
    "sensitivity",
}
DRUG_PURPOSE_ACTION_PHRASES = (
    "antihyperglycemic",
    "anti-hyperglycemic",
    "biguanide",
    "clinical use",
    "diabetes mellitus",
    "first-line",
    "foundation therapy",
    "glucose-lowering",
    "glucose lowering",
    "glucose metabolism",
    "glycaemic control",
    "glycaemia",
    "glycemic control",
    "glycemia",
    "hepatic glucose production",
    "initial therapy",
    "mechanism of action",
    "mechanisms of action",
    "oral glucose",
    "reduce hepatic",
    "therapy for",
    "treatment for",
    "treatment in",
    "type 2 diabetes",
)
CASUAL_DRUG_MENTION_PATTERNS = (
    "add-on to metformin",
    "background metformin",
    "biobank",
    "controlled with metformin",
    "controlling for",
    "inadequately controlled with metformin",
    "metformin and/or",
    "metformin with or without",
    "participants",
    "prevalence",
    "received metformin",
    "taking metformin",
)
CLINICAL_ACTION_TERMS = {
    "administer",
    "antihyperglycemic",
    "antihyperglycaemic",
    "antibody",
    "antibodies",
    "biguanide",
    "chemotherapy",
    "clinical",
    "diabetes",
    "diabetic",
    "dose",
    "drug",
    "drugs",
    "glucose",
    "glycemic",
    "glycaemic",
    "hepatic",
    "immunoglobulin",
    "immune",
    "immunotherapy",
    "insulin",
    "lower",
    "lowering",
    "lowers",
    "management",
    "monoclonal",
    "postexposure",
    "preexposure",
    "prevention",
    "prophylaxis",
    "radiotherapy",
    "reduce",
    "reduced",
    "reduces",
    "recommended",
    "sensitivity",
    "surgery",
    "therapy",
    "treat",
    "treated",
    "treatment",
    "use",
    "used",
    "vaccine",
    "vaccination",
}
PREFERRED_EVIDENCE_LABELS = {
    "Practice guideline": 1.0,
    "Guideline": 0.95,
    "Systematic review": 0.9,
    "Meta-analysis": 0.88,
    "Randomized controlled trial": 0.84,
    "Clinical trial": 0.76,
    "Review": 0.72,
    "Research article": 0.25,
}
REQUIRED_CONDITION_TERMS = {
    "metformin": {"metformin"},
    "rabies": {"rabies"},
    "diabetes": {"diabetes", "glycemic"},
    "hypertension": {"hypertension", "blood", "pressure"},
}


def build_extractive_answer(
    ranked_context: Sequence[RankedSource],
    query: str,
    target_words: int = 50,
    max_words: int = 80,
) -> Tuple[str, List[str]]:
    answer_parts = []
    used_ids = []
    treatment_query = bool(evidence_tokens(query).intersection(TREATMENT_QUERY_TERMS))
    drug_purpose_query = bool(evidence_tokens(query).intersection(DRUG_PURPOSE_QUERY_TERMS))

    pubmed_candidates = []
    for source in ranked_context:
        if source.source_kind != "PubMed":
            continue
        evidence_text = source.abstract.strip() if drug_purpose_query else "%s. %s" % (
            source.title.strip(),
            source.abstract.strip(),
        )
        if not evidence_text:
            evidence_text = source.title.strip()
        sentence, sentence_score = select_evidence_sentence_with_score(evidence_text, query)
        if not is_usable_sentence(
            sentence,
            sentence_score,
            query,
            source,
            treatment_query,
            drug_purpose_query,
        ):
            continue
        evidence_score = _preferred_evidence_score(source.evidence_label, drug_purpose_query)
        pubmed_candidates.append(
            (
                evidence_score,
                sentence_score,
                source.combined_score,
                source,
                clean_candidate_sentence(sentence, source, treatment_query),
            )
        )

    pubmed_candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)

    pubmed_count = 0
    for _, _, _, source, sentence in pubmed_candidates:
        if pubmed_count >= 2:
            break
        marker = "[PMID:%s]" % source.pmid
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
        if sentence_tokens.intersection(CLINICAL_ACTION_TERMS):
            score += 1
        scored.append((score, -position, sentence))
    scored.sort(reverse=True)
    return scored[0][2], scored[0][0]


def split_sentences(text: str) -> List[str]:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return []
    chunks = SENTENCE_SPLIT_RE.split(cleaned)
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) >= 8]


def is_usable_sentence(
    sentence: str,
    sentence_score: int,
    query: str,
    source: RankedSource,
    treatment_query: bool,
    drug_purpose_query: bool = False,
) -> bool:
    if sentence_score < 2:
        return False
    source_text = "%s %s %s" % (source.title or "", source.abstract or "", source.evidence_label or "")
    source_tokens = evidence_tokens(source_text)
    query_tokens = evidence_tokens(query)
    required_tokens = required_condition_tokens(query)
    selected_context_tokens = evidence_tokens("%s %s" % (source.title or "", sentence or ""))
    if required_tokens and not selected_context_tokens.intersection(required_tokens):
        return False
    if len(query_tokens.intersection(source_tokens)) < 2:
        return False
    if drug_purpose_query and "metformin" in query_tokens:
        sentence_tokens = evidence_tokens(sentence)
        lowered_sentence = (sentence or "").lower()
        if "metformin" not in sentence_tokens:
            return False
        if any(pattern in lowered_sentence for pattern in CASUAL_DRUG_MENTION_PATTERNS):
            return False
        if not sentence_tokens.intersection(DIRECT_DRUG_PURPOSE_TERMS):
            return False
        if not any(phrase in lowered_sentence for phrase in DRUG_PURPOSE_ACTION_PHRASES):
            return False
    if treatment_query:
        sentence_tokens = evidence_tokens(sentence)
        title_tokens = evidence_tokens(source.title or "")
        if not sentence_tokens.intersection(CLINICAL_ACTION_TERMS) and not title_tokens.intersection(
            CLINICAL_ACTION_TERMS
        ):
            return False
    return True


def _preferred_evidence_score(label: str, drug_purpose_query: bool) -> float:
    if not drug_purpose_query:
        return PREFERRED_EVIDENCE_LABELS.get(label, 0.25)
    if label in {"Practice guideline", "Guideline"}:
        return 1.0
    if label in {"Review", "Systematic review", "Meta-analysis"}:
        return 0.95
    if label in {"Randomized controlled trial", "Clinical trial"}:
        return 0.62
    return PREFERRED_EVIDENCE_LABELS.get(label, 0.25)


def clean_sentence(sentence: str) -> str:
    cleaned = " ".join((sentence or "").split())
    cleaned = SECTION_PREFIX_RE.sub("", cleaned).strip()
    cleaned = re.sub(r"\.{2,}", ".", cleaned)
    return cleaned[:1].upper() + cleaned[1:] if cleaned else ""


def clean_candidate_sentence(sentence: str, source: RankedSource, treatment_query: bool) -> str:
    cleaned = clean_sentence(sentence)
    title = clean_sentence(source.title or "")
    if title and cleaned.rstrip(".") == title.rstrip(".") and ":" in cleaned:
        cleaned = cleaned.split(":", 1)[0].rstrip(".")
    if treatment_query and title and cleaned.rstrip(".") == title.split(":", 1)[0].rstrip("."):
        cleaned = "Latest retrieved treatment evidence: %s" % cleaned[:1].lower() + cleaned[1:]
    return cleaned


def required_condition_tokens(query: str) -> set:
    tokens = evidence_tokens(query)
    required = set()
    for trigger, condition_tokens in REQUIRED_CONDITION_TERMS.items():
        if trigger in tokens:
            required.update(condition_tokens)
    return required


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
