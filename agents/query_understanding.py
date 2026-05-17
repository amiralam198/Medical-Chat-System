import re
from typing import Dict, List

from agents.schemas import QueryIntent


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
    "how",
    "in",
    "is",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "what",
    "when",
    "with",
}

EXPANSION_MAP: Dict[str, List[str]] = {
    "sglt2": ["sodium-glucose cotransporter 2", "empagliflozin", "dapagliflozin"],
    "heart failure": ["cardiac failure", "reduced ejection fraction", "preserved ejection fraction"],
    "atrial fibrillation": ["AF", "oral anticoagulation", "stroke prevention"],
    "anticoagulation": ["oral anticoagulants", "warfarin", "direct oral anticoagulants"],
    "hypertension": ["blood pressure"],
    "myocardial infarction": ["heart attack", "acute coronary syndrome"],
    "stroke": ["cerebrovascular accident"],
    "diabetes": ["type 2 diabetes", "glycemic"],
    "statin": ["HMG-CoA reductase inhibitor", "lipid lowering"],
}

INTENT_PATTERNS = {
    "therapy": {"treat", "treatment", "therapy", "drug", "dose", "management", "prevent"},
    "diagnosis": {"diagnose", "diagnosis", "test", "screening", "criteria"},
    "safety": {"safe", "safety", "risk", "adverse", "bleeding", "contraindication"},
    "prognosis": {"prognosis", "mortality", "survival", "outcome", "recurrence"},
    "evidence": {"trial", "meta", "review", "guideline", "evidence"},
}


def _tokens(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOPWORDS]


def _quote_if_phrase(term: str) -> str:
    cleaned = term.strip().replace('"', "")
    if not cleaned:
        return ""
    if " " in cleaned or "-" in cleaned:
        return '"%s"' % cleaned
    return cleaned


def build_query_intent(message: str) -> QueryIntent:
    clean_message = " ".join((message or "").split())
    lower_message = clean_message.lower()
    keywords = _tokens(clean_message)

    concept_groups = []
    for trigger, terms in EXPANSION_MAP.items():
        if trigger in lower_message:
            grouped_terms = [trigger] + terms
            quoted_group = [_quote_if_phrase(term) for term in grouped_terms if term]
            concept_groups.append("(" + " OR ".join(quoted_group) + ")")

    base_query = clean_message.replace('"', "")
    if concept_groups:
        concept_query = " AND ".join(concept_groups)
        expanded_query = "(%s OR (%s))" % (base_query, concept_query)
    else:
        expanded_query = base_query

    token_set = set(keywords)
    intents = [
        name
        for name, pattern_tokens in INTENT_PATTERNS.items()
        if token_set.intersection(pattern_tokens)
    ]
    if not intents:
        intents = ["clinical_research"]

    return QueryIntent(
        expanded_search_query=expanded_query,
        intents=intents,
        keywords=keywords[:12],
    )
