from __future__ import annotations

import json
import re

from app.agents.base import BaseAgent
from app.services.llm import StructuredLLMClient

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "report_title": {"type": "string"},
        "plan": {"type": "array", "items": {"type": "string"}},
        "search_queries": {"type": "array", "items": {"type": "string"}},
        "focus_areas": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["report_title", "plan", "search_queries", "focus_areas"],
    "additionalProperties": False,
}


class PlannerAgent(BaseAgent):
    name = "Planner"

    def __init__(self, llm: StructuredLLMClient | None = None) -> None:
        self.llm = llm

    async def _run(self, context: dict[str, object]) -> dict[str, object]:
        query = str(context["query"]).strip()
        goals = [goal for goal in context.get("goals", []) if goal]
        memory = context.get("memory", [])
        external_context = context.get("context")

        plan_payload = await self._llm_plan(
            query=query,
            goals=goals,
            memory=memory,
            external_context=external_context,
        )
        required_keys = {"report_title", "plan", "search_queries", "focus_areas"}
        if plan_payload is None or not required_keys.issubset(plan_payload):
            plan_payload = self._fallback_plan(query=query, goals=goals)

        plan = self._dedupe(plan_payload["plan"])[:5]
        search_queries = self._dedupe(plan_payload["search_queries"])[:6]
        focus_areas = self._dedupe(plan_payload["focus_areas"])[:5]

        return {
            "report_title": plan_payload["report_title"],
            "plan": plan,
            "search_queries": search_queries,
            "focus_areas": focus_areas,
            "summary": f"Built a {len(plan)}-step research plan focused on recent NLP themes.",
            "steps": [
                "Translated the user question into research tracks, search queries, and focus areas.",
                "Kept the plan scoped to recent scholarly activity rather than generic web content.",
            ],
        }

    async def _llm_plan(
        self,
        *,
        query: str,
        goals: list[str],
        memory: object,
        external_context: object,
    ) -> dict[str, object] | None:
        if self.llm is None or not self.llm.is_enabled:
            return None

        prompt = json.dumps(
            {
                "query": query,
                "goals": goals,
                "context": external_context,
                "memory": memory,
            },
            ensure_ascii=True,
            default=str,
            indent=2,
        )

        return await self.llm.generate_json(
            instructions=(
                "You are the Planner agent inside an NLP research assistant. "
                "Create a tight research plan for discovering recent research directions in NLP. "
                "Produce search queries that will work well against paper APIs such as arXiv, Semantic Scholar, and Crossref. "
                "Favor phrases that surface current methods, evaluation trends, and open problems."
            ),
            prompt=prompt,
            schema_name="research_plan",
            schema=PLAN_SCHEMA,
            max_output_tokens=900,
        )

    def _fallback_plan(self, *, query: str, goals: list[str]) -> dict[str, object]:
        segments = [
            part.strip(" ?.")
            for part in re.split(r"\band\b|,|;", query, flags=re.IGNORECASE)
            if part.strip()
        ]

        focus_areas = segments[:3] or [query]
        plan = [
            "Scan recent papers to identify the most active NLP subtopics in the request area.",
            "Compare methods, datasets, and evaluation patterns across the strongest papers.",
            "Synthesize open problems, practical implications, and next experiments to watch.",
        ]

        for goal in goals[:2]:
            plan.append(f"Translate the evidence into a stakeholder-ready takeaway for: {goal}.")

        search_queries = [
            query,
            f"recent NLP papers {focus_areas[0]}",
            f"{focus_areas[0]} benchmark evaluation language models",
        ]
        for area in focus_areas[1:3]:
            search_queries.append(f"recent natural language processing research {area}")

        return {
            "report_title": f"NLP Research Radar: {query}",
            "plan": plan,
            "search_queries": search_queries,
            "focus_areas": focus_areas,
        }

    def _dedupe(self, items: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for item in items:
            normalized = item.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            deduped.append(normalized)
            seen.add(key)
        return deduped
