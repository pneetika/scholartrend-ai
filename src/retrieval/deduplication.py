from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple

from src.models.schemas import PaperRecord


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", title.lower())).strip()


def deduplicate_papers(papers: Iterable[PaperRecord]) -> List[PaperRecord]:
    seen: Dict[Tuple[str, str], PaperRecord] = {}
    for paper in papers:
        fingerprint = (
            (paper.doi or "").lower().strip(),
            normalize_title(paper.title),
        )
        existing = seen.get(fingerprint)
        if existing is None:
            seen[fingerprint] = paper
            continue

        if len(paper.abstract) > len(existing.abstract):
            seen[fingerprint] = paper
    return list(seen.values())
