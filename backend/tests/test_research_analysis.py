from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.research import ResearchSource
from app.services.research_analysis import build_fallback_findings, build_topic_map


def make_source(
    source_id: str,
    title: str,
    snippet: str,
    *,
    provider: str = "arxiv",
    published_at: datetime | None = None,
) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        title=title,
        snippet=snippet,
        source_type="paper",
        provider=provider,
        authors=["Ada Lovelace"],
        venue="arXiv",
        published_at=published_at or datetime(2026, 1, 10, tzinfo=timezone.utc),
        keywords=[],
    )


def test_build_topic_map_surfaces_curated_topics() -> None:
    sources = [
        make_source(
            "s1",
            "Retrieval Augmented Generation for NLP Agents",
            "This paper studies retrieval augmented generation and tool use for language agents.",
        ),
        make_source(
            "s2",
            "Reasoning and Tool Use in Large Language Models",
            "We evaluate reasoning, tool use, and retrieval augmented generation in recent systems.",
            provider="semantic_scholar",
        ),
    ]

    topic_map = build_topic_map(sources, fallback_terms=["NLP agents"])

    assert topic_map
    topics = [topic.topic.lower() for topic in topic_map]
    assert any("retrieval augmented generation" in topic for topic in topics)


def test_build_fallback_findings_uses_topic_map() -> None:
    sources = [
        make_source(
            "s1",
            "Multilingual NLP Benchmarks",
            "Recent multilingual evaluation work highlights data imbalance and translation variance.",
        )
    ]
    topic_map = build_topic_map(sources, fallback_terms=["multilingual nlp"])

    findings = build_fallback_findings(
        query="recent multilingual NLP topics",
        plan=["Compare evaluation patterns."],
        sources=sources,
        topic_map=topic_map,
    )

    assert findings
    assert "momentum" in findings[0].lower()
