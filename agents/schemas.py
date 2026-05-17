from typing import List, Optional

from pydantic import BaseModel, Field


class QueryIntent(BaseModel):
    expanded_search_query: str
    intents: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class ChatJsonRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    recency_years: Optional[int] = None


class PubMedRecord(BaseModel):
    pmid: str
    title: str
    journal: str
    year: Optional[int] = None
    abstract: str = ""
    publication_types: List[str] = Field(default_factory=list)
    doi: Optional[str] = None
    url: str


class RankedSource(BaseModel):
    source_id: str
    source_kind: str
    pmid: Optional[str] = None
    title: str
    journal: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    evidence_label: str = "Research article"
    relevance_score: float = 0.0
    recency_score: float = 0.0
    journal_score: float = 0.0
    combined_score: float = 0.0
    abstract: str = ""
    chunk_text: Optional[str] = Field(default=None, exclude=True)


class CitationSource(BaseModel):
    pmid: Optional[str] = None
    title: str
    journal: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    evidence_label: str
    relevance_score: float
    source_type: str = "PubMed"


class ChatResponseModel(BaseModel):
    answer: str
    confidence: str
    sources: List[CitationSource] = Field(default_factory=list)
    pubmed_query: str
    retrieval_note: str = ""
    query_intent: QueryIntent
    evidence_context_ids: List[str] = Field(default_factory=list)
