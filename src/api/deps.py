from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from src.agents.critic_validator import CriticValidatorAgent
from src.agents.literature_search import LiteratureSearchAgent
from src.agents.paper_summarizer import PaperSummarizationAgent
from src.agents.query_planner import QueryPlannerAgent
from src.agents.relevance_ranker import RelevanceRankingAgent
from src.agents.report_writer import ReportWriterAgent
from src.agents.trend_discovery import TrendDiscoveryAgent
from src.evaluation.eval_pipeline import EvaluationPipeline
from src.models.schemas import SourceName
from src.providers.llm import build_llm_provider
from src.retrieval.embeddings import EmbeddingService
from src.retrieval.vector_store import build_vector_store
from src.storage.database import RunStore
from src.tools.arxiv_client import ArxivClient
from src.tools.crossref_client import CrossrefClient
from src.tools.openalex_client import OpenAlexClient
from src.tools.papers_with_code_client import PapersWithCodeClient
from src.tools.pubmed_client import PubMedClient
from src.tools.semantic_scholar_client import SemanticScholarClient
from src.utils.cache import ResponseCache
from src.utils.config import Settings
from src.utils.http import AsyncHTTPClient
from src.workflows.research_graph import ScholarTrendResearchGraph


@dataclass
class AppContainer:
    settings: Settings
    http_client: AsyncHTTPClient
    run_store: RunStore
    llm_provider: object
    workflow: ScholarTrendResearchGraph

    async def aclose(self) -> None:
        await self.http_client.aclose()
        close_provider = getattr(self.llm_provider, "aclose", None)
        if callable(close_provider):
            await close_provider()


def build_container(settings: Settings) -> AppContainer:
    cache = ResponseCache(settings.cache_db_path)
    http_client = AsyncHTTPClient(
        timeout_seconds=settings.request_timeout_seconds,
        cache=cache,
        default_headers={
            "User-Agent": f"{settings.app_name}/0.1 ({settings.app_env})",
        },
    )
    llm_provider = build_llm_provider(settings)
    embedding_service = EmbeddingService(settings, llm_provider)
    vector_store = build_vector_store(settings.vector_backend, str(settings.chroma_persist_dir))
    run_store = RunStore(settings.runs_db_path)

    source_clients: Dict[SourceName, object] = {
        SourceName.ARXIV: ArxivClient(http_client),
        SourceName.SEMANTIC_SCHOLAR: SemanticScholarClient(http_client),
        SourceName.CROSSREF: CrossrefClient(http_client),
        SourceName.OPENALEX: OpenAlexClient(http_client),
        SourceName.PUBMED: PubMedClient(http_client),
        SourceName.PAPERS_WITH_CODE: PapersWithCodeClient(http_client),
    }

    workflow = ScholarTrendResearchGraph(
        planner=QueryPlannerAgent(llm_provider),
        search_agent=LiteratureSearchAgent(
            source_clients=source_clients,
            mock_external_apis=settings.mock_external_apis,
        ),
        ranker=RelevanceRankingAgent(embedding_service=embedding_service, vector_store=vector_store),
        summarizer=PaperSummarizationAgent(llm_provider),
        trend_discovery=TrendDiscoveryAgent(embedding_service),
        critic=CriticValidatorAgent(),
        writer=ReportWriterAgent(),
        evaluation_pipeline=EvaluationPipeline(),
    )

    return AppContainer(
        settings=settings,
        http_client=http_client,
        run_store=run_store,
        llm_provider=llm_provider,
        workflow=workflow,
    )
