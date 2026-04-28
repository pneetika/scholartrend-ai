from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List

from src.models.schemas import PaperRecord, ResearchRequest, SourceName
from src.tools.base import BaseAcademicClient, parse_optional_date, request_start_date, safe_authors


class ArxivClient(BaseAcademicClient):
    source_name = SourceName.ARXIV
    endpoint = "https://export.arxiv.org/api/query"

    async def search(self, query: str, request: ResearchRequest) -> List[PaperRecord]:
        xml_text = await self.http_client.get_text(
            self.endpoint,
            params={
                "search_query": f'all:"{query}"',
                "start": 0,
                "max_results": request.paper_limit,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
        )
        namespace = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(xml_text)
        min_date = request_start_date(request)

        papers: List[PaperRecord] = []
        for index, entry in enumerate(root.findall("atom:entry", namespace), start=1):
            published = parse_optional_date(entry.findtext("atom:published", default="", namespaces=namespace))
            if min_date and published and published < min_date:
                continue
            paper_id = entry.findtext("atom:id", default="", namespaces=namespace).rsplit("/", 1)[-1]
            title = " ".join(entry.findtext("atom:title", default="", namespaces=namespace).split())
            abstract = " ".join(entry.findtext("atom:summary", default="", namespaces=namespace).split())
            authors = [
                author.findtext("atom:name", default="", namespaces=namespace)
                for author in entry.findall("atom:author", namespace)
            ]
            papers.append(
                PaperRecord(
                    paper_id=f"arxiv:{paper_id}",
                    title=title,
                    abstract=abstract,
                    authors=safe_authors(authors),
                    source=self.source_name,
                    source_rank=index,
                    url=entry.findtext("atom:id", default="", namespaces=namespace),
                    pdf_url=f"https://arxiv.org/pdf/{paper_id}.pdf" if paper_id else None,
                    doi=entry.findtext("arxiv:doi", default="", namespaces=namespace) or None,
                    venue="arXiv",
                    publication_date=published,
                )
            )
        return papers
