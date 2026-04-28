from __future__ import annotations

import pytest

from src.agents.relevance_ranker import RelevanceRankingAgent
from src.models.schemas import ResearchRequest, SourceName, TimeRange
from src.retrieval.vector_store import InMemoryVectorStore


class DummyEmbeddingService:
    async def embed_texts(self, texts):
        embeddings = []
        for text in texts:
            score = 1.0 if "financial" in text.lower() else 0.2
            embeddings.append([score, 1 - score, 0.0])
        return embeddings


@pytest.mark.asyncio
async def test_relevance_ranker_returns_ranked_papers(sample_papers):
    agent = RelevanceRankingAgent(DummyEmbeddingService(), InMemoryVectorStore())
    payload, _trace = await agent.run(
        {
            "request": ResearchRequest(
                topic="Agentic AI in financial services",
                time_range=TimeRange.ONE_YEAR,
                paper_limit=2,
                sources=[SourceName.ARXIV, SourceName.OPENALEX],
            ),
            "retrieved_papers": sample_papers,
        }
    )

    ranked = payload["ranked_papers"]
    assert len(ranked) == 2
    assert ranked[0].relevance_score >= ranked[1].relevance_score
