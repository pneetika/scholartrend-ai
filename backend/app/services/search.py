from __future__ import annotations

import re
import uuid
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Any

import httpx

from app.schemas.research import ResearchSource


def _clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def _strip_tags(value: str | None) -> str:
    return _clean_text(re.sub(r"<[^>]+>", " ", value or ""))


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized.replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                parsed = datetime.strptime(normalized, fmt)
                break
            except ValueError:
                continue
        else:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_recent_enough(published_at: datetime | None, recency_days: int | None) -> bool:
    if published_at is None or recency_days is None:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(days=recency_days)
    return published_at >= cutoff


class SearchProvider(ABC):
    provider_name = "base"

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int,
        recency_days: int | None,
    ) -> list[ResearchSource]:
        raise NotImplementedError


class ArxivSearchProvider(SearchProvider):
    provider_name = "arxiv"
    endpoint = "https://export.arxiv.org/api/query"

    def __init__(self, timeout_seconds: float) -> None:
        self.client = httpx.AsyncClient(timeout=timeout_seconds)

    async def search(
        self,
        query: str,
        max_results: int,
        recency_days: int | None,
    ) -> list[ResearchSource]:
        response = await self.client.get(
            self.endpoint,
            params={
                "search_query": f'all:"{query}"',
                "start": 0,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
        )
        response.raise_for_status()

        namespace = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        root = ET.fromstring(response.text)

        results: list[ResearchSource] = []
        for entry in root.findall("atom:entry", namespace):
            title = _clean_text(entry.findtext("atom:title", default="", namespaces=namespace))
            snippet = _clean_text(entry.findtext("atom:summary", default="", namespaces=namespace))
            url = _clean_text(entry.findtext("atom:id", default="", namespaces=namespace)) or None
            published_at = _parse_date(
                entry.findtext("atom:published", default="", namespaces=namespace)
            )
            if not _is_recent_enough(published_at, recency_days):
                continue

            authors = [
                _clean_text(author.findtext("atom:name", default="", namespaces=namespace))
                for author in entry.findall("atom:author", namespace)
            ]
            doi = _clean_text(entry.findtext("arxiv:doi", default="", namespaces=namespace)) or None
            paper_id = url.rsplit("/", 1)[-1] if url else None

            results.append(
                ResearchSource(
                    source_id=f"arxiv-{paper_id or uuid.uuid4().hex[:8]}",
                    title=title or f"arXiv paper for {query}",
                    snippet=snippet or "Abstract unavailable from arXiv.",
                    url=url,
                    source_type="paper",
                    provider=self.provider_name,
                    authors=[author for author in authors if author],
                    venue="arXiv",
                    published_at=published_at,
                    citation_count=None,
                    doi=doi,
                    paper_id=paper_id,
                    relevance_score=None,
                )
            )

        return results[:max_results]

    async def aclose(self) -> None:
        await self.client.aclose()


class SemanticScholarSearchProvider(SearchProvider):
    provider_name = "semantic_scholar"
    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, timeout_seconds: float, api_key: str | None = None) -> None:
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        self.client = httpx.AsyncClient(timeout=timeout_seconds, headers=headers)

    async def search(
        self,
        query: str,
        max_results: int,
        recency_days: int | None,
    ) -> list[ResearchSource]:
        response = await self.client.get(
            self.endpoint,
            params={
                "query": query,
                "limit": max_results,
                "fields": ",".join(
                    [
                        "paperId",
                        "title",
                        "abstract",
                        "authors",
                        "year",
                        "venue",
                        "url",
                        "citationCount",
                        "publicationDate",
                        "externalIds",
                    ]
                ),
            },
        )
        response.raise_for_status()
        payload = response.json()

        results: list[ResearchSource] = []
        for item in payload.get("data", []):
            published_at = _parse_date(item.get("publicationDate") or str(item.get("year") or ""))
            if not _is_recent_enough(published_at, recency_days):
                continue

            external_ids = item.get("externalIds") or {}
            doi = external_ids.get("DOI")
            paper_id = item.get("paperId")
            results.append(
                ResearchSource(
                    source_id=f"sem-{paper_id or uuid.uuid4().hex[:8]}",
                    title=_clean_text(item.get("title")) or f"Semantic Scholar paper for {query}",
                    snippet=_clean_text(item.get("abstract")) or "Abstract unavailable from Semantic Scholar.",
                    url=item.get("url"),
                    source_type="paper",
                    provider=self.provider_name,
                    authors=[
                        _clean_text(author.get("name"))
                        for author in item.get("authors", [])
                        if _clean_text(author.get("name"))
                    ],
                    venue=_clean_text(item.get("venue")) or "Semantic Scholar",
                    published_at=published_at,
                    citation_count=item.get("citationCount"),
                    doi=doi,
                    paper_id=paper_id,
                    relevance_score=None,
                )
            )

        return results[:max_results]

    async def aclose(self) -> None:
        await self.client.aclose()


class CrossrefSearchProvider(SearchProvider):
    provider_name = "crossref"
    endpoint = "https://api.crossref.org/works"

    def __init__(self, timeout_seconds: float, mailto: str | None = None) -> None:
        user_agent = "AtlasResearchAssistant/0.1"
        if mailto:
            user_agent = f"{user_agent} (mailto:{mailto})"
        self.client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={"User-Agent": user_agent},
        )

    async def search(
        self,
        query: str,
        max_results: int,
        recency_days: int | None,
    ) -> list[ResearchSource]:
        params: dict[str, Any] = {
            "query.title": query,
            "rows": max_results,
            "sort": "published",
            "order": "desc",
        }
        if recency_days is not None:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=recency_days)).date().isoformat()
            params["filter"] = f"from-pub-date:{cutoff}"

        response = await self.client.get(self.endpoint, params=params)
        response.raise_for_status()
        payload = response.json()

        results: list[ResearchSource] = []
        for item in payload.get("message", {}).get("items", []):
            published_at = self._extract_published_at(item)
            if not _is_recent_enough(published_at, recency_days):
                continue

            title = _clean_text(" ".join(item.get("title", [])))
            venue = _clean_text(" ".join(item.get("container-title", []))) or "Crossref"
            doi = item.get("DOI")
            results.append(
                ResearchSource(
                    source_id=f"crossref-{(doi or uuid.uuid4().hex[:8]).replace('/', '_')}",
                    title=title or f"Crossref paper for {query}",
                    snippet=_strip_tags(item.get("abstract")) or "Abstract unavailable from Crossref.",
                    url=item.get("URL"),
                    source_type="paper",
                    provider=self.provider_name,
                    authors=self._extract_authors(item.get("author", [])),
                    venue=venue,
                    published_at=published_at,
                    citation_count=item.get("is-referenced-by-count"),
                    doi=doi,
                    paper_id=doi,
                    relevance_score=None,
                )
            )

        return results[:max_results]

    def _extract_authors(self, authors: list[dict[str, Any]]) -> list[str]:
        names: list[str] = []
        for author in authors:
            pieces = [_clean_text(author.get("given")), _clean_text(author.get("family"))]
            name = " ".join(piece for piece in pieces if piece)
            if name:
                names.append(name)
        return names

    def _extract_published_at(self, item: dict[str, Any]) -> datetime | None:
        for key in ("published-print", "published-online", "published"):
            parts = item.get(key, {}).get("date-parts", [])
            if parts and parts[0]:
                year = parts[0][0]
                month = parts[0][1] if len(parts[0]) > 1 else 1
                day = parts[0][2] if len(parts[0]) > 2 else 1
                return datetime(year, month, day, tzinfo=timezone.utc)
        return None

    async def aclose(self) -> None:
        await self.client.aclose()


class NullSearchProvider(SearchProvider):
    provider_name = "disabled"

    async def search(
        self,
        query: str,
        max_results: int,
        recency_days: int | None,
    ) -> list[ResearchSource]:
        return []


class ScholarlySearchService:
    def __init__(self, providers: list[SearchProvider]) -> None:
        self.providers = providers

    async def search(
        self,
        query: str,
        max_results: int,
        recency_days: int | None = None,
    ) -> list[ResearchSource]:
        deduped: dict[str, ResearchSource] = {}

        for provider in self.providers:
            try:
                results = await provider.search(
                    query=query,
                    max_results=max_results,
                    recency_days=recency_days,
                )
            except Exception:
                continue

            for rank, source in enumerate(results, start=1):
                source.relevance_score = round(1.0 / rank, 3)
                fingerprint = (
                    source.doi
                    or source.paper_id
                    or source.url
                    or f"{source.title.lower()}::{','.join(source.authors[:2]).lower()}"
                )
                if fingerprint not in deduped:
                    deduped[fingerprint] = source

        results = list(deduped.values())
        results.sort(
            key=lambda source: (
                source.published_at or datetime(1970, 1, 1, tzinfo=timezone.utc),
                source.citation_count or 0,
                source.relevance_score or 0.0,
            ),
            reverse=True,
        )
        return results[: max_results * max(1, len(self.providers))]

    async def aclose(self) -> None:
        for provider in self.providers:
            close = getattr(provider, "aclose", None)
            if callable(close):
                await close()
