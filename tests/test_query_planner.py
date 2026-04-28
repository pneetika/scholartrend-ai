from __future__ import annotations

import pytest

from src.agents.query_planner import QueryPlannerAgent
from src.models.schemas import ResearchRequest, SourceName, TimeRange
from src.providers.llm import MockLLMProvider


@pytest.mark.asyncio
async def test_query_planner_adds_pubmed_for_healthcare_topic():
    agent = QueryPlannerAgent(MockLLMProvider())
    payload, _trace = await agent.run(
        {
            "request": ResearchRequest(
                topic="LLMs for healthcare summarization",
                time_range=TimeRange.ONE_YEAR,
                paper_limit=10,
                sources=[SourceName.ARXIV],
            )
        }
    )

    recommended = payload["query_plan"].recommended_sources
    assert SourceName.PUBMED in recommended
