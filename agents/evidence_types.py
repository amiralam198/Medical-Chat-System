from typing import Iterable


PUBLICATION_TYPE_LABELS = [
    ("Randomized Controlled Trial", "Randomized controlled trial"),
    ("Clinical Trial", "Clinical trial"),
    ("Meta-Analysis", "Meta-analysis"),
    ("Systematic Review", "Systematic review"),
    ("Review", "Review"),
    ("Practice Guideline", "Practice guideline"),
    ("Guideline", "Guideline"),
    ("Observational Study", "Observational study"),
    ("Comparative Study", "Comparative study"),
]


def evidence_label(publication_types: Iterable[str]) -> str:
    normalized = {item.strip().lower() for item in publication_types if item}
    for pubmed_name, label in PUBLICATION_TYPE_LABELS:
        if pubmed_name.lower() in normalized:
            return label
    if normalized:
        return "Research article"
    return "Research article"
