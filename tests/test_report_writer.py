from __future__ import annotations

import pytest

from src.agents.paper_summarizer import PaperSummarizationAgent
from src.agents.report_writer import ReportWriterAgent
from src.evaluation.eval_pipeline import EvaluationPipeline
from src.models.schemas import EvaluationMetrics, ResearchRequest, TimeRange
from src.providers.llm import MockLLMProvider


@pytest.mark.asyncio
async def test_report_writer_renders_markdown_sections(sample_ranked_papers):
    summarizer = PaperSummarizationAgent(MockLLMProvider())
    summary_payload, _ = await summarizer.run({"ranked_papers": sample_ranked_papers})
    evaluation = EvaluationPipeline().score(
        ranked_papers=sample_ranked_papers,
        summaries=summary_payload["paper_summaries"],
        themes=[],
        issues=[],
    )
    agent = ReportWriterAgent()
    payload, _trace = await agent.run(
        {
            "run_id": "run-test",
            "request": ResearchRequest(topic="Agentic AI in financial services", time_range=TimeRange.ONE_YEAR),
            "ranked_papers": sample_ranked_papers,
            "paper_summaries": summary_payload["paper_summaries"],
            "themes": [],
            "methods_and_techniques": ["retrieval-grounded agents"],
            "research_gaps": ["limited benchmark coverage"],
            "validation_issues": [],
            "evaluation": evaluation,
            "agent_steps": [],
            "human_review_required": False,
        }
    )

    markdown = payload["report"].report_markdown
    assert "# Research Trend Report:" in markdown
    assert "## Top Papers" in markdown
    assert "## References" in markdown
