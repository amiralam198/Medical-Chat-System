# Architecture

The system is a two-process local app: Streamlit for doctors and FastAPI for retrieval, ranking, and extractive answer construction.

```mermaid
flowchart LR
    Doctor[Doctor browser] --> UI[Streamlit UI :8501]
    UI --> API[FastAPI backend :8000]
    API --> QU[Query understanding module]
    QU --> TR[Trusted retrieval module]
    TR --> PM[PubMed E-utilities]
    PM --> TR
    API --> PDF[PDF extraction and chunking]
    PDF --> RANK[Evidence ranking]
    TR --> RANK
    RANK --> EMB[Local sentence-transformers ranking]
    EMB --> RANK
    RANK --> ANSWER[Extractive answer module]
    ANSWER --> CITE[Citation packaging]
    CITE --> API
    API --> UI
```

## Modules

- `backend/main.py`: FastAPI app, CORS, lifespan startup, local embedding load, `/health`.
- `backend/routes/chat.py`: JSON and multipart chat endpoints.
- `backend/services/pipeline.py`: orchestration across the evidence modules.
- `retrieval/pubmed.py`: async NCBI `esearch` and `efetch`, XML parsing, abstract-only PubMed data.
- `retrieval/trusted_journals.py`: journal query, ISO allowlist, journal tier scores.
- `agents/query_understanding.py`: heuristic query expansion and intent tagging, no LLM.
- `agents/evidence_ranking.py`: local embedding cosine similarity or lexical Jaccard fallback.
- `agents/extractive_answer.py`: verbatim abstract/PDF snippets with citation markers.
- `agents/citation_agent.py`: public `sources[]` response objects.
- `pdf_pipeline/`: PyMuPDF text extraction and chunking.
- `vectorstore/`: optional local embeddings and per-request Chroma helper.

## Startup Behavior

`backend/main.py` sets `HF_HOME` to `./.hf_cache` before loading embeddings. If the embedding model or dependencies fail, `app.state.embeddings` is `None` and ranking falls back to lexical overlap. The API stays available.
