from __future__ import annotations

from typing import List

from src.models.schemas import PaperRecord, ResearchRequest, SourceName
from src.tools.base import BaseAcademicClient, parse_optional_date, request_start_date, safe_authors


class SemanticScholarClient(BaseAcademicClient):
    source_name = SourceName.SEMANTIC_SCHOLAR
    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def search(self, query: str, request: ResearchRequest) -> List[PaperRecord]:
        payload = await self.http_client.get_json(
            self.endpoint,
            params={
                "query": query,
                "limit": request.paper_limit,
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
            cache_namespace="semantic_scholar",
        )

        min_date = request_start_date(request)
        papers: List[PaperRecord] = []
        for index, item in enumerate(payload.get("data", []), start=1):
            published = parse_optional_date(item.get("publicationDate") or str(item.get("year") or ""))
            if min_date and published and published < min_date:
                continue
            authors = [author.get("name", "") for author in item.get("authors", [])]
            external_ids = item.get("externalIds") or {}
            papers.append(
                PaperRecord(
                    paper_id=f"semanticscholar:{item.get('paperId', index)}",
                    title=item.get("title", "Untitled paper"),
                    abstract=item.get("abstract") or "",
                    authors=safe_authors(authors),
                    source=self.source_name,
                    source_rank=index,
                    url=item.get("url"),
                    doi=external_ids.get("DOI"),
                    venue=item.get("venue"),
                    publication_date=published,
                    citation_count=item.get("citationCount"),
                    raw_metadata=item,
                )
            )
        return papers
