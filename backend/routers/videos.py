"""Video generation and serving router."""

from __future__ import annotations

import threading
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..session_store import sessions
from ..models.schemas import (
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoStatusResponse,
)
from ..services.video_generator import VideoJob, generate_video_for_topic, video_jobs

router = APIRouter()


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(req: VideoGenerateRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    topics = session["topics"]
    if req.topic_index < 0 or req.topic_index >= len(topics):
        raise HTTPException(status_code=400, detail="Invalid topic index.")

    existing_key = f"{req.session_id}_{req.topic_index}"
    for jid, job in video_jobs.items():
        if job.session_id == req.session_id and job.topic_index == req.topic_index:
            if job.status in ("pending", "processing"):
                return VideoGenerateResponse(job_id=jid, status=job.status)
            if job.status == "completed":
                return VideoGenerateResponse(job_id=jid, status=job.status)

    job_id = str(uuid.uuid4())
    topic = topics[req.topic_index]
    job = VideoJob(
        job_id=job_id,
        session_id=req.session_id,
        topic_index=req.topic_index,
    )
    video_jobs[job_id] = job

    thread = threading.Thread(
        target=generate_video_for_topic,
        args=(job, topic["title"], topic["content"]),
        daemon=True,
    )
    thread.start()

    return VideoGenerateResponse(job_id=job_id, status="pending")


@router.get("/status/{job_id}", response_model=VideoStatusResponse)
async def video_status(job_id: str):
    job = video_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    video_url = None
    if job.status == "completed" and job.video_path:
        video_url = f"/api/videos/file/{job_id}"

    return VideoStatusResponse(
        job_id=job_id,
        status=job.status,
        video_url=video_url,
        error=job.error,
    )


@router.get("/file/{job_id}")
async def serve_video(job_id: str):
    job = video_jobs.get(job_id)
    if not job or job.status != "completed" or not job.video_path:
        raise HTTPException(status_code=404, detail="Video not found.")

    return FileResponse(
        job.video_path,
        media_type="video/mp4",
        filename=f"topic_{job.topic_index}_lesson.mp4",
    )
