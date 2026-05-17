from typing import Iterable, List, Set

from agents.schemas import CitationSource, RankedSource


def package_sources(ranked_context: Iterable[RankedSource], used_ids: Iterable[str]) -> List[CitationSource]:
    used_id_set = set(used_ids)
    seen: Set[str] = set()
    citations = []
    for source in ranked_context:
        if used_id_set and source.source_id not in used_id_set:
            continue
        dedupe_key = source.pmid or source.source_id
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        citations.append(
            CitationSource(
                pmid=source.pmid,
                title=source.title,
                journal=source.journal,
                year=source.year,
                url=source.url,
                doi=source.doi,
                evidence_label=source.evidence_label,
                relevance_score=round(float(source.relevance_score), 4),
                source_type=source.source_kind,
            )
        )
    return citations
