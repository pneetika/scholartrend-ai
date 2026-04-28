from __future__ import annotations

import re
from typing import Any, Dict, List

from src.agents.base import BaseAgent
from src.models.schemas import PaperSummary, RankedPaper, ResearchRequest, ThemeCluster, ValidationIssue


class CriticValidatorAgent(BaseAgent):
    name = "Critic / Validation Agent"

    async def _run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        request: ResearchRequest = state["request"]
        ranked_papers: List[RankedPaper] = state.get("ranked_papers", [])
        summaries: List[PaperSummary] = state.get("paper_summaries", [])
        themes: List[ThemeCluster] = state.get("themes", [])

        issues: List[ValidationIssue] = []
        for ranked_paper, summary in zip(ranked_papers, summaries):
            abstract_tokens = set(re.findall(r"[a-zA-Z][a-zA-Z\-]+", ranked_paper.paper.abstract.lower()))
            summary_tokens = set(re.findall(r"[a-zA-Z][a-zA-Z\-]+", summary.short_summary.lower()))
            overlap = len(abstract_tokens & summary_tokens) / max(1, len(summary_tokens))
            if overlap < 0.25 and ranked_paper.paper.abstract:
                summary.grounded = False
                issues.append(
                    ValidationIssue(
                        severity="high",
                        paper_id=ranked_paper.paper.paper_id,
                        message="Summary has low token overlap with the retrieved abstract and should be reviewed.",
                    )
                )
            if not ranked_paper.paper.url:
                issues.append(
                    ValidationIssue(
                        severity="medium",
                        paper_id=ranked_paper.paper.paper_id,
                        message="Paper is missing a landing-page URL.",
                    )
                )
            if not ranked_paper.paper.abstract:
                issues.append(
                    ValidationIssue(
                        severity="medium",
                        paper_id=ranked_paper.paper.paper_id,
                        message="Paper lacks an abstract, so summary confidence is reduced.",
                    )
                )

        if len(themes) < 2:
            issues.append(
                ValidationIssue(
                    severity="medium",
                    message="Theme discovery produced limited diversity; consider broadening queries or source coverage.",
                )
            )

        human_review_required = request.require_human_review or any(
            issue.severity == "high" for issue in issues
        )

        return {
            "paper_summaries": summaries,
            "validation_issues": issues,
            "human_review_required": human_review_required,
            "_trace_details": [
                f"Flagged {len(issues)} validation issue(s).",
                "Human review recommended." if human_review_required else "No mandatory human review flag raised.",
            ],
        }
