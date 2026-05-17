import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.logging_config import configure_logging
from backend.routes.chat import router as chat_router
from backend.settings import get_settings
from vectorstore.embeddings import load_embeddings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / ".hf_cache"))
    app.state.embeddings = load_embeddings()
    app.state.embeddings_loaded = app.state.embeddings is not None
    yield


settings = get_settings()
app = FastAPI(
    title="Reliable Medical Chat System for Doctors",
    version=settings.api_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health() -> dict:
    loaded = getattr(app.state, "embeddings_loaded", False)
    return {
        "status": "ok",
        "api_version": settings.api_version,
        "embeddings_loaded": "yes" if loaded else "no",
        "chat_works_without_embeddings": "yes",
    }
