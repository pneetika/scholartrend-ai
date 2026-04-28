from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from src.agents.critic_validator import CriticValidatorAgent
from src.agents.literature_search import LiteratureSearchAgent
from src.agents.paper_summarizer import PaperSummarizationAgent
from src.agents.query_planner import QueryPlannerAgent
from src.agents.relevance_ranker import RelevanceRankingAgent
from src.agents.report_writer import ReportWriterAgent
from src.agents.trend_discovery import TrendDiscoveryAgent
from src.evaluation.eval_pipeline import EvaluationPipeline
from src.models.schemas import AgentStepTrace, EvaluationMetrics, ResearchRequest, ResearchReport, ValidationIssue


class ResearchState(TypedDict, total=False):
    run_id: str
    request: ResearchRequest
    query_plan: object
    retrieved_papers: list
    ranked_papers: list
    paper_summaries: list
    themes: list
    methods_and_techniques: list
    research_gaps: list
    validation_issues: list
    evaluation: EvaluationMetrics
    human_review_required: bool
    report: ResearchReport
    agent_steps: List[AgentStepTrace]


class ScholarTrendResearchGraph:
    def __init__(
        self,
        *,
        planner: QueryPlannerAgent,
        search_agent: LiteratureSearchAgent,
        ranker: RelevanceRankingAgent,
        summarizer: PaperSummarizationAgent,
        trend_discovery: TrendDiscoveryAgent,
        critic: CriticValidatorAgent,
        writer: ReportWriterAgent,
        evaluation_pipeline: EvaluationPipeline,
    ) -> None:
        self.planner = planner
        self.search_agent = search_agent
        self.ranker = ranker
        self.summarizer = summarizer
        self.trend_discovery = trend_discovery
        self.critic = critic
        self.writer = writer
        self.evaluation_pipeline = evaluation_pipeline
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(ResearchState)
        builder.add_node("planner", self._planner_node)
        builder.add_node("search", self._search_node)
        builder.add_node("rank", self._rank_node)
        builder.add_node("summarize", self._summarize_node)
        builder.add_node("discover_trends", self._trends_node)
        builder.add_node("critic", self._critic_node)
        builder.add_node("evaluate", self._evaluation_node)
        builder.add_node("write_report", self._writer_node)

        builder.add_edge(START, "planner")
        builder.add_edge("planner", "search")
        builder.add_edge("search", "rank")
        builder.add_edge("rank", "summarize")
        builder.add_edge("summarize", "discover_trends")
        builder.add_edge("discover_trends", "critic")
        builder.add_edge("critic", "evaluate")
        builder.add_edge("evaluate", "write_report")
        builder.add_edge("write_report", END)
        return builder.compile()

    async def run(self, request: ResearchRequest) -> ResearchReport:
        initial_state: ResearchState = {
            "run_id": f"run-{uuid.uuid4().hex[:12]}",
            "request": request,
            "agent_steps": [],
        }
        result = await self.graph.ainvoke(initial_state)
        return result["report"]

    async def _planner_node(self, state: ResearchState) -> ResearchState:
        return await self._run_agent(self.planner, state)

    async def _search_node(self, state: ResearchState) -> ResearchState:
        return await self._run_agent(self.search_agent, state)

    async def _rank_node(self, state: ResearchState) -> ResearchState:
        return await self._run_agent(self.ranker, state)

    async def _summarize_node(self, state: ResearchState) -> ResearchState:
        return await self._run_agent(self.summarizer, state)

    async def _trends_node(self, state: ResearchState) -> ResearchState:
        return await self._run_agent(self.trend_discovery, state)

    async def _critic_node(self, state: ResearchState) -> ResearchState:
        return await self._run_agent(self.critic, state)

    async def _writer_node(self, state: ResearchState) -> ResearchState:
        return await self._run_agent(self.writer, state)

    async def _evaluation_node(self, state: ResearchState) -> ResearchState:
        metrics = self.evaluation_pipeline.score(
            ranked_papers=state.get("ranked_papers", []),
            summaries=state.get("paper_summaries", []),
            themes=state.get("themes", []),
            issues=state.get("validation_issues", []),
        )
        return {"evaluation": metrics}

    async def _run_agent(self, agent, state: ResearchState) -> ResearchState:
        payload, trace = await agent.run(dict(state))
        traces = list(state.get("agent_steps", []))
        traces.append(trace)
        payload["agent_steps"] = traces
        if "report" in payload:
            payload["report"].agent_steps = traces
        return payload
