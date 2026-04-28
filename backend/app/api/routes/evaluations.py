from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.schemas.research import EvaluationMetrics, EvaluationRequest
from app.services.container import ServiceContainer

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/score", response_model=EvaluationMetrics)
async def score_report(
    payload: EvaluationRequest,
    container: ServiceContainer = Depends(get_container),
) -> EvaluationMetrics:
    return container.evaluation_service.score(
        plan=payload.plan,
        findings=payload.findings,
        risks=payload.risks,
        sources=payload.sources,
    )

