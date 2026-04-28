from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.agents.base import BaseAgent
from app.schemas.research import ResearchSource, TopicInsight
from app.services.llm import StructuredLLMClient
from app.services.research_analysis import compact_sources_for_prompt

CRITIC_SCHEMA = {
    "type": "object",
    "properties": {
        "risks": {"type": "array", "items": {"type": "string"}},
        "follow_ups": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["risks", "follow_ups"],
    "additionalProperties": False,
}


class CriticAgent(BaseAgent):
    name = "Critic"

    def __init__(self, llm: StructuredLLMClient | None = None) -> None:
        self.llm = llm

    async def _run(self, context: dict[str, object]) -> dict[str, object]:
        plan = list(context.get("plan", []))
        findings = list(context.get("findings", []))
        sources = [source for source in context.get("sources", []) if isinstance(source, ResearchSource)]
        topic_map = [topic for topic in context.get("topic_map", []) if isinstance(topic, TopicInsight)]
        recency_days = int(context.get("recency_days") or 365)

        risks = self._fallback_risks(
            plan=plan,
            findings=findings,
            sources=sources,
            topic_map=topic_map,
            recency_days=recency_days,
        )
        follow_ups = self._fallback_follow_ups(risks=risks)

        llm_payload = await self._llm_critique(
            plan=plan,
            findings=findings,
            sources=sources,
            topic_map=topic_map,
        )
        if llm_payload is not None:
            risks = [item for item in llm_payload.get("risks", []) if item][:5] or risks
            follow_ups = [item for item in llm_payload.get("follow_ups", []) if item][:5] or follow_ups

        return {
            "risks": risks,
            "follow_ups": follow_ups,
            "summary": "Reviewed evidence freshness, diversity, and grounding risks.",
            "steps": [
                "Checked whether the source set is recent enough and broad enough to support trend claims.",
                "Flagged where the brief may lean too hard on preprints, sparse evidence, or missing domain context.",
            ],
        }

    async def _llm_critique(
        self,
        *,
        plan: list[str],
        findings: list[str],
        sources: list[ResearchSource],
        topic_map: list[TopicInsight],
    ) -> dict[str, object] | None:
        if self.llm is None or not self.llm.is_enabled or not sources:
            return None

        prompt = json.dumps(
            {
                "plan": plan,
                "findings": findings,
                "topic_map": [topic.model_dump(mode="json") for topic in topic_map],
                "sources": compact_sources_for_prompt(sources),
            },
            ensure_ascii=True,
            indent=2,
        )
        return await self.llm.generate_json(
            instructions=(
                "You are the Critic agent in an NLP research assistant. "
                "Audit the evidence for blind spots, overclaiming, staleness, and weak grounding. "
                "Return only concrete risks and practical validation follow-ups."
            ),
            prompt=prompt,
            schema_name="research_critique",
            schema=CRITIC_SCHEMA,
            max_output_tokens=900,
        )

    def _fallback_risks(
        self,
        *,
        plan: list[str],
        findings: list[str],
        sources: list[ResearchSource],
        topic_map: list[TopicInsight],
        recency_days: int,
    ) -> list[str]:
        risks: list[str] = []
        if len(sources) < max(5, len(plan) + 1):
            risks.append("The evidence pool is still narrow for making strong claims about the full NLP landscape.")
        if len(findings) < len(plan):
            risks.append("Some planned questions still lack explicit findings or supporting evidence.")
        if not any(source.source_type == "document" for source in sources):
            risks.append("No uploaded papers or notes were used, so the brief is grounded only in live scholarly APIs.")
        if not any(source.provider == "crossref" for source in sources):
            risks.append("The run leans heavily toward preprints; add peer-reviewed coverage before final conclusions.")
        if len(topic_map) < 2:
            risks.append("Topic clustering is shallow, which may mean the query is too broad or the evidence is too sparse.")

        cutoff = datetime.now(timezone.utc) - timedelta(days=recency_days)
        recent_count = sum(
            1
            for source in sources
            if source.published_at is not None and source.published_at >= cutoff
        )
        if recent_count and recent_count < max(2, len(sources) // 2):
            risks.append("Several sources fall outside the desired recency window, so momentum claims need extra caution.")

        return risks

    def _fallback_follow_ups(self, *, risks: list[str]) -> list[str]:
        follow_ups = [
            "Refresh the query with narrower subtopics if you want a sharper trend story.",
            "Cross-check the most important claim against at least one peer-reviewed source.",
            "Upload one or two survey papers or lab notes to strengthen the RAG grounding layer.",
        ]
        if risks:
            follow_ups.insert(0, "Run a second research pass focused only on the flagged gaps.")
        return follow_ups[:4]
