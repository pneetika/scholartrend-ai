from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.schemas.research import ResearchSource, TopicInsight
from app.services.llm import StructuredLLMClient
from app.services.research_analysis import compact_sources_for_prompt

WRITER_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {"type": "string"},
        "report_markdown": {"type": "string"},
        "key_findings": {"type": "array", "items": {"type": "string"}},
        "next_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["executive_summary", "report_markdown", "key_findings", "next_steps"],
    "additionalProperties": False,
}


class WriterAgent(BaseAgent):
    name = "Writer"

    def __init__(self, llm: StructuredLLMClient | None = None) -> None:
        self.llm = llm

    async def _run(self, context: dict[str, object]) -> dict[str, object]:
        query = str(context["query"])
        plan = list(context.get("plan", []))
        findings = list(context.get("findings", []))
        topic_map = [topic for topic in context.get("topic_map", []) if isinstance(topic, TopicInsight)]
        risks = list(context.get("risks", []))
        follow_ups = list(context.get("follow_ups", []))
        sources = [source for source in context.get("sources", []) if isinstance(source, ResearchSource)]

        executive_summary = self._build_summary(query=query, findings=findings, topic_map=topic_map, risks=risks)
        report_markdown = self._build_report(
            query=query,
            plan=plan,
            findings=findings,
            topic_map=topic_map,
            risks=risks,
            follow_ups=follow_ups,
            sources=sources,
        )
        key_findings = findings[:4]
        next_steps = follow_ups[:4]

        llm_payload = await self._llm_write(
            query=query,
            plan=plan,
            findings=findings,
            topic_map=topic_map,
            risks=risks,
            follow_ups=follow_ups,
            sources=sources,
        )
        if llm_payload is not None:
            executive_summary = llm_payload.get("executive_summary", executive_summary)
            report_markdown = llm_payload.get("report_markdown", report_markdown)
            key_findings = [item for item in llm_payload.get("key_findings", []) if item][:4] or key_findings
            next_steps = [item for item in llm_payload.get("next_steps", []) if item][:4] or next_steps

        return {
            "executive_summary": executive_summary,
            "report_markdown": report_markdown,
            "key_findings": key_findings,
            "next_steps": next_steps,
            "summary": "Drafted an NLP research brief with trend signals, citations, and next steps.",
            "steps": [
                "Converted the agent outputs into a stakeholder-friendly markdown report.",
                "Highlighted the most active themes in the paper set before listing evidence and cautions.",
            ],
        }

    async def _llm_write(
        self,
        *,
        query: str,
        plan: list[str],
        findings: list[str],
        topic_map: list[TopicInsight],
        risks: list[str],
        follow_ups: list[str],
        sources: list[ResearchSource],
    ) -> dict[str, object] | None:
        if self.llm is None or not self.llm.is_enabled or not sources:
            return None

        prompt = json.dumps(
            {
                "query": query,
                "plan": plan,
                "findings": findings,
                "topic_map": [topic.model_dump(mode="json") for topic in topic_map],
                "risks": risks,
                "follow_ups": follow_ups,
                "sources": compact_sources_for_prompt(sources),
            },
            ensure_ascii=True,
            indent=2,
        )
        return await self.llm.generate_json(
            instructions=(
                "You are the Writer agent in an NLP research assistant. "
                "Write a crisp briefing for a researcher or hiring manager who wants to understand what is happening now in NLP. "
                "The markdown report should include short sections for Landscape Snapshot, Topic Radar, Evidence Base, Risks, and Next Steps. "
                "Keep every claim tied to the supplied evidence and avoid hype."
            ),
            prompt=prompt,
            schema_name="research_report",
            schema=WRITER_SCHEMA,
            max_output_tokens=1800,
        )

    def _build_summary(
        self,
        *,
        query: str,
        findings: list[str],
        topic_map: list[TopicInsight],
        risks: list[str],
    ) -> str:
        if topic_map:
            lead = f"{topic_map[0].topic} is one of the clearest active threads in the current NLP paper set."
        elif findings:
            lead = findings[0]
        else:
            lead = f"The system assembled an initial research snapshot for {query}."

        if risks:
            return f"{lead} The brief is useful as a first pass, but {len(risks)} evidence gap(s) still need validation."
        return f"{lead} The evidence is broad enough for a first portfolio-grade briefing."

    def _build_report(
        self,
        *,
        query: str,
        plan: list[str],
        findings: list[str],
        topic_map: list[TopicInsight],
        risks: list[str],
        follow_ups: list[str],
        sources: list[ResearchSource],
    ) -> str:
        lines = [
            f"# NLP Research Brief: {query}",
            "",
            "## Landscape Snapshot",
            self._build_summary(query=query, findings=findings, topic_map=topic_map, risks=risks),
            "",
            "## Research Plan",
        ]

        for item in plan:
            lines.append(f"- {item}")

        lines.extend(["", "## Topic Radar"])
        if topic_map:
            for topic in topic_map:
                lines.append(f"### {topic.topic} ({topic.trend_signal})")
                lines.append(topic.summary)
                support_titles = [
                    source.title
                    for source in sources
                    if source.source_id in set(topic.supporting_source_ids)
                ][:3]
                if support_titles:
                    lines.append("")
                    lines.append(f"Supporting papers: {', '.join(support_titles)}.")
                lines.append("")
        else:
            lines.append("No clear topic clusters were extracted from the current evidence base.")
            lines.append("")

        lines.append("## Key Findings")
        for item in findings:
            lines.append(f"- {item}")

        lines.extend(["", "## Risks"])
        if risks:
            for item in risks:
                lines.append(f"- {item}")
        else:
            lines.append("- No major structural risks were flagged in the current evidence set.")

        lines.extend(["", "## Next Steps"])
        for item in follow_ups:
            lines.append(f"- {item}")

        lines.extend(["", "## Evidence Base"])
        for index, source in enumerate(sources, start=1):
            metadata_parts = []
            if source.venue:
                metadata_parts.append(source.venue)
            if source.published_at:
                metadata_parts.append(str(source.published_at.year))
            if source.citation_count is not None:
                metadata_parts.append(f"{source.citation_count} citations")
            metadata_text = f" [{' | '.join(metadata_parts)}]" if metadata_parts else ""
            url = f" ({source.url})" if source.url else ""
            lines.append(f"{index}. {source.title}{metadata_text}{url}")
            if source.authors:
                lines.append(f"   Authors: {', '.join(source.authors[:5])}")
            lines.append(f"   {source.snippet[:280]}")

        return "\n".join(lines)
