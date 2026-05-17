import tempfile
from typing import Dict, List


def rank_chunks_with_chroma(
    chunks: List[Dict[str, str]],
    query: str,
    embeddings: object,
    top_k: int = 3,
) -> List[Dict[str, object]]:
    from langchain_community.vectorstores import Chroma
    from langchain_core.documents import Document

    documents = [
        Document(
            page_content=chunk["text"],
            metadata={
                "chunk_id": chunk["chunk_id"],
                "source_name": chunk.get("source_name", "Uploaded PDF"),
            },
        )
        for chunk in chunks
        if chunk.get("text")
    ]
    if not documents:
        return []

    with tempfile.TemporaryDirectory(prefix="medical_chat_chroma_") as tmpdir:
        store = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=tmpdir,
        )
        scored_docs = store.similarity_search_with_score(query, k=min(top_k, len(documents)))

    hits = []
    for document, distance in scored_docs:
        similarity = max(0.0, min(1.0, 1.0 - float(distance)))
        hits.append(
            {
                "chunk_id": document.metadata.get("chunk_id"),
                "source_name": document.metadata.get("source_name", "Uploaded PDF"),
                "text": document.page_content,
                "score": similarity,
            }
        )
    return hits
