from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from src.agents.base import BaseAgent
from src.models.schemas import (
    EvaluationMetrics,
    PaperSummary,
    RankedPaper,
    ReferenceEntry,
    ResearchReport,
    ThemeCluster,
    ValidationIssue,
)


class ReportWriterAgent(BaseAgent):
    name = "Report Writer Agent"

    async def _run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        run_id = state["run_id"]
        topic = state["request"].topic
        ranked_papers: List[RankedPaper] = state.get("ranked_papers", [])
        summaries: List[PaperSummary] = state.get("paper_summaries", [])
        themes: List[ThemeCluster] = state.get("themes", [])
        methods: List[str] = state.get("methods_and_techniques", [])
        gaps: List[str] = state.get("research_gaps", [])
        issues: List[ValidationIssue] = state.get("validation_issues", [])
        evaluation: EvaluationMetrics = state["evaluation"]
        human_review_required: bool = state.get("human_review_required", False)

        executive_summary = self._executive_summary(topic, themes, ranked_papers)
        recent_trends = [
            f"{theme.label}: {theme.description}"
            for theme in themes
        ]
        business_implications = self._business_implications(topic, themes, gaps)
        references = [
            ReferenceEntry(
                title=item.paper.title,
                url=item.paper.url,
                doi=item.paper.doi,
                source=item.paper.source,
            )
            for item in ranked_papers
        ]
        markdown = self._render_markdown(
            topic=topic,
            executive_summary=executive_summary,
            themes=themes,
            ranked_papers=ranked_papers,
            summaries=summaries,
            methods=methods,
            gaps=gaps,
            business_implications=business_implications,
            references=references,
        )

        report = ResearchReport(
            run_id=run_id,
            topic=topic,
            generated_at=datetime.utcnow(),
            executive_summary=executive_summary,
            key_research_themes=themes,
            recent_trends=recent_trends,
            top_papers=ranked_papers,
            paper_summaries=summaries,
            methods_and_techniques=methods,
            research_gaps=gaps,
            business_implications=business_implications,
            references=references,
            validation_issues=issues,
            evaluation=evaluation,
            agent_steps=state.get("agent_steps", []),
            report_markdown=markdown,
            human_review_required=human_review_required,
        )
        return {
            "report": report,
            "_trace_details": [
                f"Composed final research brief with {len(ranked_papers)} top papers and {len(themes)} themes.",
            ],
        }

    def _executive_summary(
        self,
        topic: str,
        themes: List[ThemeCluster],
        ranked_papers: List[RankedPaper],
    ) -> str:
        if not ranked_papers:
            return f"No strong evidence was retrieved yet for {topic}."
        theme_lead = themes[0].label if themes else "the strongest retrieved cluster"
        top_source = ranked_papers[0].paper.source.value.replace("_", " ")
        return (
            f"Recent literature on {topic} is coalescing around {theme_lead.lower()}, with the highest-ranked evidence "
            f"coming from {top_source} and adjacent scholarly sources. The current paper set suggests that researchers are "
            "balancing new agentic or retrieval-heavy techniques with evaluation rigor, domain constraints, and deployment concerns."
        )

    def _business_implications(
        self,
        topic: str,
        themes: List[ThemeCluster],
        gaps: List[str],
    ) -> List[str]:
        implications = [
            f"Teams exploring {topic} should benchmark both performance and operational risk before production rollout.",
            "The strongest near-term value is likely in analyst-assistive workflows rather than fully autonomous decisions.",
        ]
        if any("evaluation" in theme.label.lower() for theme in themes):
            implications.append("Evaluation maturity is becoming a competitive advantage, especially for regulated deployments.")
        if gaps:
            implications.append("Research gaps suggest opportunities for proprietary datasets, internal evaluation suites, or human review loops.")
        return implications[:5]

    def _render_markdown(
        self,
        *,
        topic: str,
        executive_summary: str,
        themes: List[ThemeCluster],
        ranked_papers: List[RankedPaper],
        summaries: List[PaperSummary],
        methods: List[str],
        gaps: List[str],
        business_implications: List[str],
        references: List[ReferenceEntry],
    ) -> str:
        lines = [f"# Research Trend Report: {topic}", "", "## Executive Summary", executive_summary, ""]

        lines.append("## Top Emerging Themes")
        for theme in themes:
            lines.append(f"### {theme.label}")
            lines.append(f"- Description: {theme.description}")
            lines.append(f"- Representative papers: {', '.join(theme.representative_paper_ids[:3])}")
            lines.append(f"- Why this is emerging: Trend signal is `{theme.trend_signal}`.")
        lines.append("")

        lines.append("## Top Papers")
        lines.append("| Title | Year | Authors | Source | Relevance score | Summary | Link |")
        lines.append("|---|---:|---|---|---:|---|---|")
        summary_lookup = {summary.paper_id: summary for summary in summaries}
        for item in ranked_papers:
            paper = item.paper
            summary = summary_lookup.get(paper.paper_id)
            author_names = ", ".join(author.name for author in paper.authors[:3])
            lines.append(
                f"| {paper.title} | {paper.publication_date.year if paper.publication_date else 'n/a'} | "
                f"{author_names or 'n/a'} | {paper.source.value} | {item.relevance_score:.2f} | "
                f"{(summary.short_summary if summary else paper.abstract[:140]).replace('|', '/')} | "
                f"{paper.url or ''} |"
            )
        lines.append("")

        lines.append("## Methods and Techniques Being Used")
        for item in methods or ["Method patterns are still emerging across the retrieved paper set."]:
            lines.append(f"- {item}")
        lines.append("")

        lines.append("## Research Gaps")
        for item in gaps or ["The current paper set does not expose consistent gap statements yet."]:
            lines.append(f"- {item}")
        lines.append("")

        lines.append("## Business / Product Implications")
        for item in business_implications:
            lines.append(f"- {item}")
        lines.append("")

        lines.append("## References")
        for reference in references:
            suffix = f" ({reference.url})" if reference.url else ""
            doi = f" DOI: {reference.doi}" if reference.doi else ""
            lines.append(f"- {reference.title} [{reference.source.value}]{doi}{suffix}")
        return "\n".join(lines)
