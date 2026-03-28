"""Web search and industry standards router."""

from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import SearchRequest, SearchResponse, SourceLink
from ..services.web_search import search_industry_standards

router = APIRouter()


@router.post("/industry-standards", response_model=SearchResponse)
async def industry_standards(req: SearchRequest):
    result = search_industry_standards(req.topic_title, req.topic_content)
    return SearchResponse(
        summary=result.summary,
        sources=[
            SourceLink(title=s.title, url=s.url, snippet=s.snippet)
            for s in result.sources
        ],
    )
