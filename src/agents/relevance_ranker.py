from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any, Dict, List

import numpy as np

from src.agents.base import BaseAgent
from src.models.schemas import PaperRecord, RankedPaper, ResearchRequest
from src.retrieval.deduplication import deduplicate_papers
from src.retrieval.embeddings import EmbeddingService
from src.retrieval.vector_store import VectorDocument


SOURCE_CREDIBILITY = {
    "pubmed": 0.95,
    "semantic_scholar": 0.9,
    "openalex": 0.86,
    "crossref": 0.82,
    "arxiv": 0.72,
    "papers_with_code": 0.68,
}


class RelevanceRankingAgent(BaseAgent):
    name = "Relevance Ranking Agent"

    def __init__(self, embedding_service: EmbeddingService, vector_store) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    async def _run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        request: ResearchRequest = state["request"]
        raw_papers: List[PaperRecord] = state.get("retrieved_papers", [])
        unique_papers = deduplicate_papers(raw_papers)
        if not unique_papers:
            return {
                "ranked_papers": [],
                "_trace_details": ["No papers available for ranking."],
            }

        topic_embedding = (await self.embedding_service.embed_texts([request.topic]))[0]
        paper_texts = [self._paper_text(paper) for paper in unique_papers]
        paper_embeddings = await self.embedding_service.embed_texts(paper_texts)
        ranked_papers = []

        vector_documents = []
        for paper, embedding in zip(unique_papers, paper_embeddings):
            semantic_score = self._cosine_similarity(topic_embedding, embedding)
            keyword_score = self._keyword_overlap(request.topic, self._paper_text(paper))
            recency_score = self._recency_score(paper.publication_date)
            citation_score = self._citation_score(paper.citation_count)
            credibility_score = SOURCE_CREDIBILITY.get(paper.source.value, 0.6)
            relevance_score = round(
                (semantic_score * 0.42)
                + (keyword_score * 0.2)
                + (recency_score * 0.18)
                + (citation_score * 0.12)
                + (credibility_score * 0.08),
                4,
            )
            ranked_papers.append(
                RankedPaper(
                    paper=paper,
                    relevance_score=relevance_score,
                    semantic_score=round(semantic_score, 4),
                    keyword_score=round(keyword_score, 4),
                    recency_score=round(recency_score, 4),
                    citation_score=round(citation_score, 4),
                    credibility_score=round(credibility_score, 4),
                    rationale=(
                        f"semantic={semantic_score:.2f}, keyword={keyword_score:.2f}, "
                        f"recency={recency_score:.2f}, citations={citation_score:.2f}"
                    ),
                )
            )
            vector_documents.append(
                VectorDocument(
                    document_id=paper.paper_id,
                    text=self._paper_text(paper),
                    metadata={
                        "title": paper.title,
                        "source": paper.source.value,
                        "url": paper.url,
                    },
                    embedding=embedding,
                )
            )

        ranked_papers.sort(key=lambda item: item.relevance_score, reverse=True)
        top_ranked = ranked_papers[: request.paper_limit]
        self.vector_store.upsert(vector_documents)

        return {
            "ranked_papers": top_ranked,
            "_trace_details": [
                f"Deduplicated {len(raw_papers)} raw results down to {len(unique_papers)} unique papers.",
                f"Kept the top {len(top_ranked)} papers after hybrid ranking.",
            ],
        }

    def _paper_text(self, paper: PaperRecord) -> str:
        return " ".join([paper.title, paper.abstract, " ".join(paper.keywords)]).strip()

    def _cosine_similarity(self, left: List[float], right: List[float]) -> float:
        left_vector = np.array(left)
        right_vector = np.array(right)
        return float(np.dot(left_vector, right_vector))

    def _keyword_overlap(self, topic: str, paper_text: str) -> float:
        topic_tokens = {token for token in re.findall(r"[a-zA-Z][a-zA-Z\-]+", topic.lower()) if len(token) > 2}
        paper_tokens = {token for token in re.findall(r"[a-zA-Z][a-zA-Z\-]+", paper_text.lower()) if len(token) > 2}
        if not topic_tokens:
            return 0.0
        return len(topic_tokens & paper_tokens) / len(topic_tokens)

    def _recency_score(self, publication_date: date) -> float:
        if publication_date is None:
            return 0.2
        age_days = (datetime.utcnow().date() - publication_date).days
        if age_days <= 90:
            return 1.0
        if age_days <= 180:
            return 0.85
        if age_days <= 365:
            return 0.7
        if age_days <= 730:
            return 0.45
        return 0.2

    def _citation_score(self, citation_count: int) -> float:
        if citation_count is None or citation_count <= 0:
            return 0.0
        return min(math.log1p(citation_count) / 5.0, 1.0)
