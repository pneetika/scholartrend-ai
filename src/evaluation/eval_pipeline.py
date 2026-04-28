from __future__ import annotations

from typing import List

from src.models.schemas import EvaluationMetrics, PaperSummary, RankedPaper, ThemeCluster, ValidationIssue


class EvaluationPipeline:
    def score(
        self,
        *,
        ranked_papers: List[RankedPaper],
        summaries: List[PaperSummary],
        themes: List[ThemeCluster],
        issues: List[ValidationIssue],
    ) -> EvaluationMetrics:
        source_diversity = min(1.0, len({item.paper.source.value for item in ranked_papers}) / 4.0) if ranked_papers else 0.0
        citation_completeness = (
            sum(1 for item in ranked_papers if item.paper.url or item.paper.doi) / max(1, len(ranked_papers))
        )
        grounding_score = (
            sum(1 for item in summaries if item.grounded) / max(1, len(summaries))
        )
        theme_diversity = min(1.0, len(themes) / 4.0)
        issue_penalty = min(0.3, len(issues) * 0.04)
        overall_score = max(
            0.0,
            round(
                ((source_diversity * 0.2) + (citation_completeness * 0.25) + (grounding_score * 0.35) + (theme_diversity * 0.2))
                - issue_penalty,
                3,
            ),
        )
        return EvaluationMetrics(
            source_diversity=round(source_diversity, 3),
            citation_completeness=round(citation_completeness, 3),
            grounding_score=round(grounding_score, 3),
            theme_diversity=round(theme_diversity, 3),
            overall_score=overall_score,
            notes=[
                f"Ranked paper count: {len(ranked_papers)}.",
                f"Theme count: {len(themes)}.",
                f"Validation issue count: {len(issues)}.",
            ],
        )
