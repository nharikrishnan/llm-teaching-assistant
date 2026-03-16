"""Teaching, quiz, answer checking, and chat router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..session_store import sessions
from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    CheckRequest,
    CheckResponse,
    CheckResultOut,
    ExplainRequest,
    ExplainResponse,
    QuizItemOut,
    QuizRequest,
    QuizResponse,
)
from ..services.teacher import (
    answer_question,
    check_answer,
    generate_qa,
    teach_topic,
)

router = APIRouter()


def _get_topic(session_id: str, topic_index: int) -> dict:
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    topics = session["topics"]
    if topic_index < 0 or topic_index >= len(topics):
        raise HTTPException(status_code=400, detail="Invalid topic index.")
    return topics[topic_index]


@router.post("/explain", response_model=ExplainResponse)
async def explain(req: ExplainRequest):
    topic = _get_topic(req.session_id, req.topic_index)
    explanation = teach_topic(topic["title"], topic["content"])
    return ExplainResponse(explanation=explanation)


@router.post("/quiz", response_model=QuizResponse)
async def quiz(req: QuizRequest):
    topic = _get_topic(req.session_id, req.topic_index)
    items = generate_qa(topic["title"], topic["content"], req.num_questions)
    return QuizResponse(
        questions=[QuizItemOut(question=q.question, answer=q.answer) for q in items]
    )


@router.post("/check", response_model=CheckResponse)
async def check(req: CheckRequest):
    results: list[CheckResultOut] = []
    for a in req.answers:
        result = check_answer(a.question, a.correct_answer, a.student_answer)
        results.append(
            CheckResultOut(
                question=a.question,
                correct=result.correct,
                explanation=result.explanation,
            )
        )
    return CheckResponse(results=results)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    topic = _get_topic(req.session_id, req.topic_index)
    history = [{"role": m.role, "content": m.content} for m in req.history]
    reply = answer_question(
        topic["title"], topic["content"], req.message, conversation_history=history
    )
    return ChatResponse(reply=reply)
