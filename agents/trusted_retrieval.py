from typing import List, Optional, Tuple

from agents.schemas import PubMedRecord, QueryIntent
from retrieval.pubmed import fetch_pubmed_records


async def retrieve_pubmed(
    query_intent: QueryIntent,
    settings: object,
    recency_years: Optional[int] = None,
) -> Tuple[List[PubMedRecord], str, str]:
    return await fetch_pubmed_records(
        user_query=query_intent.expanded_search_query,
        email=settings.ncbi_email,
        timeout_s=settings.pubmed_timeout_s,
        retmax=settings.pubmed_retmax,
        recency_years=recency_years,
    )
