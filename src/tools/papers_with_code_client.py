from __future__ import annotations

from pathlib import Path
from typing import List

from src.models.schemas import PaperRecord, ResearchRequest, SourceName
from src.tools.base import BaseAcademicClient


class PapersWithCodeClient(BaseAcademicClient):
    source_name = SourceName.PAPERS_WITH_CODE

    async def search(self, query: str, request: ResearchRequest) -> List[PaperRecord]:
        mock_path = Path("samples/mock/papers_with_code_mock.json")
        if not mock_path.exists():
            return []
        return []
