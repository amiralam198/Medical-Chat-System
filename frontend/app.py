import html
import os
import uuid
from typing import Dict, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

from export_pdf import build_transcript_pdf


load_dotenv()

DEFAULT_API_BASE = os.getenv("MEDICAL_CHAT_API", "http://127.0.0.1:8000")
REQUEST_TIMEOUT_S = 75
HEALTH_TIMEOUT_S = 2.5


st.set_page_config(
    page_title="Reliable Medical Chat",
    page_icon="+",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], .stDeployButton { display: none !important; }
    .stApp { background: #f5f7fb; color: #172033; }
    .block-container { padding-top: 2rem; padding-bottom: 2.4rem; max-width: 1260px; }
    section[data-testid="stSidebar"] { background: #e9eef5; border-right: 1px solid #d6dee9; }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #314056; }
    .hero {
        display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem;
        margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #dde4ee;
    }
    .hero-copy { max-width: 840px; min-width: 0; }
    .app-title {
        font-size: clamp(1.8rem, 2.05vw, 2.25rem); line-height: 1.08;
        font-weight: 760; letter-spacing: 0; color: #122033; margin: 0;
    }
    .app-subtitle { margin-top: 0.4rem; color: #526178; font-size: 0.98rem; }
    .hero-badges {
        display: flex; gap: 0.45rem; flex-wrap: wrap; justify-content: flex-end;
        max-width: 265px; padding-top: 0.18rem;
    }
    .quiet-badge {
        border: 1px solid #cad6e5; background: #ffffff; color: #2d425c;
        border-radius: 999px; padding: 0.28rem 0.7rem; font-size: 0.82rem; font-weight: 700;
    }
    .port-note {
        border: 1px solid #bfd2e7; border-left: 4px solid #2476a6; border-radius: 8px;
        background: #eef6fd; color: #1c4d72; padding: 0.86rem 1rem; margin: 0.2rem 0 1.35rem;
        font-size: 0.96rem;
    }
    .section-label {
        font-size: 0.88rem; font-weight: 760; color: #1d2b40;
        margin: 0.75rem 0 0.4rem; letter-spacing: 0;
    }
    .answer-panel {
        border: 1px solid #d7e0eb; border-radius: 8px; padding: 1rem 1.05rem;
        background: #ffffff; color: #172033; box-shadow: 0 1px 2px rgba(25, 39, 64, 0.04);
        line-height: 1.55;
    }
    .empty-state {
        min-height: 164px; border: 1px dashed #c9d4e2; border-radius: 8px;
        background: #ffffff; padding: 1rem 1.05rem; color: #526178;
        display: flex; flex-direction: column; justify-content: center;
    }
    .empty-title { color: #172033; font-weight: 760; font-size: 1.02rem; margin-bottom: 0.2rem; }
    .status-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.7rem; }
    .status-dot { width: 0.58rem; height: 0.58rem; border-radius: 999px; display: inline-block; }
    .status-dot-waiting { background: #8b98aa; }
    .status-dot-ok { background: #23875b; }
    .status-dot-bad { background: #c33d32; }
    .metric-strip { display: flex; gap: 0.55rem; flex-wrap: wrap; margin-top: 0.75rem; }
    .metric-chip {
        border: 1px solid #d5dee9; border-radius: 7px; padding: 0.42rem 0.6rem;
        background: #fbfcfe; color: #334155; font-size: 0.84rem; font-weight: 650;
    }
    .source-panel {
        border: 1px solid #dbe3ee; border-radius: 8px; padding: 0.85rem 0.95rem;
        background: #ffffff; margin-bottom: 0.65rem; box-shadow: 0 1px 2px rgba(25, 39, 64, 0.04);
    }
    .source-title { color: #18263a; line-height: 1.35; margin-bottom: 0.35rem; }
    .source-meta { color: #536176; font-size: 0.88rem; line-height: 1.45; }
    .source-link { margin-top: 0.35rem; font-size: 0.88rem; }
    .source-link a { color: #146c94; font-weight: 700; text-decoration: none; }
    .source-link a:hover { text-decoration: underline; }
    .status-pill {
        display: inline-flex; align-items: center; gap: 0.42rem; border-radius: 999px;
        padding: 0.24rem 0.62rem; font-size: 0.82rem; font-weight: 760; border: 1px solid transparent;
    }
    .status-online { background: #e0f4ea; color: #12613f; border-color: #b6e4cd; }
    .status-offline { background: #fde8e5; color: #a43a31; border-color: #f4b8b0; }
    .status-muted { background: #f4f6f9; color: #526178; border-color: #d8e0ea; }
    .sidebar-card {
        border: 1px solid #d3dce8; border-radius: 8px; padding: 0.75rem;
        background: #ffffff; margin: 0.2rem 0 0.9rem;
    }
    .confidence {
        display: inline-block; border-radius: 999px; padding: 0.18rem 0.62rem;
        font-size: 0.84rem; font-weight: 700; border: 1px solid transparent;
    }
    .confidence-high { color: #075e45; background: #dff7ec; border-color: #a8e7cb; }
    .confidence-medium { color: #7a4b00; background: #fff3cf; border-color: #f2d68a; }
    .confidence-low { color: #8a1f1f; background: #fde7e7; border-color: #f2b8b8; }
    .muted { color: #5b6472; font-size: 0.92rem; }
    div[data-testid="stForm"] {
        border: 1px solid #d7e0eb; border-radius: 8px; background: #ffffff;
        box-shadow: 0 1px 2px rgba(25, 39, 64, 0.04); padding: 1rem;
    }
    .stTextArea textarea, .stTextInput input {
        border-color: #cbd6e4 !important; background: #fbfcfe !important; color: #172033 !important;
    }
    .stSelectbox [data-baseweb="select"] > div {
        border-color: #cbd6e4; background: #ffffff;
    }
    .stButton button, .stDownloadButton button, .stFormSubmitButton button {
        border-radius: 7px; border-color: #bfcbd9; font-weight: 740;
    }
    .stFormSubmitButton button {
        background: #146c94; color: #ffffff; border-color: #146c94;
    }
    .stFormSubmitButton button:hover {
        background: #0f5878; color: #ffffff; border-color: #0f5878;
    }
    @media (min-width: 1180px) {
        .app-title { white-space: nowrap; }
    }
    @media (max-width: 900px) {
        .hero { align-items: flex-start; flex-direction: column; }
        .hero-badges { justify-content: flex-start; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_response" not in st.session_state:
        st.session_state.last_response = None


def confidence_class(confidence: str) -> str:
    normalized = (confidence or "Low").lower()
    if normalized == "high":
        return "confidence confidence-high"
    if normalized == "medium":
        return "confidence confidence-medium"
    return "confidence confidence-low"


@st.cache_data(ttl=5, show_spinner=False)
def backend_health(api_base: str) -> Dict[str, object]:
    try:
        response = requests.get("%s/health" % api_base.rstrip("/"), timeout=HEALTH_TIMEOUT_S)
        response.raise_for_status()
        payload = response.json()
        payload["reachable"] = True
        return payload
    except Exception as exc:
        return {"reachable": False, "error": str(exc)}


def render_backend_status(health: Dict[str, object]) -> None:
    if health.get("reachable"):
        embeddings = str(health.get("embeddings_loaded", "no"))
        embedding_label = "embedding ranking" if embeddings == "yes" else "lexical fallback"
        version = html.escape(str(health.get("api_version", "unknown")))
        st.markdown(
            """
            <div class="sidebar-card">
                <div class="status-pill status-online"><span class="status-dot status-dot-ok"></span>Backend online</div>
                <div class="source-meta" style="margin-top:0.55rem;">API %s · %s</div>
            </div>
            """
            % (version, html.escape(embedding_label)),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="sidebar-card">
                <div class="status-pill status-offline"><span class="status-dot status-dot-bad"></span>Backend offline</div>
                <div class="source-meta" style="margin-top:0.55rem;">Start FastAPI on port 8000.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_response(response: Dict[str, object]) -> None:
    answer = html.escape(str(response.get("answer", "")))
    confidence = html.escape(str(response.get("confidence", "Low")))
    context_ids = response.get("evidence_context_ids", []) or []
    sources = response.get("sources", []) or []
    st.markdown(
        '<div class="section-label">Answer</div><div class="answer-panel">%s</div>'
        % answer,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="metric-strip">
            <span class="%s">%s confidence</span>
            <span class="metric-chip">%s cited source%s</span>
            <span class="metric-chip">%s context item%s</span>
        </div>
        """
        % (
            confidence_class(confidence),
            confidence,
            len(sources),
            "" if len(sources) == 1 else "s",
            len(context_ids),
            "" if len(context_ids) == 1 else "s",
        ),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">Sources</div>', unsafe_allow_html=True)
    if not sources:
        st.caption("No cited sources were returned.")
    for source in sources:
        if isinstance(source, dict):
            render_source(source)

    retrieval_note = str(response.get("retrieval_note", "") or "")
    if retrieval_note:
        st.info(retrieval_note)


def render_source(source: Dict[str, object]) -> None:
    title = html.escape(str(source.get("title") or "Untitled source"))
    journal = html.escape(str(source.get("journal") or ""))
    year = html.escape(str(source.get("year") or ""))
    evidence_label = html.escape(str(source.get("evidence_label") or "Research article"))
    relevance = html.escape(str(source.get("relevance_score") or "0"))
    pmid = source.get("pmid")
    url = source.get("url")
    doi = source.get("doi")

    link_html = ""
    if url:
        safe_url = html.escape(str(url), quote=True)
        link_html = '<a href="%s" target="_blank" rel="noopener">Open PubMed</a>' % safe_url
    doi_html = ""
    if doi:
        doi_html = " · DOI %s" % html.escape(str(doi))
    pmid_html = " PMID: %s" % html.escape(str(pmid)) if pmid else ""

    st.markdown(
        """
        <div class="source-panel">
            <div class="source-title"><strong>%s</strong></div>
            <div class="source-meta">%s %s · %s · relevance %s%s</div>
            <div class="source-link">%s%s</div>
        </div>
        """
        % (title, journal, year, evidence_label, relevance, pmid_html, link_html, doi_html),
        unsafe_allow_html=True,
    )


def render_empty_answer() -> None:
    st.markdown('<div class="section-label">Answer</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="empty-state">
            <div class="status-row">
                <span class="status-dot status-dot-waiting"></span>
                <span class="muted">Waiting for a question</span>
            </div>
            <div class="empty-title">No answer yet</div>
            <div class="muted">Retrieved evidence, confidence, and citation links will appear here.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def call_api(
    api_base: str,
    message: str,
    session_id: str,
    recency_years: Optional[int],
    uploaded_pdf: object,
) -> Dict[str, object]:
    api_base = api_base.rstrip("/")
    if uploaded_pdf is not None:
        data = {"message": message, "session_id": session_id}
        if recency_years:
            data["recency_years"] = str(recency_years)
        files = {
            "file": (
                uploaded_pdf.name,
                uploaded_pdf.getvalue(),
                "application/pdf",
            )
        }
        response = requests.post(
            "%s/api/v1/chat" % api_base,
            data=data,
            files=files,
            timeout=REQUEST_TIMEOUT_S,
        )
    else:
        payload = {
            "message": message,
            "session_id": session_id,
            "recency_years": recency_years,
        }
        response = requests.post(
            "%s/api/v1/chat/json" % api_base,
            json=payload,
            timeout=REQUEST_TIMEOUT_S,
        )

    response.raise_for_status()
    return response.json()


def recency_value(label: str) -> Optional[int]:
    if label == "2y":
        return 2
    if label == "5y":
        return 5
    return None


init_state()

with st.sidebar:
    st.subheader("Local API")
    api_base = st.text_input("API base URL", value=DEFAULT_API_BASE)
    render_backend_status(backend_health(api_base))
    recency_label = st.selectbox("Recency filter", ["None", "2y", "5y"], index=0)

    if st.button("Reset session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.history = []
        st.session_state.last_response = None
        st.rerun()

    if st.session_state.history:
        try:
            pdf_bytes = build_transcript_pdf(st.session_state.history)
            st.download_button(
                "Export chat PDF",
                data=pdf_bytes,
                file_name="medical-chat-transcript.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.warning("Transcript export is unavailable: %s" % exc)

st.markdown(
    """
    <div class="hero">
        <div class="hero-copy">
            <h1 class="app-title">Reliable Medical Chat System for Doctors</h1>
            <div class="app-subtitle">Local evidence workspace for clinical and research questions</div>
        </div>
        <div class="hero-badges">
            <span class="quiet-badge">PubMed</span>
            <span class="quiet-badge">PDF upload</span>
            <span class="quiet-badge">Cited excerpts</span>
        </div>
    </div>
    <div class="port-note"><strong>8501</strong> doctor UI · <strong>8000</strong> backend API · do not open 8000 for doctors</div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([0.58, 0.42], gap="large")

with left:
    st.markdown('<div class="section-label">Doctor&apos;s question</div>', unsafe_allow_html=True)
    with st.form("doctor_question_form", clear_on_submit=False):
        question = st.text_area(
            "Clinical or research question",
            placeholder="Example: SGLT2 inhibitors heart failure",
            height=150,
        )
        uploaded_pdf = st.file_uploader("Optional PDF", type=["pdf"])
        submitted = st.form_submit_button("Get answer", use_container_width=True)

    if submitted:
        if not question.strip():
            st.warning("Enter a clinical or research question.")
        else:
            with st.spinner("Retrieving trusted evidence..."):
                try:
                    result = call_api(
                        api_base=api_base,
                        message=question.strip(),
                        session_id=st.session_state.session_id,
                        recency_years=recency_value(recency_label),
                        uploaded_pdf=uploaded_pdf,
                    )
                    st.session_state.last_response = result
                    st.session_state.history.append(
                        {"question": question.strip(), "response": result}
                    )
                except requests.exceptions.ConnectionError:
                    st.error(
                        "Cannot reach the backend at %s. Start it with: "
                        "`python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`"
                        % api_base
                    )
                except requests.exceptions.Timeout:
                    st.error("The backend request timed out. PubMed may be slow; retry or increase PUBMED_TIMEOUT_S.")
                except requests.HTTPError as exc:
                    detail = exc.response.text if exc.response is not None else str(exc)
                    st.error("Backend returned an error: %s" % detail)
                except Exception as exc:
                    st.error("Request failed: %s" % exc)

with right:
    if st.session_state.last_response:
        render_response(st.session_state.last_response)
    else:
        render_empty_answer()

if st.session_state.history:
    st.divider()
    st.markdown('<div class="section-label">Session transcript</div>', unsafe_allow_html=True)
    for item in reversed(st.session_state.history[-5:]):
        st.markdown("**Question:** %s" % html.escape(item["question"]))
        response = item.get("response", {})
        if isinstance(response, dict):
            st.caption("Confidence: %s" % response.get("confidence", "Low"))
            st.write(response.get("answer", ""))
