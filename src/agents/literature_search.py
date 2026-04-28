from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from src.agents.base import BaseAgent
from src.models.schemas import PaperRecord, ResearchRequest, SearchQueryPlan, SourceName
from src.tools.base import BaseAcademicClient


class LiteratureSearchAgent(BaseAgent):
    name = "Literature Search Agent"

    def __init__(
        self,
        source_clients: Mapping[SourceName, BaseAcademicClient],
        mock_external_apis: bool = False,
    ) -> None:
        self.source_clients = source_clients
        self.mock_external_apis = mock_external_apis

    async def _run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        request: ResearchRequest = state["request"]
        query_plan: SearchQueryPlan = state["query_plan"]

        if self.mock_external_apis:
            papers = self._load_mock_papers(request.paper_limit)
            return {
                "retrieved_papers": papers,
                "_trace_details": [
                    f"Loaded {len(papers)} mock papers for offline development.",
                ],
            }

        sources = list(dict.fromkeys(request.sources + query_plan.recommended_sources))
        queries = query_plan.search_queries[:3] or [request.topic]

        tasks = []
        task_labels = []
        for source in sources:
            client = self.source_clients.get(source)
            if client is None:
                continue
            for query in queries:
                tasks.append(client.search(query, request))
                task_labels.append(f"{source.value}:{query}")

        results: List[PaperRecord] = []
        details: List[str] = []
        for label, outcome in zip(task_labels, await asyncio.gather(*tasks, return_exceptions=True)):
            if isinstance(outcome, Exception):
                details.append(f"{label} failed: {outcome}")
                continue
            details.append(f"{label} returned {len(outcome)} papers.")
            results.extend(outcome)

        return {
            "retrieved_papers": results,
            "_trace_details": details or ["No sources returned results."],
        }

    def _load_mock_papers(self, limit: int) -> List[PaperRecord]:
        path = Path("samples/mock/mock_papers.json")
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        papers = [PaperRecord.model_validate(item) for item in payload]
        return papers[:limit]
