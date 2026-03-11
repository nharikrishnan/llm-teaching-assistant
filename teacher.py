"""Teach a topic and generate Q&A from document content using the LLM."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from llm_config import get_llm


@dataclass
class QuizItem:
    """A single quiz question and its correct answer."""

    question: str
    answer: str


def teach_topic(topic_title: str, topic_content: str) -> str:
    """
    Generate a clear, structured explanation of the topic using only the provided content.

    Args:
        topic_title: Title of the topic.
        topic_content: Raw document text for this topic.

    Returns:
        LLM-generated teaching text (structured explanation).
    """
    if not topic_content or not topic_content.strip():
        return "No content available for this topic."

    system_prompt = """You are a clear, patient teacher. Explain the given topic in a structured way:
- Use short paragraphs and bullet points where helpful.
- Do not add information that is not in the provided text.
- Be didactic and easy to follow."""

    user_prompt = f"""Topic: {topic_title}\n\nContent from the document:\n\n{topic_content}\n\nExplain this topic clearly and structurally, using only the content above."""

    llm = get_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def generate_qa(topic_title: str, topic_content: str, num_questions: int = 5) -> list[QuizItem]:
    """
    Generate quiz questions and answers based only on the given topic content.

    Args:
        topic_title: Title of the topic.
        topic_content: Raw document text for this topic.
        num_questions: Desired number of questions (default 5).

    Returns:
        List of QuizItem with question and answer.
    """
    if not topic_content or not topic_content.strip():
        return []

    system_prompt = """You generate short quiz questions from document content.
Return valid JSON only, no markdown or explanation.
Format: [{"question": "...", "answer": "..."}, ...]
Base questions and answers strictly on the provided text. Keep answers concise."""

    user_prompt = f"""Topic: {topic_title}\n\nContent:\n\n{topic_content[:30000]}\n\nGenerate {num_questions} quiz questions with correct answers. Return the JSON array only."""

    llm = get_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    return _parse_qa_response(content)


def answer_question(
    topic_title: str,
    topic_content: str,
    user_question: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """
    Answer a student's question about the topic, grounded in the document content.
    Supports multi-turn conversation via conversation_history.

    Args:
        topic_title: Title of the current topic.
        topic_content: Raw document text for this topic.
        user_question: The student's question.
        conversation_history: Optional list of {"role": "user"|"assistant", "content": "..."}.

    Returns:
        The teacher's answer (assistant message).
    """
    if not topic_content or not topic_content.strip():
        return "There is no content for this topic to base an answer on."

    context = f"Topic: {topic_title}\n\nDocument section:\n\n{topic_content[:25000]}"

    system_prompt = """You are a patient, clear teacher. The student can ask questions or express doubts about the material.
Answer based only on the provided document section below. Use the same tone and structure as in the material.
If the question is outside or beyond the given content, say so politely and suggest they re-read the section or ask a more specific question.
Keep answers concise but complete. For follow-up questions, use the conversation history and the document section.

Document section to use for your answers:
"""
    system_prompt += context

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
    """Parse LLM JSON response into list of QuizItem."""
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
