from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from src.models.schemas import PaperRecord, ResearchRequest, SourceName
from src.tools.base import BaseAcademicClient, request_start_date, safe_authors


class CrossrefClient(BaseAcademicClient):
    source_name = SourceName.CROSSREF
    endpoint = "https://api.crossref.org/works"

    async def search(self, query: str, request: ResearchRequest) -> List[PaperRecord]:
        params: Dict[str, Any] = {
            "query.title": query,
            "rows": request.paper_limit,
            "sort": "published",
            "order": "desc",
        }
        start_date = request_start_date(request)
        if start_date:
            params["filter"] = f"from-pub-date:{start_date.isoformat()}"

        payload = await self.http_client.get_json(
            self.endpoint,
            params=params,
            cache_namespace="crossref",
        )

        papers: List[PaperRecord] = []
        for index, item in enumerate(payload.get("message", {}).get("items", []), start=1):
            published = self._extract_date(item)
            title = " ".join(item.get("title", [])) or "Untitled paper"
            authors = [
                " ".join(part for part in [author.get("given"), author.get("family")] if part)
                for author in item.get("author", [])
            ]
            papers.append(
                PaperRecord(
                    paper_id=f"crossref:{item.get('DOI', index)}",
                    title=title,
                    abstract=(item.get("abstract") or "").replace("<jats:p>", "").replace("</jats:p>", ""),
                    authors=safe_authors(authors),
                    source=self.source_name,
                    source_rank=index,
                    url=item.get("URL"),
                    doi=item.get("DOI"),
                    venue=" ".join(item.get("container-title", [])) or None,
                    publication_date=published,
                    citation_count=item.get("is-referenced-by-count"),
                    raw_metadata=item,
                )
            )
        return papers

    def _extract_date(self, item: Dict[str, Any]) -> Optional[date]:
        for key in ("published-print", "published-online", "published"):
            parts = item.get(key, {}).get("date-parts", [])
            if parts and parts[0]:
                year = parts[0][0]
                month = parts[0][1] if len(parts[0]) > 1 else 1
                day = parts[0][2] if len(parts[0]) > 2 else 1
                return date(year, month, day)
        return None
