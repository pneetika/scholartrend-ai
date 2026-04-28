from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from app.schemas.research import ResearchSource, TopicInsight

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "their",
    "these",
    "this",
    "to",
    "toward",
    "with",
    "using",
    "via",
    "recent",
    "paper",
    "papers",
    "study",
    "results",
    "model",
    "models",
    "language",
    "task",
    "tasks",
    "method",
    "methods",
    "nlp",
}

CURATED_TOPICS = [
    "retrieval augmented generation",
    "large language models",
    "small language models",
    "agentic systems",
    "tool use",
    "reasoning",
    "multimodal",
    "alignment",
    "evaluation",
    "benchmarks",
    "synthetic data",
    "long context",
    "multilingual",
    "code generation",
    "information extraction",
]


def compact_sources_for_prompt(sources: list[ResearchSource], limit: int = 12) -> list[dict[str, object]]:
    compacted: list[dict[str, object]] = []
    for source in sources[:limit]:
        compacted.append(
            {
                "source_id": source.source_id,
                "title": source.title,
                "snippet": source.snippet[:500],
                "provider": source.provider,
                "venue": source.venue,
                "published_at": source.published_at.isoformat() if source.published_at else None,
                "authors": source.authors[:5],
                "citation_count": source.citation_count,
                "keywords": source.keywords[:6],
            }
        )
    return compacted


def build_topic_map(
    sources: list[ResearchSource],
    fallback_terms: list[str] | None = None,
    limit: int = 4,
) -> list[TopicInsight]:
    phrase_to_sources: dict[str, set[str]] = defaultdict(set)
    phrase_counts: Counter[str] = Counter()

    for source in sources:
        phrases = _candidate_phrases(source)
        for phrase in phrases:
            phrase_to_sources[phrase].add(source.source_id)
            phrase_counts[phrase] += 1

    for term in fallback_terms or []:
        normalized = normalize_topic(term)
        if normalized:
            phrase_counts[normalized] += 1

    ranked = sorted(
        phrase_counts,
        key=lambda phrase: (
            len(phrase_to_sources.get(phrase, set())),
            phrase_counts[phrase],
            _topic_bonus(phrase),
            len(phrase.split()),
        ),
        reverse=True,
    )

    insights: list[TopicInsight] = []
    seen_prefixes: set[str] = set()
    for phrase in ranked:
        if len(insights) >= limit:
            break

        prefix = phrase.split()[0]
        if prefix in seen_prefixes and len(phrase.split()) == 1:
            continue

        matching_sources = [
            source
            for source in sources
            if source.source_id in phrase_to_sources.get(phrase, set())
        ]
        if not matching_sources and fallback_terms:
            matching_sources = sources[:2]
        if not matching_sources:
            continue

        seen_prefixes.add(prefix)
        insights.append(
            TopicInsight(
                topic=phrase.title(),
                trend_signal=_trend_signal(matching_sources),
                summary=_topic_summary(phrase, matching_sources),
                supporting_source_ids=[source.source_id for source in matching_sources[:4]],
            )
        )

    if insights:
        return insights

    fallback = normalize_topic((fallback_terms or ["NLP research landscape"])[0])
    return [
        TopicInsight(
            topic=fallback.title(),
            trend_signal="watchlist",
            summary="Live results are limited, so this topic should be refreshed with more papers or uploaded references.",
            supporting_source_ids=[source.source_id for source in sources[:3]],
        )
    ]


def build_fallback_findings(
    query: str,
    plan: list[str],
    sources: list[ResearchSource],
    topic_map: list[TopicInsight],
) -> list[str]:
    findings: list[str] = []
    for topic in topic_map[:3]:
        findings.append(f"{topic.topic} shows {topic.trend_signal} momentum across the recent paper set.")

    for item in plan[:2]:
        if len(findings) >= 4:
            break
        findings.append(f"{item} The current evidence base includes {min(len(sources), 6)} supporting sources.")

    if not findings:
        findings.append(f"Recent research evidence has been collected for {query}.")

    return findings[:4]


def normalize_topic(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip().lower())
    return cleaned.strip(".,:;!?")


def _candidate_phrases(source: ResearchSource) -> set[str]:
    text = f"{source.title} {source.snippet}"
    tokens = [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z\-]+", text.lower())
        if token not in STOPWORDS and len(token) > 2
    ]

    phrases: set[str] = set()
    for size in (3, 2, 1):
        for index in range(0, max(0, len(tokens) - size + 1)):
            parts = tokens[index : index + size]
            if any(part in STOPWORDS for part in parts):
                continue
            phrase = " ".join(parts)
            if len(phrase) < 5:
                continue
            phrases.add(phrase)

    for curated in CURATED_TOPICS:
        if curated in text.lower():
            phrases.add(curated)

    return phrases


def _topic_bonus(phrase: str) -> int:
    bonus = 0
    for curated in CURATED_TOPICS:
        if curated == phrase:
            bonus += 5
        elif curated in phrase:
            bonus += 2
    return bonus


def _trend_signal(sources: list[ResearchSource]) -> str:
    published_dates = [source.published_at for source in sources if source.published_at is not None]
    if not published_dates:
        return "watchlist"

    now = datetime.now(timezone.utc)
    avg_age_days = sum((now - published_at).days for published_at in published_dates) / len(published_dates)
    avg_citations = sum((source.citation_count or 0) for source in sources) / len(sources)

    if avg_age_days <= 120 and len(sources) >= 2:
        return "emerging"
    if avg_age_days <= 270:
        return "accelerating"
    if avg_citations >= 40 or len(sources) >= 3:
        return "established"
    return "watchlist"


def _topic_summary(topic: str, sources: list[ResearchSource]) -> str:
    venues = sorted({source.venue for source in sources if source.venue})[:2]
    dates = [source.published_at for source in sources if source.published_at]
    newest_year = max((date.year for date in dates), default=None)
    venue_text = f" across {', '.join(venues)}" if venues else ""
    year_text = f" in {newest_year}" if newest_year else ""
    return (
        f"{topic.title()} appears in {len(sources)} supporting papers{venue_text}{year_text}, "
        "suggesting sustained interest in this line of NLP work."
    )
