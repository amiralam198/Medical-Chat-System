import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional


LOGGER = logging.getLogger(__name__)
MODEL_IDS = (
    "sentence-transformers/all-MiniLM-L6-v2",
    "all-MiniLM-L6-v2",
)


@lru_cache(maxsize=1)
def load_embeddings() -> Optional[object]:
    project_root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("HF_HOME", str(project_root / ".hf_cache"))

    if os.getenv("DISABLE_EMBEDDINGS", "").lower() in {"1", "true", "yes"}:
        LOGGER.info("Embeddings disabled by DISABLE_EMBEDDINGS; lexical ranking will be used.")
        return None

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except Exception as exc:
        LOGGER.warning("LangChain HuggingFaceEmbeddings import failed: %s", exc)
        return None

    last_error = None
    for model_id in MODEL_IDS:
        try:
            return HuggingFaceEmbeddings(
                model_name=model_id,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        except Exception as exc:
            last_error = exc
            LOGGER.warning("Embedding model %s failed to load: %s", model_id, exc)

    LOGGER.warning("Embeddings unavailable; lexical ranking will be used: %s", last_error)
    return None
