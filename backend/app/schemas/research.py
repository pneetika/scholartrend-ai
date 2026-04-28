from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import MemoryEntry


class ResearchRequest(BaseModel):
    session_id: str | None = None
    query: str = Field(min_length=6, max_length=1000)
    goals: list[str] = Field(default_factory=list)
    context: str | None = None
    include_web_search: bool = True
    top_k: int | None = Field(default=None, ge=1, le=10)
    recency_days: int = Field(default=365, ge=30, le=3650)


class ResearchSource(BaseModel):
    source_id: str
    title: str
    snippet: str
    url: str | None = None
    source_type: str
    provider: str
    authors: list[str] = Field(default_factory=list)
    venue: str | None = None
    published_at: datetime | None = None
    citation_count: int | None = None
    doi: str | None = None
    paper_id: str | None = None
    relevance_score: float | None = None
    keywords: list[str] = Field(default_factory=list)


class TopicInsight(BaseModel):
    topic: str
    trend_signal: str
    summary: str
    supporting_source_ids: list[str] = Field(default_factory=list)


class AgentTrace(BaseModel):
    name: str
    status: str
    summary: str
    steps: list[str]
    started_at: datetime
    completed_at: datetime


class EvaluationMetrics(BaseModel):
    citation_density: float
    evidence_coverage: float
    critique_score: float
    overall_score: float
    notes: list[str]


class ResearchResponse(BaseModel):
    run_id: str
    session_id: str
    executive_summary: str
    report_markdown: str
    plan: list[str]
    topic_map: list[TopicInsight]
    key_findings: list[str]
    risks: list[str]
    next_steps: list[str]
    sources: list[ResearchSource]
    agent_traces: list[AgentTrace]
    evaluation: EvaluationMetrics
    memory_snapshot: list[MemoryEntry]


class EvaluationRequest(BaseModel):
    plan: list[str]
    findings: list[str]
    risks: list[str] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)
