from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SourceName(str, Enum):
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    CROSSREF = "crossref"
    OPENALEX = "openalex"
    PUBMED = "pubmed"
    PAPERS_WITH_CODE = "papers_with_code"


class LLMProviderName(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    MOCK = "mock"


class TimeRange(str, Enum):
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"
    THREE_YEARS = "3y"
    CUSTOM = "custom"


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=5, max_length=300)
    time_range: TimeRange = TimeRange.ONE_YEAR
    paper_limit: int = Field(default=12, ge=3, le=50)
    sources: List[SourceName] = Field(
        default_factory=lambda: [
            SourceName.ARXIV,
            SourceName.SEMANTIC_SCHOLAR,
            SourceName.CROSSREF,
            SourceName.OPENALEX,
        ]
    )
    custom_start_date: Optional[date] = None
    custom_end_date: Optional[date] = None
    llm_provider: Optional[LLMProviderName] = None
    require_human_review: bool = False


class PaperAuthor(BaseModel):
    name: str
    affiliation: Optional[str] = None


class PaperRecord(BaseModel):
    paper_id: str
    title: str
    abstract: str = ""
    authors: List[PaperAuthor] = Field(default_factory=list)
    source: SourceName
    source_rank: Optional[int] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    publication_date: Optional[date] = None
    citation_count: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    raw_metadata: Dict[str, object] = Field(default_factory=dict)


class RankedPaper(BaseModel):
    paper: PaperRecord
    relevance_score: float
    semantic_score: float
    keyword_score: float
    recency_score: float
    citation_score: float
    credibility_score: float
    rationale: str


class PaperSummary(BaseModel):
    paper_id: str
    title: str
    problem: str
    method: str
    dataset: str
    findings: str
    limitations: str
    future_work: str
    short_summary: str
    grounded: bool = True
    citations: List[str] = Field(default_factory=list)


class ThemeCluster(BaseModel):
    theme_id: str
    label: str
    description: str
    representative_paper_ids: List[str] = Field(default_factory=list)
    repeated_methods: List[str] = Field(default_factory=list)
    evaluation_patterns: List[str] = Field(default_factory=list)
    research_gaps: List[str] = Field(default_factory=list)
    trend_signal: str


class ValidationIssue(BaseModel):
    severity: str
    message: str
    paper_id: Optional[str] = None


class AgentStepTrace(BaseModel):
    agent_name: str
    started_at: datetime
    completed_at: datetime
    status: str
    details: List[str] = Field(default_factory=list)


class EvaluationMetrics(BaseModel):
    source_diversity: float
    citation_completeness: float
    grounding_score: float
    theme_diversity: float
    overall_score: float
    notes: List[str] = Field(default_factory=list)


class ReferenceEntry(BaseModel):
    title: str
    url: Optional[str] = None
    doi: Optional[str] = None
    source: SourceName


class ResearchReport(BaseModel):
    run_id: str
    topic: str
    generated_at: datetime
    executive_summary: str
    key_research_themes: List[ThemeCluster] = Field(default_factory=list)
    recent_trends: List[str] = Field(default_factory=list)
    top_papers: List[RankedPaper] = Field(default_factory=list)
    paper_summaries: List[PaperSummary] = Field(default_factory=list)
    methods_and_techniques: List[str] = Field(default_factory=list)
    research_gaps: List[str] = Field(default_factory=list)
    business_implications: List[str] = Field(default_factory=list)
    references: List[ReferenceEntry] = Field(default_factory=list)
    validation_issues: List[ValidationIssue] = Field(default_factory=list)
    evaluation: EvaluationMetrics
    agent_steps: List[AgentStepTrace] = Field(default_factory=list)
    report_markdown: str
    report_pdf_path: Optional[str] = None
    human_review_required: bool = False


class SourceStatus(BaseModel):
    source: SourceName
    enabled: bool
    notes: str


class HealthResponse(BaseModel):
    app_name: str
    environment: str
    llm_provider: str
    vector_backend: str
    timestamp: datetime


class SearchQueryPlan(BaseModel):
    domains: List[str] = Field(default_factory=list)
    keyword_variants: List[str] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)
    recommended_sources: List[SourceName] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
