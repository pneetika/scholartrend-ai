from __future__ import annotations

from dataclasses import dataclass

from app.agents.critic import CriticAgent
from app.agents.orchestrator import ResearchOrchestrator
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.writer import WriterAgent
from app.core.config import Settings
from app.rag.chunking import TextChunker
from app.rag.embeddings import HashingEmbeddingModel, OpenAIEmbeddingModel
from app.rag.pipeline import RAGPipeline
from app.rag.vector_store import FileVectorStore
from app.services.evaluation import EvaluationService
from app.services.llm import StructuredLLMClient
from app.services.memory import MemoryStore
from app.services.search import (
    ArxivSearchProvider,
    CrossrefSearchProvider,
    NullSearchProvider,
    ScholarlySearchService,
    SemanticScholarSearchProvider,
)
from app.services.uploads import UploadService


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    memory_store: MemoryStore
    rag_pipeline: RAGPipeline
    upload_service: UploadService
    search_service: ScholarlySearchService
    evaluation_service: EvaluationService
    llm_service: StructuredLLMClient
    orchestrator: ResearchOrchestrator

    async def aclose(self) -> None:
        await self.search_service.aclose()
        await self.llm_service.aclose()
        close_embedding = getattr(self.rag_pipeline.vector_store.embedding_model, "close", None)
        if callable(close_embedding):
            close_embedding()


def build_container(settings: Settings) -> ServiceContainer:
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        embedding_model = OpenAIEmbeddingModel(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    else:
        embedding_model = HashingEmbeddingModel()

    vector_store = FileVectorStore(path=settings.vector_store_path, embedding_model=embedding_model)
    rag_pipeline = RAGPipeline(chunker=TextChunker(), vector_store=vector_store)
    memory_store = MemoryStore(db_path=settings.memory_db_path)
    llm_service = StructuredLLMClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        timeout_seconds=settings.request_timeout_seconds,
    )
    providers = []
    for provider_name in settings.search_providers:
        if provider_name == "arxiv":
            providers.append(ArxivSearchProvider(timeout_seconds=settings.request_timeout_seconds))
        elif provider_name == "semantic_scholar":
            providers.append(
                SemanticScholarSearchProvider(
                    timeout_seconds=settings.request_timeout_seconds,
                    api_key=settings.semantic_scholar_api_key,
                )
            )
        elif provider_name == "crossref":
            providers.append(
                CrossrefSearchProvider(
                    timeout_seconds=settings.request_timeout_seconds,
                    mailto=settings.crossref_mailto,
                )
            )
        elif provider_name == "disabled":
            providers.append(NullSearchProvider())
    if not providers:
        providers.append(NullSearchProvider())

    search_service = ScholarlySearchService(providers=providers)
    evaluation_service = EvaluationService()
    upload_service = UploadService(settings=settings, rag_pipeline=rag_pipeline)

    orchestrator = ResearchOrchestrator(
        planner=PlannerAgent(llm=llm_service),
        researcher=ResearcherAgent(
            search_service=search_service,
            rag_pipeline=rag_pipeline,
            default_top_k=settings.retrieval_top_k,
            llm=llm_service,
        ),
        critic=CriticAgent(llm=llm_service),
        writer=WriterAgent(llm=llm_service),
        memory_store=memory_store,
        evaluation_service=evaluation_service,
    )

    return ServiceContainer(
        settings=settings,
        memory_store=memory_store,
        rag_pipeline=rag_pipeline,
        upload_service=upload_service,
        search_service=search_service,
        evaluation_service=evaluation_service,
        llm_service=llm_service,
        orchestrator=orchestrator,
    )
