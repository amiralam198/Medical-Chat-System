# Reliable Medical Chat System for Doctors

Local, production-style medical evidence app for doctors. The backend retrieves trusted PubMed abstracts from an allowlisted journal set, optionally ranks uploaded PDF chunks, and returns short extractive answers with mandatory citations.

The answer path uses no generative LLM APIs. There are no OpenAI, Gemini, Anthropic, or cloud model keys. Sentence-transformers are used only for ranking when available; if local embeddings fail, the API falls back to lexical ranking and still serves chat.

## Trusted Evidence Policy

- PubMed via NCBI E-utilities only: `esearch` plus `efetch`.
- Journal allowlist: BMJ, Br Med J, Lancet, Nature, JAMA, JAMA Intern Med, N Engl J Med, Ann Intern Med, Diabetes Care, Diabetologia, Circulation, J Am Heart Assoc, Eur Heart J, Circ Res, Stroke.
- PubMed query scope: `({user_query}) AND (PUBMED_JOURNAL_QUERY)` with optional recency filter.
- Post-fetch journal verification checks `Journal/ISOAbbreviation` against the allowlist.
- Publisher full text is never scraped. Paywalled content is not accessed.
- Uploaded PDFs are labeled as user-provided and are not treated as peer-reviewed by default.

## Requirements

Python 3.9+ is supported. The first embedding load may download `all-MiniLM-L6-v2` into the project-local `.hf_cache` directory.

```bash
cd medical-chat-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `NCBI_EMAIL` in `.env` before using PubMed. NCBI asks API clients to include a real email address.

## Run Locally

Terminal 1:

```bash
cd medical-chat-system
source .venv/bin/activate
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd medical-chat-system
source .venv/bin/activate
streamlit run frontend/app.py
```

Open the doctor UI at `http://localhost:8501`. Do not send doctors to port `8000`; that is the backend API.

Verify the backend:

```bash
curl http://127.0.0.1:8000/health
```

Expected shape:

```json
{
  "status": "ok",
  "api_version": "2.1.0",
  "embeddings_loaded": "yes",
  "chat_works_without_embeddings": "yes"
}
```

`embeddings_loaded` may be `"no"` on machines without local model dependencies. Chat still works through lexical ranking.

## Deploy on Vercel

The Vercel deployment serves the FastAPI app from `backend.main:app` through the root `app.py` shim and includes a browser UI at `/`. The Streamlit UI remains for local use.

Vercel installs the minimal runtime dependencies from `pyproject.toml`. The heavier local-only dependencies in `requirements.txt` are excluded from Vercel uploads by `.vercelignore`, and embeddings are disabled on Vercel so the API uses lexical ranking.

Set these environment variables in Vercel when available:

```bash
NCBI_EMAIL=you@example.com
DISABLE_EMBEDDINGS=1
```

Deploy from the project root:

```bash
npx vercel deploy
npx vercel deploy --prod
```

## Demo Queries

- `SGLT2 inhibitors heart failure`
- `atrial fibrillation anticoagulation`
- `stomach ache with sneezing` may correctly return `I don't know based on the retrieved evidence.` if no allowlisted-journal abstracts match.

## API

`GET /health`

`POST /api/v1/chat/json`

```json
{
  "message": "SGLT2 inhibitors heart failure",
  "session_id": "local-session",
  "recency_years": 2
}
```

`POST /api/v1/chat`

Multipart fields: `message`, `session_id`, optional `recency_years`, optional PDF `file`.

Response fields include `answer`, `confidence`, structured `sources`, `pubmed_query`, `retrieval_note`, `query_intent`, and `evidence_context_ids`. PDF `chunk_text` is internal and is not returned.

## Implementation Notes

The pipeline is intentionally modular:

1. `agents/query_understanding.py`: heuristic query expansion and intent tags.
2. `agents/trusted_retrieval.py`: PubMed retrieval wrapper.
3. `agents/evidence_ranking.py`: embedding or lexical ranking plus PDF hit merge.
4. `agents/extractive_answer.py`: verbatim sentence selection and citation markers.
5. `agents/citation_agent.py`: public citation packaging.

The default no-evidence response is exactly:

```text
I don't know based on the retrieved evidence.
```
