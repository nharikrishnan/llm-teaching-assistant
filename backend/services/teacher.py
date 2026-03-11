"""Teach a topic, generate Q&A, check answers, and chat — all grounded in document content."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .llm_config import get_llm


@dataclass
class QuizItem:
    question: str
    answer: str


@dataclass
class CheckResult:
    correct: bool
    explanation: str


def teach_topic(topic_title: str, topic_content: str) -> str:
    if not topic_content or not topic_content.strip():
        return "No content available for this topic."

    system_prompt = (
        "You are a clear, patient teacher. Explain the given topic in a structured way:\n"
        "- Use short paragraphs and bullet points where helpful.\n"
        "- Do not add information that is not in the provided text.\n"
        "- Be didactic and easy to follow."
    )
    user_prompt = (
        f"Topic: {topic_title}\n\nContent from the document:\n\n{topic_content}\n\n"
        "Explain this topic clearly and structurally, using only the content above."
    )

    llm = get_llm()
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def generate_qa(topic_title: str, topic_content: str, num_questions: int = 5) -> list[QuizItem]:
    if not topic_content or not topic_content.strip():
        return []

    system_prompt = (
        "You generate short quiz questions from document content.\n"
        "Return valid JSON only, no markdown or explanation.\n"
        'Format: [{"question": "...", "answer": "..."}, ...]\n'
        "Base questions and answers strictly on the provided text. Keep answers concise."
    )
    user_prompt = (
        f"Topic: {topic_title}\n\nContent:\n\n{topic_content[:30000]}\n\n"
        f"Generate {num_questions} quiz questions with correct answers. Return the JSON array only."
    )

    llm = get_llm()
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)
    return _parse_qa_response(content)


def check_answer(question: str, correct_answer: str, student_answer: str) -> CheckResult:
    """Use LLM to evaluate a student's answer with partial credit and explanations."""
    if not student_answer or not student_answer.strip():
        return CheckResult(correct=False, explanation="No answer provided.")

    system_prompt = (
        "You are a fair, encouraging teacher grading a student's quiz answer.\n"
        "Compare the student's answer to the correct answer.\n"
        "Accept answers that are conceptually correct even if worded differently.\n"
        'Return valid JSON only: {"correct": true/false, "explanation": "brief reason"}'
    )
    user_prompt = (
        f"Question: {question}\n"
        f"Correct answer: {correct_answer}\n"
        f"Student's answer: {student_answer}\n\n"
        "Evaluate and return JSON."
    )

    llm = get_llm()
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        data = json.loads(content)
        return CheckResult(
            correct=bool(data.get("correct", False)),
            explanation=str(data.get("explanation", "")),
        )
    except (json.JSONDecodeError, AttributeError):
        return CheckResult(correct=False, explanation="Could not evaluate the answer.")


def answer_question(
    topic_title: str,
    topic_content: str,
    user_question: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    if not topic_content or not topic_content.strip():
        return "There is no content for this topic to base an answer on."

    context = f"Topic: {topic_title}\n\nDocument section:\n\n{topic_content[:25000]}"

    system_prompt = (
        "You are a patient, clear teacher. The student can ask questions or express doubts about the material.\n"
        "Answer based only on the provided document section below. Use the same tone and structure as in the material.\n"
        "If the question is outside or beyond the given content, say so politely and suggest they re-read the section "
        "or ask a more specific question.\n"
        "Keep answers concise but complete. For follow-up questions, use the conversation history and the document section.\n\n"
        f"Document section to use for your answers:\n{context}"
    )

    messages: list = [SystemMessage(content=system_prompt)]
    for turn in conversation_history or []:
        role = (turn.get("role") or "").lower()
        content = turn.get("content") or ""
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_question))

    llm = get_llm()
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def _parse_qa_response(content: str) -> list[QuizItem]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    items: list[QuizItem] = []
    for entry in data:
        if isinstance(entry, dict):
            q = entry.get("question") or entry.get("q")
            a = entry.get("answer") or entry.get("a")
            if isinstance(q, str) and isinstance(a, str) and q.strip():
                items.append(QuizItem(question=q.strip(), answer=a.strip()))
    return items
