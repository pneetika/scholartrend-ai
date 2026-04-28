from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from src.api.deps import AppContainer, build_container
from src.models.schemas import HealthResponse, ResearchRequest, ResearchReport, SourceName, SourceStatus
from src.utils.config import get_settings
from src.utils.logging import configure_logging
from src.utils.report_export import markdown_to_pdf

settings = get_settings()
configure_logging(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = build_container(settings)
    app.state.container = container
    yield
    await container.aclose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_container() -> AppContainer:
    return app.state.container


@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        app_name=settings.app_name,
        environment=settings.app_env,
        llm_provider=settings.llm_provider.value,
        vector_backend=settings.vector_backend,
        timestamp=datetime.utcnow(),
    )


@app.get("/api/v1/sources", response_model=list[SourceStatus])
async def list_sources() -> list[SourceStatus]:
    return [
        SourceStatus(source=SourceName.ARXIV, enabled=True, notes="Open preprint API."),
        SourceStatus(source=SourceName.SEMANTIC_SCHOLAR, enabled=True, notes="Adds citation and metadata signals."),
        SourceStatus(source=SourceName.CROSSREF, enabled=True, notes="Strong DOI and venue coverage."),
        SourceStatus(source=SourceName.OPENALEX, enabled=True, notes="Broad academic discovery API."),
        SourceStatus(source=SourceName.PUBMED, enabled=True, notes="Used for healthcare and biomedical queries."),
        SourceStatus(source=SourceName.PAPERS_WITH_CODE, enabled=False, notes="Reserved for compliant mock or future supported API integration."),
    ]


@app.post("/api/v1/research/report", response_model=ResearchReport)
async def create_report(payload: ResearchRequest) -> ResearchReport:
    container = get_container()
    active_container = container
    if payload.llm_provider and payload.llm_provider != container.settings.llm_provider:
        temporary_settings = container.settings.model_copy(update={"llm_provider": payload.llm_provider})
        active_container = build_container(temporary_settings)
    try:
        report = await active_container.workflow.run(payload)
    finally:
        if active_container is not container:
            await active_container.aclose()
    pdf_path = settings.reports_dir / f"{report.run_id}.pdf"
    markdown_to_pdf(report.report_markdown, pdf_path)
    report.report_pdf_path = str(pdf_path)
    container.run_store.save_run(report.run_id, report.topic, report.model_dump(mode="json"))
    return report


@app.get("/api/v1/reports/{run_id}", response_model=ResearchReport)
async def get_report(run_id: str) -> ResearchReport:
    container = get_container()
    payload = container.run_store.get_run(run_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return ResearchReport.model_validate(payload)


@app.get("/api/v1/reports/{run_id}/markdown")
async def download_markdown(run_id: str) -> Response:
    container = get_container()
    payload = container.run_store.get_run(run_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Report not found")
    report = ResearchReport.model_validate(payload)
    return Response(
        content=report.report_markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{run_id}.md"'},
    )


@app.get("/api/v1/reports/{run_id}/pdf")
async def download_pdf(run_id: str) -> Response:
    container = get_container()
    payload = container.run_store.get_run(run_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Report not found")
    report = ResearchReport.model_validate(payload)
    pdf_path = Path(report.report_pdf_path) if report.report_pdf_path else settings.reports_dir / f"{run_id}.pdf"
    if not pdf_path.exists():
        markdown_to_pdf(report.report_markdown, pdf_path)
    return Response(
        content=pdf_path.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{run_id}.pdf"'},
    )
