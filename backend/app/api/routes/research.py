from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.container import ServiceContainer

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/run", response_model=ResearchResponse)
async def run_research(
    payload: ResearchRequest,
    container: ServiceContainer = Depends(get_container),
) -> ResearchResponse:
    return await container.orchestrator.run(payload)

