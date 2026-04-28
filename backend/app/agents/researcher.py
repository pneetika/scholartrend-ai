from __future__ import annotations

import asyncio
import json
from collections import OrderedDict

from app.agents.base import BaseAgent
from app.rag.pipeline import RAGPipeline
from app.schemas.research import ResearchSource, TopicInsight
from app.services.llm import StructuredLLMClient
from app.services.research_analysis import (
    build_fallback_findings,
    build_topic_map,
    compact_sources_for_prompt,
)
from app.services.search import ScholarlySearchService

RESEARCHER_SCHEMA = {
    "type": "object",
    "properties": {
        "key_findings": {"type": "array", "items": {"type": "string"}},
        "topic_map": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "trend_signal": {
                        "type": "string",
                        "enum": ["emerging", "accelerating", "established", "watchlist"],
                    },
                    "summary": {"type": "string"},
                    "supporting_source_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["topic", "trend_signal", "summary", "supporting_source_ids"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["key_findings", "topic_map"],
    "additionalProperties": False,
}


class ResearcherAgent(BaseAgent):
    name = "Researcher"

    def __init__(
        self,
        search_service: ScholarlySearchService,
        rag_pipeline: RAGPipeline,
        default_top_k: int,
        llm: StructuredLLMClient | None = None,
    ) -> None:
        self.search_service = search_service
        self.rag_pipeline = rag_pipeline
        self.default_top_k = default_top_k
        self.llm = llm

    async def _run(self, context: dict[str, object]) -> dict[str, object]:
        query = str(context["query"])
        plan = list(context.get("plan", []))
        search_queries = list(context.get("search_queries", [])) or [query]
        focus_areas = list(context.get("focus_areas", []))
        include_web_search = bool(context.get("include_web_search", True))
        top_k = int(context.get("top_k") or self.default_top_k)
        recency_days = int(context.get("recency_days") or 365)

        scholarly_sources: list[ResearchSource] = []
        if include_web_search:
            batches = await asyncio.gather(
                *[
                    self.search_service.search(
                        search_query,
                        max_results=top_k,
                        recency_days=recency_days,
                    )
                    for search_query in search_queries[:3]
                ],
                return_exceptions=True,
            )
            for batch in batches:
                if isinstance(batch, Exception):
                    continue
                scholarly_sources.extend(batch)

        retrieved_chunks = []
        for search_query in [query, *focus_areas[:2]]:
            retrieved_chunks.extend(self.rag_pipeline.retrieve(query=search_query, limit=top_k))

        local_sources = [
            ResearchSource(
                source_id=chunk.chunk_id,
                title=f"Upload: {chunk.document_name}",
                snippet=chunk.text[:420],
                url=None,
                source_type="document",
                provider="local-rag",
                venue="Local upload",
                relevance_score=chunk.score,
            )
            for chunk in retrieved_chunks
        ]

        deduped_sources: "OrderedDict[str, ResearchSource]" = OrderedDict()
        for source in [*scholarly_sources, *local_sources]:
            fingerprint = (
                source.doi
                or source.paper_id
                or source.url
                or f"{source.title.lower()}::{source.snippet[:80].lower()}"
            )
            deduped_sources.setdefault(fingerprint, source)

        sources = list(deduped_sources.values())[: max(top_k * 3, 8)]
        for source in sources:
            if not source.keywords:
                source.keywords = self._keywords_for_source(source)

        topic_map = build_topic_map(sources=sources, fallback_terms=focus_areas or [query])
        findings = build_fallback_findings(query=query, plan=plan, sources=sources, topic_map=topic_map)

        llm_payload = await self._llm_synthesis(
            query=query,
            plan=plan,
            sources=sources,
            topic_map=topic_map,
        )
        if llm_payload is not None:
            findings = [item for item in llm_payload.get("key_findings", []) if item][:4] or findings
            topic_map = [
                TopicInsight.model_validate(item)
                for item in llm_payload.get("topic_map", [])
                if item
            ] or topic_map

        return {
            "findings": findings,
            "topic_map": topic_map,
            "sources": sources,
            "summary": (
                f"Collected {len(sources)} sources from scholarly APIs and the local RAG store."
            ),
            "steps": [
                "Queried paper-centric sources for recent NLP evidence across multiple search tracks.",
                "Pulled supporting passages from uploaded documents so the final brief can stay grounded.",
                "Synthesized early topic signals before the critic and writer agents refine the story.",
            ],
        }

    async def _llm_synthesis(
        self,
        *,
        query: str,
        plan: list[str],
        sources: list[ResearchSource],
        topic_map: list[TopicInsight],
    ) -> dict[str, object] | None:
        if self.llm is None or not self.llm.is_enabled or not sources:
            return None

        prompt = json.dumps(
            {
                "query": query,
                "plan": plan,
                "seed_topic_map": [topic.model_dump(mode="json") for topic in topic_map],
                "sources": compact_sources_for_prompt(sources),
            },
            ensure_ascii=True,
            indent=2,
        )

        return await self.llm.generate_json(
            instructions=(
                "You are the Researcher agent in an NLP research assistant. "
                "Review the supplied papers and local notes, then identify the most active research directions. "
                "Return concise findings and a topic map that emphasize current momentum, not generic background."
            ),
            prompt=prompt,
            schema_name="research_findings",
            schema=RESEARCHER_SCHEMA,
            max_output_tokens=1200,
        )

    def _keywords_for_source(self, source: ResearchSource) -> list[str]:
        tokens = [
            token.lower()
            for token in source.title.replace(":", " ").replace(",", " ").split()
            if len(token) > 3
        ]
        deduped: list[str] = []
        seen: set[str] = set()
        for token in tokens:
            normalized = token.strip("().,;!?")
            if normalized in seen:
                continue
            deduped.append(normalized)
            seen.add(normalized)
        return deduped[:5]
