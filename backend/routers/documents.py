"""Document upload and topic extraction router."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..session_store import generate_session_id, sessions
from ..models.schemas import TopicOut, TopicsResponse, UploadResponse
from ..services.chunker import extract_topics
from ..services.doc_loader import load_pdf_as_text

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 50 MB.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        full_text = load_pdf_as_text(tmp_path)
        topics = extract_topics(full_text)

        session_id = generate_session_id()
        sessions[session_id] = {
            "full_text": full_text,
            "topics": [{"title": t.title, "content": t.content} for t in topics],
        }

        return UploadResponse(
            session_id=session_id,
            topics=[
                TopicOut(index=i, title=t.title, content=t.content)
                for i, t in enumerate(topics)
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


@router.get("/topics/{session_id}", response_model=TopicsResponse)
async def get_topics(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    topics = session["topics"]
    return TopicsResponse(
        session_id=session_id,
        topics=[
            TopicOut(index=i, title=t["title"], content=t["content"])
            for i, t in enumerate(topics)
        ],
    )
