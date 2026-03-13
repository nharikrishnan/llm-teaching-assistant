"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import documents, teaching, videos, search
from .session_store import sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    sessions.clear()


app = FastAPI(title="Teaching Assistant API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(teaching.router, prefix="/api/teaching", tags=["teaching"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(search.router, prefix="/api/search", tags=["search"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
