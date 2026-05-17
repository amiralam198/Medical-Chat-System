# Recording Demo

Record the Streamlit doctor UI:

```text
http://localhost:8501
```

Do not record the backend API port directly. Port `8000` is for FastAPI requests from the UI.

Suggested flow:

1. Start FastAPI on port `8000`.
2. Start Streamlit on port `8501`.
3. Open `http://localhost:8501`.
4. Ask `SGLT2 inhibitors heart failure`.
5. Show the short extractive answer, confidence badge, and PubMed source links.
6. Optionally upload a PDF and show the `[user PDF]` marker.

If port `8501` is already busy, Streamlit may choose `8502`. In that case, record the Streamlit URL shown in the terminal.
