"""Split document text into topics using LLM-based outline and content mapping."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from llm_config import get_llm


@dataclass
class Topic:
    """A single topic with title and its document content."""

    title: str
    content: str


def extract_topics(full_text: str, max_topics: int = 15) -> list[Topic]:
    """
    Use the LLM to split the document into logical topics and return title + content per topic.

    Args:
        full_text: The full document text.
        max_topics: Maximum number of topics to create (avoids huge lists and token overflow).

    Returns:
        List of Topic with title and content (excerpt from the document).
    """
    if not full_text or not full_text.strip():
        return []

    # Truncate if very long to stay within context limits (e.g. 100k chars)
    text_to_use = full_text
    if len(full_text) > 120_000:
        text_to_use = full_text[:120_000] + "\n\n[Document truncated for processing.]"

    system_prompt = """You are a precise assistant. Your task is to split a document into logical topics (sections).
For each topic, provide a short, clear title and the exact excerpt from the document that covers that topic.
Do not invent or paraphrase: "content" must be verbatim text from the document.
Return valid JSON only, no markdown or explanation. Format: [{"title": "...", "content": "..."}, ...]
Use between 3 and """ + str(max_topics) + """ topics. Each topic's content should be a contiguous excerpt."""

    user_prompt = f"""Document:\n\n{text_to_use}\n\nReturn the JSON array of topics (title + content) as specified."""

    llm = get_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    return _parse_topics_response(content)


def _parse_topics_response(content: str) -> list[Topic]:
    """Parse LLM response into list of Topic; fallback to single topic on parse failure."""
    content = content.strip()
    # Remove optional markdown code fence
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return [Topic(title="Full document", content=content[:50000])]

    if not isinstance(data, list):
        return [Topic(title="Full document", content=content[:50000])]

    topics: list[Topic] = []
    for item in data:
        if isinstance(item, dict):
            title = item.get("title") or "Untitled"
            text = item.get("content") or ""
            if isinstance(title, str) and isinstance(text, str):
                topics.append(Topic(title=title.strip(), content=text.strip()))
    if not topics:
        return [Topic(title="Full document", content=content[:50000])]
    return topics
