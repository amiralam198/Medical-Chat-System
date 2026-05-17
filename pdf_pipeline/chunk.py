from typing import Dict, List


def chunk_pdf_text(text: str, source_name: str = "Uploaded PDF") -> List[Dict[str, str]]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=180,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        texts = splitter.split_text(cleaned)
    except Exception:
        texts = _fallback_chunks(cleaned, chunk_size=1200, overlap=180)

    return [
        {
            "chunk_id": "%s-%03d" % (source_name.replace(" ", "_"), index + 1),
            "source_name": source_name,
            "text": chunk,
        }
        for index, chunk in enumerate(texts)
        if chunk.strip()
    ]


def _fallback_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(text_length, start + chunk_size)
        chunks.append(text[start:end])
        if end == text_length:
            break
        start = max(end - overlap, start + 1)
    return chunks
