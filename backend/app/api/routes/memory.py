from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.schemas.common import MemoryEntry
from app.services.container import ServiceContainer

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{session_id}", response_model=list[MemoryEntry])
async def get_memory(
    session_id: str,
    container: ServiceContainer = Depends(get_container),
) -> list[MemoryEntry]:
    return container.memory_store.recent(session_id=session_id, limit=20)


@router.get("/runs/recent", response_model=list[dict[str, str]])
async def recent_runs(container: ServiceContainer = Depends(get_container)) -> list[dict[str, str]]:
    return container.memory_store.recent_runs(limit=12)

