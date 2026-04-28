from __future__ import annotations

from app.schemas.research import EvaluationMetrics, ResearchSource


class EvaluationService:
    def score(
        self,
        plan: list[str],
        findings: list[str],
        risks: list[str],
        sources: list[ResearchSource],
    ) -> EvaluationMetrics:
        plan_count = max(1, len(plan))
        finding_count = max(1, len(findings))
        source_count = len(sources)
        provider_count = len({source.provider for source in sources})

        citation_density = min(1.0, source_count / finding_count)
        evidence_coverage = min(1.0, (finding_count + max(0, provider_count - 1)) / (plan_count + 1))
        critique_score = max(0.2, 1.0 - (len(risks) * 0.15))
        overall_score = round(
            (citation_density * 0.4) + (evidence_coverage * 0.35) + (critique_score * 0.25),
            2,
        )

        notes = [
            f"{source_count} cited sources were available to support the final brief.",
            f"{len(findings)} findings were generated across {len(plan)} planned workstreams and {provider_count} source providers.",
        ]
        if risks:
            notes.append("Critic agent surfaced unresolved risks that should be validated before execution.")
        else:
            notes.append("Critic agent did not flag major structural weaknesses in the current draft.")

        return EvaluationMetrics(
            citation_density=round(citation_density, 2),
            evidence_coverage=round(evidence_coverage, 2),
            critique_score=round(critique_score, 2),
            overall_score=overall_score,
            notes=notes,
        )
