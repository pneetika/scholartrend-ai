from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.schemas.common import HealthResponse
from app.services.container import ServiceContainer

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(container: ServiceContainer = Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=container.settings.app_env,
        timestamp=datetime.now(timezone.utc),
    )

