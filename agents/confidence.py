from typing import Iterable, List

from agents.schemas import RankedSource
from agents.source_verification import IDK_PHRASE


def estimate_confidence(
    answer: str,
    ranked_context: Iterable[RankedSource],
    used_ids: List[str],
) -> str:
    if answer == IDK_PHRASE or not used_ids:
        return "Low"

    used_set = set(used_ids)
    used_sources = [source for source in ranked_context if source.source_id in used_set]
    if not used_sources:
        return "Low"

    best_score = max(source.combined_score for source in used_sources)
    pubmed_with_abstract = [
        source
        for source in used_sources
        if source.source_kind == "PubMed" and bool(source.abstract.strip())
    ]

    if best_score >= 0.62 and len(pubmed_with_abstract) >= 2:
        return "High"
    if best_score >= 0.38 and len(pubmed_with_abstract) >= 1:
        return "Medium"
    return "Low"
