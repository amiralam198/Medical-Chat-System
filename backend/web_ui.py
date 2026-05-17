from fastapi.responses import HTMLResponse


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reliable Medical Chat</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f7fb;
      --panel: #ffffff;
      --panel-soft: #eef4fa;
      --ink: #172033;
      --muted: #526178;
      --line: #d6e0ec;
      --line-strong: #bdcad9;
      --accent: #146c94;
      --accent-dark: #0f5878;
      --ok: #23875b;
      --bad: #c33d32;
      --warn: #8a6200;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    .shell {
      display: grid;
      grid-template-columns: minmax(260px, 320px) 1fr;
      min-height: 100vh;
    }

    aside {
      background: #e8eef6;
      border-right: 1px solid var(--line);
      padding: 22px;
    }

    main {
      padding: 24px;
      max-width: 1220px;
      width: 100%;
      margin: 0 auto;
    }

    header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      padding-bottom: 18px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 20px;
    }

    h1 {
      margin: 0;
      font-size: clamp(28px, 3vw, 38px);
      line-height: 1.08;
      font-weight: 760;
      letter-spacing: 0;
    }

    h2 {
      margin: 0 0 10px;
      font-size: 15px;
      font-weight: 760;
      letter-spacing: 0;
    }

    p {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }

    .subtitle {
      margin-top: 8px;
      font-size: 15px;
    }

    .badges {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 7px;
      max-width: 300px;
    }

    .badge {
      border: 1px solid #c8d5e4;
      border-radius: 999px;
      background: #fff;
      color: #2d425c;
      padding: 5px 11px;
      font-size: 13px;
      font-weight: 720;
      white-space: nowrap;
    }

    .status-card,
    .control-card,
    .answer-card,
    .source-card,
    .empty-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 1px 2px rgba(25, 39, 64, 0.04);
    }

    .status-card,
    .control-card {
      padding: 14px;
      margin-bottom: 14px;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      padding: 5px 11px;
      font-size: 13px;
      font-weight: 760;
      border: 1px solid #d8e0ea;
      background: #f4f6f9;
      color: #526178;
    }

    .status-pill.online {
      background: #e0f4ea;
      color: #12613f;
      border-color: #b6e4cd;
    }

    .status-pill.offline {
      background: #fde8e5;
      color: #a43a31;
      border-color: #f4b8b0;
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: #8b98aa;
      flex: 0 0 auto;
    }

    .online .dot { background: var(--ok); }
    .offline .dot { background: var(--bad); }

    .meta {
      margin-top: 9px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }

    label {
      display: block;
      font-size: 13px;
      font-weight: 740;
      color: #1d2b40;
      margin: 0 0 7px;
    }

    input,
    select,
    textarea {
      width: 100%;
      border: 1px solid #cbd6e4;
      border-radius: 7px;
      background: #fbfcfe;
      color: var(--ink);
      font: inherit;
      font-size: 15px;
      padding: 10px 11px;
      outline: none;
    }

    textarea {
      min-height: 164px;
      resize: vertical;
      line-height: 1.45;
    }

    input:focus,
    select:focus,
    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(20, 108, 148, 0.12);
    }

    .field { margin-bottom: 14px; }

    .grid {
      display: grid;
      grid-template-columns: minmax(0, 0.58fr) minmax(320px, 0.42fr);
      gap: 22px;
      align-items: start;
    }

    form,
    .results {
      min-width: 0;
    }

    form {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 17px;
      box-shadow: 0 1px 2px rgba(25, 39, 64, 0.04);
    }

    button {
      appearance: none;
      border: 1px solid var(--accent);
      border-radius: 7px;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
      font: inherit;
      font-weight: 760;
      padding: 11px 14px;
      min-height: 44px;
      width: 100%;
    }

    button:hover { background: var(--accent-dark); border-color: var(--accent-dark); }
    button:disabled { cursor: wait; opacity: 0.72; }

    .secondary-button {
      background: #ffffff;
      color: #25425c;
      border-color: var(--line-strong);
      margin-top: 8px;
    }

    .secondary-button:hover {
      background: #f6f9fc;
      border-color: #9eb1c5;
    }

    .section-label {
      font-size: 14px;
      font-weight: 760;
      color: #1d2b40;
      margin: 0 0 9px;
    }

    .answer-card,
    .empty-card {
      padding: 16px;
      min-height: 170px;
    }

    .answer-text {
      white-space: pre-wrap;
      line-height: 1.55;
      overflow-wrap: anywhere;
    }

    .empty-card {
      display: flex;
      flex-direction: column;
      justify-content: center;
      border-style: dashed;
      color: var(--muted);
    }

    .empty-title {
      color: var(--ink);
      font-weight: 760;
      margin: 7px 0 3px;
    }

    .metric-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 12px 0 18px;
    }

    .metric {
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      border: 1px solid #d5dee9;
      border-radius: 7px;
      padding: 5px 9px;
      background: #fbfcfe;
      color: #334155;
      font-size: 13px;
      font-weight: 700;
    }

    .confidence-high { color: #075e45; background: #dff7ec; border-color: #a8e7cb; }
    .confidence-medium { color: #7a4b00; background: #fff3cf; border-color: #f2d68a; }
    .confidence-low { color: #8a1f1f; background: #fde7e7; border-color: #f2b8b8; }

    .source-card {
      padding: 14px;
      margin-bottom: 11px;
    }

    .source-title {
      color: #18263a;
      font-weight: 760;
      line-height: 1.35;
      margin-bottom: 6px;
      overflow-wrap: anywhere;
    }

    .source-meta {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }

    .source-card a {
      display: inline-block;
      margin-top: 6px;
      color: var(--accent);
      font-weight: 760;
      text-decoration: none;
    }

    .source-card a:hover { text-decoration: underline; }

    .note {
      margin-top: 12px;
      border: 1px solid #bfd2e7;
      border-left: 4px solid #2476a6;
      border-radius: 8px;
      background: #eef6fd;
      color: #1c4d72;
      padding: 12px 13px;
      line-height: 1.45;
      font-size: 14px;
      overflow-wrap: anywhere;
    }

    .note.warning {
      border-color: #efd28f;
      border-left-color: var(--warn);
      background: #fff7df;
      color: #674600;
    }

    .hidden { display: none !important; }

    @media (max-width: 920px) {
      .shell { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      main { padding: 18px; }
      header { flex-direction: column; }
      .badges { justify-content: flex-start; }
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="status-card">
        <div id="health-pill" class="status-pill"><span class="dot"></span><span>Checking backend</span></div>
        <div id="health-meta" class="meta">Health check pending.</div>
      </div>
      <div class="control-card">
        <div class="field">
          <label for="recency">Recency filter</label>
          <select id="recency">
            <option value="">None</option>
            <option value="2">2y</option>
            <option value="5">5y</option>
          </select>
        </div>
        <button id="reset" class="secondary-button" type="button">Reset session</button>
      </div>
    </aside>
    <main>
      <header>
        <div>
          <h1>Reliable Medical Chat System for Doctors</h1>
          <p class="subtitle">Evidence workspace for clinical and research questions</p>
        </div>
        <div class="badges" aria-label="Evidence channels">
          <span class="badge">PubMed</span>
          <span class="badge">PDF upload</span>
          <span class="badge">Cited excerpts</span>
        </div>
      </header>

      <div class="grid">
        <form id="chat-form">
          <div class="section-label">Doctor's question</div>
          <div class="field">
            <label for="question">Clinical or research question</label>
            <textarea id="question" name="question" placeholder="Example: SGLT2 inhibitors heart failure" required></textarea>
          </div>
          <div class="field">
            <label for="pdf">Optional PDF</label>
            <input id="pdf" name="pdf" type="file" accept="application/pdf">
          </div>
          <button id="submit" type="submit">Get answer</button>
          <div id="form-note" class="note warning hidden"></div>
        </form>

        <section class="results" aria-live="polite">
          <div class="section-label">Answer</div>
          <div id="empty" class="empty-card">
            <span class="dot"></span>
            <div class="empty-title">No answer yet</div>
            <p>Retrieved evidence, confidence, and citation links will appear here.</p>
          </div>
          <div id="answer" class="answer-card hidden">
            <div id="answer-text" class="answer-text"></div>
          </div>
          <div id="metrics" class="metric-strip hidden"></div>
          <div id="sources-label" class="section-label hidden">Sources</div>
          <div id="sources"></div>
          <div id="retrieval-note" class="note hidden"></div>
        </section>
      </div>
    </main>
  </div>

  <script>
    const state = {
      sessionId: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    };

    const form = document.getElementById("chat-form");
    const submitButton = document.getElementById("submit");
    const question = document.getElementById("question");
    const pdf = document.getElementById("pdf");
    const recency = document.getElementById("recency");
    const formNote = document.getElementById("form-note");
    const empty = document.getElementById("empty");
    const answer = document.getElementById("answer");
    const answerText = document.getElementById("answer-text");
    const metrics = document.getElementById("metrics");
    const sourcesLabel = document.getElementById("sources-label");
    const sources = document.getElementById("sources");
    const retrievalNote = document.getElementById("retrieval-note");
    const healthPill = document.getElementById("health-pill");
    const healthMeta = document.getElementById("health-meta");

    function setText(element, value) {
      element.textContent = value == null ? "" : String(value);
    }

    function setBusy(isBusy) {
      submitButton.disabled = isBusy;
      submitButton.textContent = isBusy ? "Retrieving evidence..." : "Get answer";
    }

    function showFormNote(message) {
      if (!message) {
        formNote.classList.add("hidden");
        setText(formNote, "");
        return;
      }
      setText(formNote, message);
      formNote.classList.remove("hidden");
    }

    function confidenceClass(value) {
      const normalized = String(value || "low").toLowerCase();
      if (normalized === "high") return "confidence-high";
      if (normalized === "medium") return "confidence-medium";
      return "confidence-low";
    }

    function metric(label, extraClass) {
      const item = document.createElement("span");
      item.className = "metric" + (extraClass ? " " + extraClass : "");
      setText(item, label);
      return item;
    }

    function renderResponse(payload) {
      empty.classList.add("hidden");
      answer.classList.remove("hidden");
      setText(answerText, payload.answer || "");

      const sourceItems = Array.isArray(payload.sources) ? payload.sources : [];
      const contextItems = Array.isArray(payload.evidence_context_ids) ? payload.evidence_context_ids : [];
      const confidence = payload.confidence || "Low";

      metrics.replaceChildren(
        metric(confidence + " confidence", confidenceClass(confidence)),
        metric(sourceItems.length + " cited source" + (sourceItems.length === 1 ? "" : "s")),
        metric(contextItems.length + " context item" + (contextItems.length === 1 ? "" : "s"))
      );
      metrics.classList.remove("hidden");

      sources.replaceChildren();
      sourcesLabel.classList.toggle("hidden", sourceItems.length === 0);
      sourceItems.forEach(renderSource);

      if (payload.retrieval_note) {
        setText(retrievalNote, payload.retrieval_note);
        retrievalNote.classList.remove("hidden");
      } else {
        retrievalNote.classList.add("hidden");
      }
    }

    function renderSource(source) {
      const card = document.createElement("article");
      card.className = "source-card";

      const title = document.createElement("div");
      title.className = "source-title";
      setText(title, source.title || "Untitled source");
      card.appendChild(title);

      const meta = document.createElement("div");
      meta.className = "source-meta";
      const pieces = [
        source.journal || "",
        source.year || "",
        source.evidence_label || "Research article",
        source.relevance_score ? "relevance " + source.relevance_score : "",
        source.pmid ? "PMID " + source.pmid : "",
      ].filter(Boolean);
      setText(meta, pieces.join(" | "));
      card.appendChild(meta);

      if (source.url) {
        const link = document.createElement("a");
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noopener";
        setText(link, "Open PubMed");
        card.appendChild(link);
      }

      sources.appendChild(card);
    }

    async function fetchWithTimeout(url, options, timeoutMs) {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), timeoutMs);
      try {
        return await fetch(url, { ...options, signal: controller.signal });
      } finally {
        clearTimeout(id);
      }
    }

    async function checkHealth() {
      try {
        const response = await fetchWithTimeout("/health", {}, 5000);
        if (!response.ok) throw new Error("HTTP " + response.status);
        const data = await response.json();
        healthPill.className = "status-pill online";
        healthPill.lastElementChild.textContent = "Backend online";
        const embeddingLabel = data.embeddings_loaded === "yes" ? "embedding ranking" : "lexical fallback";
        setText(healthMeta, "API " + (data.api_version || "unknown") + " | " + embeddingLabel);
      } catch (error) {
        healthPill.className = "status-pill offline";
        healthPill.lastElementChild.textContent = "Backend offline";
        setText(healthMeta, error.message || "Health check failed.");
      }
    }

    async function submitQuestion(event) {
      event.preventDefault();
      const cleanQuestion = question.value.trim();
      if (!cleanQuestion) {
        showFormNote("Enter a clinical or research question.");
        return;
      }

      showFormNote("");
      setBusy(true);

      try {
        let response;
        const recencyYears = recency.value ? Number(recency.value) : null;

        if (pdf.files && pdf.files[0]) {
          const data = new FormData();
          data.append("message", cleanQuestion);
          data.append("session_id", state.sessionId);
          if (recencyYears) data.append("recency_years", String(recencyYears));
          data.append("file", pdf.files[0]);
          response = await fetchWithTimeout("/api/v1/chat", { method: "POST", body: data }, 80000);
        } else {
          response = await fetchWithTimeout(
            "/api/v1/chat/json",
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                message: cleanQuestion,
                session_id: state.sessionId,
                recency_years: recencyYears,
              }),
            },
            80000
          );
        }

        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || "HTTP " + response.status);
        }

        renderResponse(await response.json());
      } catch (error) {
        const aborted = error && error.name === "AbortError";
        showFormNote(aborted ? "The request timed out. PubMed may be slow; retry with a narrower question." : "Request failed: " + (error.message || error));
      } finally {
        setBusy(false);
      }
    }

    document.getElementById("reset").addEventListener("click", () => {
      state.sessionId = crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
      question.value = "";
      pdf.value = "";
      showFormNote("");
      answer.classList.add("hidden");
      metrics.classList.add("hidden");
      sourcesLabel.classList.add("hidden");
      retrievalNote.classList.add("hidden");
      sources.replaceChildren();
      empty.classList.remove("hidden");
    });

    form.addEventListener("submit", submitQuestion);
    checkHealth();
  </script>
</body>
</html>
"""


def index_page() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML)
