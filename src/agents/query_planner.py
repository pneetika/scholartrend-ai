from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from src.agents.base import BaseAgent
from src.models.schemas import ResearchRequest, SearchQueryPlan, SourceName
from src.providers.llm import BaseLLMProvider


PLANNER_SCHEMA = {
    "type": "object",
    "properties": {
        "domains": {"type": "array", "items": {"type": "string"}},
        "keyword_variants": {"type": "array", "items": {"type": "string"}},
        "search_queries": {"type": "array", "items": {"type": "string"}},
        "recommended_sources": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["domains", "keyword_variants", "search_queries", "recommended_sources", "notes"],
    "additionalProperties": False,
}


class QueryPlannerAgent(BaseAgent):
    name = "Query Planner Agent"

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self.llm_provider = llm_provider

    async def _run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        request: ResearchRequest = state["request"]
        fallback_plan = self._fallback_plan(request)

        prompt = json.dumps(
            {
                "topic": request.topic,
                "time_range": request.time_range.value,
                "paper_limit": request.paper_limit,
            },
            indent=2,
        )
        generated = await self.llm_provider.generate_json(
            prompt=prompt,
            schema=PLANNER_SCHEMA,
            system_prompt=(
                "You are a research query planning agent. Expand the user topic into academic search queries, "
                "synonyms, research domains, and recommended scholarly sources."
            ),
        )

        if generated:
            try:
                plan = SearchQueryPlan(
                    domains=generated.get("domains") or fallback_plan.domains,
                    keyword_variants=generated.get("keyword_variants") or fallback_plan.keyword_variants,
                    search_queries=generated.get("search_queries") or fallback_plan.search_queries,
                    recommended_sources=self._normalize_sources(
                        generated.get("recommended_sources") or [source.value for source in fallback_plan.recommended_sources]
                    ),
                    notes=generated.get("notes") or fallback_plan.notes,
                )
            except Exception:
                plan = fallback_plan
        else:
            plan = fallback_plan

        return {
            "query_plan": plan,
            "_trace_details": [
                f"Expanded topic into {len(plan.search_queries)} scholarly search queries.",
                f"Recommended sources: {', '.join(source.value for source in plan.recommended_sources)}.",
            ],
        }

    def _fallback_plan(self, request: ResearchRequest) -> SearchQueryPlan:
        topic = request.topic.lower().strip()
        words = [word for word in re.findall(r"[a-zA-Z][a-zA-Z\-]+", topic) if len(word) > 2]
        keyword_variants = list(dict.fromkeys(words + self._synonyms_for_topic(topic)))
        search_queries = [
            request.topic,
            f"recent research {request.topic}",
            f"{request.topic} evaluation benchmark",
            f"{request.topic} foundation models",
        ]
        if "agent" in topic or "agentic" in topic:
            search_queries.append(f"{request.topic} tool use planning workflow")
        if "health" in topic or "medical" in topic or "clinical" in topic:
            search_queries.append(f"{request.topic} biomedical literature")

        recommended_sources: List[SourceName] = [
            SourceName.ARXIV,
            SourceName.SEMANTIC_SCHOLAR,
            SourceName.CROSSREF,
            SourceName.OPENALEX,
        ]
        if any(token in topic for token in ["health", "medical", "clinical", "patient", "hospital"]):
            recommended_sources.append(SourceName.PUBMED)

        domains = self._domain_hints(topic)
        return SearchQueryPlan(
            domains=domains,
            keyword_variants=keyword_variants[:10],
            search_queries=list(dict.fromkeys(search_queries))[:6],
            recommended_sources=recommended_sources,
            notes=["Fallback planner used deterministic keyword expansion."],
        )

    def _synonyms_for_topic(self, topic: str) -> List[str]:
        synonyms = []
        if "llm" in topic or "language model" in topic:
            synonyms.extend(["large language models", "foundation models", "transformer models"])
        if "retrieval" in topic or "rag" in topic:
            synonyms.extend(["retrieval augmented generation", "retrieval pipelines", "grounded generation"])
        if "agent" in topic:
            synonyms.extend(["autonomous agents", "agentic systems", "tool-using agents"])
        if "financial" in topic:
            synonyms.extend(["fintech", "risk analysis", "compliance automation"])
        if "health" in topic:
            synonyms.extend(["clinical summarization", "biomedical NLP", "medical decision support"])
        return synonyms

    def _domain_hints(self, topic: str) -> List[str]:
        domains = ["natural language processing", "machine learning"]
        if "financial" in topic:
            domains.append("financial services")
        if "health" in topic:
            domains.append("healthcare")
        if "retrieval" in topic or "rag" in topic:
            domains.append("information retrieval")
        if "sales" in topic:
            domains.append("analytics")
        return list(dict.fromkeys(domains))

    def _normalize_sources(self, values: List[str]) -> List[SourceName]:
        normalized = []
        for value in values:
            try:
                normalized.append(SourceName(value))
            except Exception:
                continue
        return normalized or [
            SourceName.ARXIV,
            SourceName.SEMANTIC_SCHOLAR,
            SourceName.CROSSREF,
            SourceName.OPENALEX,
        ]
