"""Web search service: DuckDuckGo search + LLM synthesis for industry standards."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_config import get_llm


@dataclass
class SearchSource:
    title: str
    url: str
    snippet: str


@dataclass
class IndustryStandardsResult:
    summary: str
    sources: list[SearchSource]


def search_industry_standards(topic_title: str, topic_content: str = "") -> IndustryStandardsResult:
    """Search for current industry standards related to a topic and synthesize with LLM."""
    raw_results = _search_duckduckgo(topic_title)

    if not raw_results:
        return IndustryStandardsResult(
            summary="No search results found for this topic. Try a different search term.",
            sources=[],
        )

    sources = [
        SearchSource(title=r["title"], url=r["url"], snippet=r["snippet"])
        for r in raw_results
    ]

    search_context = "\n\n".join(
        f"**{r['title']}**\n{r['url']}\n{r['snippet']}" for r in raw_results
    )

    summary = _synthesize_with_llm(topic_title, topic_content, search_context)

    return IndustryStandardsResult(summary=summary, sources=sources)


def _search_duckduckgo(query: str, max_results: int = 8) -> list[dict]:
    """Search DuckDuckGo and return results."""
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            search_query = f"{query} industry standards best practices current"
            results = list(ddgs.text(search_query, max_results=max_results))

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", r.get("link", "")),
                "snippet": r.get("body", r.get("snippet", "")),
            }
            for r in results
            if r.get("title")
        ]
    except Exception:
        return []


def _synthesize_with_llm(topic_title: str, topic_content: str, search_context: str) -> str:
    """Use LLM to synthesize search results into a structured industry standards summary."""
    system_prompt = (
        "You are a knowledgeable industry analyst. Based on the web search results provided, "
        "create a structured summary of current industry standards and best practices related to the topic.\n\n"
        "Format your response with these sections:\n"
        "## Current Industry Practices\n"
        "Brief overview of how this topic is applied in industry today.\n\n"
        "## Key Tools & Technologies\n"
        "Relevant tools, frameworks, or technologies currently used.\n\n"
        "## Best Practices\n"
        "Recommended approaches and standards.\n\n"
        "## Recent Trends\n"
        "Any emerging trends or changes in the field.\n\n"
        "Base your summary strictly on the search results provided. Be concise and practical."
    )

    context_snippet = f"\n\nDocument context: {topic_content[:2000]}" if topic_content else ""

    user_prompt = (
        f"Topic: {topic_title}{context_snippet}\n\n"
        f"Web search results:\n\n{search_context}\n\n"
        "Synthesize these results into the structured industry standards summary."
    )

    llm = get_llm()
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)
