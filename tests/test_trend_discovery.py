from __future__ import annotations

import pytest

from src.agents.paper_summarizer import PaperSummarizationAgent
from src.agents.trend_discovery import TrendDiscoveryAgent
from src.providers.llm import MockLLMProvider


class DummyEmbeddingService:
    async def embed_texts(self, texts):
        return [[float(index + 1), 0.5, 0.1] for index, _ in enumerate(texts)]


@pytest.mark.asyncio
async def test_trend_discovery_returns_themes(sample_ranked_papers):
    summarizer = PaperSummarizationAgent(MockLLMProvider())
    summary_payload, _ = await summarizer.run({"ranked_papers": sample_ranked_papers})
    agent = TrendDiscoveryAgent(DummyEmbeddingService())
    payload, _trace = await agent.run(
        {
            "ranked_papers": sample_ranked_papers,
            "paper_summaries": summary_payload["paper_summaries"],
        }
    )

    assert payload["themes"]
    assert payload["methods_and_techniques"]
