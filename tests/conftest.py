from __future__ import annotations

from datetime import date

import pytest

from src.models.schemas import PaperAuthor, PaperRecord, RankedPaper, SourceName


@pytest.fixture
def sample_papers():
    return [
        PaperRecord(
            paper_id="arxiv:1",
            title="Agentic AI for Financial Risk Operations",
            abstract=(
                "We present a retrieval-grounded agent architecture for financial risk operations. "
                "The approach combines tool use and document retrieval. Results show improved accuracy. "
                "Limitations include dataset scarcity. Future work includes stronger benchmarks."
            ),
            authors=[PaperAuthor(name="Ada Researcher")],
            source=SourceName.ARXIV,
            url="https://arxiv.org/abs/1",
            publication_date=date(2025, 1, 11),
            citation_count=14,
        ),
        PaperRecord(
            paper_id="openalex:2",
            title="Evaluation Patterns for Financial LLM Agents",
            abstract=(
                "This study examines evaluation design for financial language model agents. "
                "We compare expert review and benchmark scoring. Findings show benchmark-only evaluation misses domain failures."
            ),
            authors=[PaperAuthor(name="Grace Liu")],
            source=SourceName.OPENALEX,
            url="https://openalex.org/W2",
            publication_date=date(2024, 10, 1),
            citation_count=18,
        ),
    ]


@pytest.fixture
def sample_ranked_papers(sample_papers):
    return [
        RankedPaper(
            paper=sample_papers[0],
            relevance_score=0.91,
            semantic_score=0.9,
            keyword_score=0.8,
            recency_score=0.8,
            citation_score=0.5,
            credibility_score=0.72,
            rationale="high semantic match",
        ),
        RankedPaper(
            paper=sample_papers[1],
            relevance_score=0.84,
            semantic_score=0.82,
            keyword_score=0.7,
            recency_score=0.7,
            citation_score=0.55,
            credibility_score=0.86,
            rationale="strong evaluation overlap",
        ),
    ]
