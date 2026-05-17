from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from agents.schemas import ChatJsonRequest, ChatResponseModel
from backend.services.pipeline import run_chat_pipeline
from backend.settings import get_settings


router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat/json", response_model=ChatResponseModel)
async def chat_json(payload: ChatJsonRequest, request: Request) -> ChatResponseModel:
    message = (payload.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    return await run_chat_pipeline(
        message=message,
        session_id=payload.session_id,
        recency_years=payload.recency_years,
        pdf_bytes=None,
        pdf_filename=None,
        embeddings=getattr(request.app.state, "embeddings", None),
        settings=get_settings(),
    )


@router.post("/chat", response_model=ChatResponseModel)
async def chat_multipart(
    request: Request,
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    recency_years: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
) -> ChatResponseModel:
    clean_message = (message or "").strip()
    if not clean_message:
        raise HTTPException(status_code=400, detail="message is required")

    pdf_bytes = None
    pdf_filename = None
    if file is not None:
        pdf_filename = file.filename or "Uploaded PDF"
        if not pdf_filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF uploads are supported")
        pdf_bytes = await file.read()

    return await run_chat_pipeline(
        message=clean_message,
        session_id=session_id,
        recency_years=recency_years,
        pdf_bytes=pdf_bytes,
        pdf_filename=pdf_filename,
        embeddings=getattr(request.app.state, "embeddings", None),
        settings=get_settings(),
    )
