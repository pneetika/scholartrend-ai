from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Tuple

from src.models.schemas import AgentStepTrace


class BaseAgent(ABC):
    name = "Base Agent"

    async def run(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], AgentStepTrace]:
        started_at = datetime.utcnow()
        payload = await self._run(state)
        completed_at = datetime.utcnow()
        trace = AgentStepTrace(
            agent_name=self.name,
            started_at=started_at,
            completed_at=completed_at,
            status="completed",
            details=payload.pop("_trace_details", []),
        )
        return payload, trace

    @abstractmethod
    async def _run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
