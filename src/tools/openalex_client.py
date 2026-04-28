from __future__ import annotations

from typing import List

from src.models.schemas import PaperRecord, ResearchRequest, SourceName
from src.tools.base import BaseAcademicClient, parse_optional_date, request_start_date, safe_authors


class OpenAlexClient(BaseAcademicClient):
    source_name = SourceName.OPENALEX
    endpoint = "https://api.openalex.org/works"

    async def search(self, query: str, request: ResearchRequest) -> List[PaperRecord]:
        params = {"search": query, "per-page": request.paper_limit, "page": 1}
        start_date = request_start_date(request)
        if start_date:
            params["filter"] = f"from_publication_date:{start_date.isoformat()}"

        payload = await self.http_client.get_json(
            self.endpoint,
            params=params,
            cache_namespace="openalex",
        )

        papers: List[PaperRecord] = []
        for index, item in enumerate(payload.get("results", []), start=1):
            authors = [
                authorship.get("author", {}).get("display_name", "")
                for authorship in item.get("authorships", [])
            ]
            abstract = self._decode_abstract(item.get("abstract_inverted_index") or {})
            papers.append(
                PaperRecord(
                    paper_id=f"openalex:{item.get('id', index)}",
                    title=item.get("display_name", "Untitled paper"),
                    abstract=abstract,
                    authors=safe_authors(authors),
                    source=self.source_name,
                    source_rank=index,
                    url=item.get("primary_location", {}).get("landing_page_url"),
                    doi=item.get("doi"),
                    venue=item.get("primary_location", {}).get("source", {}).get("display_name"),
                    publication_date=parse_optional_date(item.get("publication_date")),
                    citation_count=item.get("cited_by_count"),
                    raw_metadata=item,
                )
            )
        return papers

    def _decode_abstract(self, inverted_index):
        if not inverted_index:
            return ""
        position_map = {}
        for token, positions in inverted_index.items():
            for position in positions:
                position_map[position] = token
        return " ".join(position_map[position] for position in sorted(position_map))
