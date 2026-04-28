from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.schemas.research import AgentTrace


class BaseAgent(ABC):
    name = "base"

    async def run(self, context: dict[str, Any]) -> tuple[dict[str, Any], AgentTrace]:
        started_at = datetime.now(timezone.utc)
        payload = await self._run(context)
        completed_at = datetime.now(timezone.utc)

        trace = AgentTrace(
            name=self.name,
            status="completed",
            summary=payload.get("summary", ""),
            steps=payload.get("steps", []),
            started_at=started_at,
            completed_at=completed_at,
        )
        return payload, trace

    @abstractmethod
    async def _run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

