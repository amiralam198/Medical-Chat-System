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
    "do",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "latest",
    "new",
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

DRUG_EXPANSION_MAP: Dict[str, List[str]] = {
    "metformin": [
        "clinical use",
        "mechanisms of action",
        "type 2 diabetes",
        "glucose lowering",
        "glycemic control",
        "hepatic glucose production",
        "insulin sensitivity",
        "biguanide",
    ],
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
    "rabies": [
        "rabies post-exposure prophylaxis",
        "rabies vaccine",
        "rabies immunoglobulin",
        "human rabies immune globulin",
    ],
    "cancer": ["neoplasm", "malignancy", "oncology"],
}

INTENT_PATTERNS = {
    "therapy": {"treat", "treatment", "therapy", "drug", "dose", "management", "prevent"},
    "diagnosis": {"diagnose", "diagnosis", "test", "screening", "criteria"},
    "safety": {"safe", "safety", "risk", "adverse", "bleeding", "contraindication"},
    "prognosis": {"prognosis", "mortality", "survival", "outcome", "recurrence"},
    "evidence": {"trial", "meta", "review", "guideline", "evidence"},
    "latest_treatment": {"latest", "new", "recent", "newest"},
    "drug_purpose": {"do", "does", "work", "works", "mechanism", "use", "used", "purpose"},
}

THERAPY_QUERY_TERMS = [
    "treatment",
    "therapy",
    "management",
    "guideline",
    "practice guideline",
    "clinical trial",
    "randomized trial",
    "systematic review",
    "review",
]

DRUG_PURPOSE_QUERY_TERMS = [
    "clinical use",
    "mechanisms of action",
    "mechanism",
    "pharmacology",
    "review",
    "glucose lowering",
    "glycemic control",
    "hepatic glucose production",
    "insulin sensitivity",
    "biguanide",
]

CANCER_SUBTYPE_TERMS = {
    "breast",
    "lung",
    "colorectal",
    "colon",
    "rectal",
    "prostate",
    "pancreatic",
    "ovarian",
    "cervical",
    "endometrial",
    "gastric",
    "stomach",
    "liver",
    "hepatocellular",
    "renal",
    "kidney",
    "bladder",
    "melanoma",
    "leukemia",
    "lymphoma",
    "myeloma",
    "glioblastoma",
    "thyroid",
    "head",
    "neck",
    "esophageal",
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
    token_set = set(re.findall(r"[a-z0-9]+", lower_message))

    is_therapy_query = bool(token_set.intersection(INTENT_PATTERNS["therapy"]))
    is_latest_query = bool(token_set.intersection(INTENT_PATTERNS["latest_treatment"]))
    is_drug_purpose_query = bool(token_set.intersection(INTENT_PATTERNS["drug_purpose"]))

    concept_groups = []
    for trigger, terms in DRUG_EXPANSION_MAP.items():
        if trigger in lower_message:
            trigger_term = "%s[Title]" % trigger if is_drug_purpose_query else _quote_if_phrase(trigger)
            quoted_terms = [_quote_if_phrase(term) for term in terms if term]
            concept_groups.append("(%s AND (%s))" % (trigger_term, " OR ".join(quoted_terms)))

    for trigger, terms in EXPANSION_MAP.items():
        if trigger in lower_message:
            grouped_terms = [trigger] + terms
            quoted_group = [_quote_if_phrase(term) for term in grouped_terms if term]
            concept_groups.append("(" + " OR ".join(quoted_group) + ")")

    if is_therapy_query or is_latest_query:
        concept_groups.append(
            "(" + " OR ".join(_quote_if_phrase(term) for term in THERAPY_QUERY_TERMS) + ")"
        )
    if is_drug_purpose_query:
        concept_groups.append(
            "(" + " OR ".join(_quote_if_phrase(term) for term in DRUG_PURPOSE_QUERY_TERMS) + ")"
        )

    base_query = " ".join(keywords) if is_drug_purpose_query and keywords else clean_message.replace('"', "")
    if concept_groups:
        concept_query = " AND ".join(concept_groups)
        if is_drug_purpose_query:
            expanded_query = concept_query
        else:
            expanded_query = "(%s OR (%s))" % (base_query, concept_query)
    else:
        expanded_query = base_query

    intents = [
        name
        for name, pattern_tokens in INTENT_PATTERNS.items()
        if token_set.intersection(pattern_tokens)
    ]
    if "latest_treatment" in intents and "therapy" not in intents:
        intents.append("therapy")
    if "drug_purpose" in intents and "therapy" not in intents:
        intents.append("therapy")
    if _is_broad_cancer_question(token_set, lower_message):
        intents.append("broad_condition")
    if not intents:
        intents = ["clinical_research"]

    return QueryIntent(
        expanded_search_query=expanded_query,
        intents=intents,
        keywords=keywords[:12],
    )


def _is_broad_cancer_question(token_set: set, lower_message: str) -> bool:
    cancer_terms = {"cancer", "cancers", "neoplasm", "neoplasms", "malignancy", "malignancies"}
    if not token_set.intersection(cancer_terms):
        return False
    if token_set.intersection(CANCER_SUBTYPE_TERMS):
        return False
    return "all cancers" not in lower_message
