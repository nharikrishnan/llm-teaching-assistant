"""Pydantic request/response models for all API endpoints."""

from __future__ import annotations

from pydantic import BaseModel


# --- Documents ---

class TopicOut(BaseModel):
    index: int
    title: str
    content: str


class UploadResponse(BaseModel):
    session_id: str
    topics: list[TopicOut]


class TopicsResponse(BaseModel):
    session_id: str
    topics: list[TopicOut]


# --- Teaching ---

class ExplainRequest(BaseModel):
    session_id: str
    topic_index: int


class ExplainResponse(BaseModel):
    explanation: str


class QuizRequest(BaseModel):
    session_id: str
    topic_index: int
    num_questions: int = 5


class QuizItemOut(BaseModel):
    question: str
    answer: str


class QuizResponse(BaseModel):
    questions: list[QuizItemOut]


class AnswerCheck(BaseModel):
    question: str
    correct_answer: str
    student_answer: str


class CheckRequest(BaseModel):
    answers: list[AnswerCheck]


class CheckResultOut(BaseModel):
    question: str
    correct: bool
    explanation: str


class CheckResponse(BaseModel):
    results: list[CheckResultOut]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: str
    topic_index: int
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


# --- Videos ---

class VideoGenerateRequest(BaseModel):
    session_id: str
    topic_index: int


class VideoGenerateResponse(BaseModel):
    job_id: str
    status: str


class VideoStatusResponse(BaseModel):
    job_id: str
    status: str  # "pending" | "processing" | "completed" | "failed"
    video_url: str | None = None
    error: str | None = None


# --- Search ---

class SearchRequest(BaseModel):
    topic_title: str
    topic_content: str = ""


class SourceLink(BaseModel):
    title: str
    url: str
    snippet: str = ""


class SearchResponse(BaseModel):
    summary: str
    sources: list[SourceLink]
