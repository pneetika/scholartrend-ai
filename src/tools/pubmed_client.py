from __future__ import annotations

from typing import List

from src.models.schemas import PaperRecord, ResearchRequest, SourceName
from src.tools.base import BaseAcademicClient, parse_optional_date, request_start_date, safe_authors


class PubMedClient(BaseAcademicClient):
    source_name = SourceName.PUBMED
    esearch_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    esummary_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    async def search(self, query: str, request: ResearchRequest) -> List[PaperRecord]:
        start_date = request_start_date(request)
        search_term = query
        if start_date:
            search_term = f"{query} AND {start_date.isoformat()}[pdat] : 3000[pdat]"

        search_payload = await self.http_client.get_json(
            self.esearch_endpoint,
            params={
                "db": "pubmed",
                "retmode": "json",
                "retmax": request.paper_limit,
                "sort": "pub_date",
                "term": search_term,
            },
            cache_namespace="pubmed_esearch",
        )
        ids = search_payload.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []

        summary_payload = await self.http_client.get_json(
            self.esummary_endpoint,
            params={
                "db": "pubmed",
                "retmode": "json",
                "id": ",".join(ids),
            },
            cache_namespace="pubmed_esummary",
        )

        papers: List[PaperRecord] = []
        for index, paper_id in enumerate(ids, start=1):
            item = summary_payload.get("result", {}).get(paper_id, {})
            authors = [author.get("name", "") for author in item.get("authors", [])]
            papers.append(
                PaperRecord(
                    paper_id=f"pubmed:{paper_id}",
                    title=item.get("title", "Untitled paper"),
                    abstract="",
                    authors=safe_authors(authors),
                    source=self.source_name,
                    source_rank=index,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{paper_id}/",
                    doi=None,
                    venue=item.get("fulljournalname"),
                    publication_date=parse_optional_date(item.get("pubdate")),
                    raw_metadata=item,
                )
            )
        return papers
