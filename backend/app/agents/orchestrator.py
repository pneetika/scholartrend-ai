from __future__ import annotations

import uuid

from app.agents.critic import CriticAgent
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.writer import WriterAgent
from app.core.logging import get_logger
from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.evaluation import EvaluationService
from app.services.memory import MemoryStore

LOGGER = get_logger(__name__)


class ResearchOrchestrator:
    def __init__(
        self,
        planner: PlannerAgent,
        researcher: ResearcherAgent,
        critic: CriticAgent,
        writer: WriterAgent,
        memory_store: MemoryStore,
        evaluation_service: EvaluationService,
    ) -> None:
        self.planner = planner
        self.researcher = researcher
        self.critic = critic
        self.writer = writer
        self.memory_store = memory_store
        self.evaluation_service = evaluation_service

    async def run(self, request: ResearchRequest) -> ResearchResponse:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:10]}"
        memory_snapshot = self.memory_store.recent(session_id=session_id, limit=6)

        planner_payload, planner_trace = await self.planner.run(
            {
                "query": request.query,
                "goals": request.goals,
                "context": request.context,
                "memory": memory_snapshot,
            }
        )

        researcher_payload, researcher_trace = await self.researcher.run(
            {
                "query": request.query,
                "plan": planner_payload["plan"],
                "search_queries": planner_payload.get("search_queries", []),
                "focus_areas": planner_payload.get("focus_areas", []),
                "include_web_search": request.include_web_search,
                "top_k": request.top_k,
                "recency_days": request.recency_days,
            }
        )

        critic_payload, critic_trace = await self.critic.run(
            {
                "plan": planner_payload["plan"],
                "findings": researcher_payload["findings"],
                "topic_map": researcher_payload["topic_map"],
                "sources": researcher_payload["sources"],
                "recency_days": request.recency_days,
            }
        )

        writer_payload, writer_trace = await self.writer.run(
            {
                "query": request.query,
                "plan": planner_payload["plan"],
                "findings": researcher_payload["findings"],
                "topic_map": researcher_payload["topic_map"],
                "risks": critic_payload["risks"],
                "follow_ups": critic_payload["follow_ups"],
                "sources": researcher_payload["sources"],
            }
        )

        evaluation = self.evaluation_service.score(
            plan=planner_payload["plan"],
            findings=writer_payload["key_findings"],
            risks=critic_payload["risks"],
            sources=researcher_payload["sources"],
        )

        self.memory_store.remember(session_id=session_id, role="user", content=request.query)
        self.memory_store.remember(
            session_id=session_id,
            role="assistant",
            content=writer_payload["executive_summary"],
        )
        self.memory_store.store_run(
            run_id=run_id,
            session_id=session_id,
            query=request.query,
            executive_summary=writer_payload["executive_summary"],
        )

        response = ResearchResponse(
            run_id=run_id,
            session_id=session_id,
            executive_summary=writer_payload["executive_summary"],
            report_markdown=writer_payload["report_markdown"],
            plan=planner_payload["plan"],
            topic_map=researcher_payload["topic_map"],
            key_findings=writer_payload["key_findings"],
            risks=critic_payload["risks"],
            next_steps=writer_payload["next_steps"],
            sources=researcher_payload["sources"],
            agent_traces=[planner_trace, researcher_trace, critic_trace, writer_trace],
            evaluation=evaluation,
            memory_snapshot=self.memory_store.recent(session_id=session_id, limit=8),
        )

        LOGGER.info(
            "Research run completed",
            extra={"extra_payload": {"run_id": run_id, "session_id": session_id}},
        )
        return response
