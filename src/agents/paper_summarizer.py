from __future__ import annotations

import re
from typing import Any, Dict, List

from src.agents.base import BaseAgent
from src.models.schemas import PaperSummary, RankedPaper
from src.providers.llm import BaseLLMProvider


class PaperSummarizationAgent(BaseAgent):
    name = "Paper Summarization Agent"

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self.llm_provider = llm_provider

    async def _run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ranked_papers: List[RankedPaper] = state.get("ranked_papers", [])
        summaries = [self._heuristic_summary(item) for item in ranked_papers]
        return {
            "paper_summaries": summaries,
            "_trace_details": [
                f"Generated grounded summaries for {len(summaries)} ranked papers.",
            ],
        }

    def _heuristic_summary(self, ranked_paper: RankedPaper) -> PaperSummary:
        paper = ranked_paper.paper
        sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", paper.abstract) if segment.strip()]
        problem = sentences[0] if sentences else f"This paper studies {paper.title}."
        method = self._find_sentence(sentences, ["propose", "present", "introduce", "method", "approach", "framework"])
        dataset = self._find_sentence(sentences, ["dataset", "benchmark", "corpus", "evaluation", "experiment"])
        findings = self._find_sentence(sentences, ["result", "improve", "outperform", "show", "achieve"])
        limitations = self._find_sentence(sentences, ["limitation", "however", "challenge", "cost", "constraint"])
        future_work = self._find_sentence(sentences, ["future", "further", "next", "extension"])

        return PaperSummary(
            paper_id=paper.paper_id,
            title=paper.title,
            problem=problem,
            method=method or "The abstract does not explicitly describe the method in a single sentence.",
            dataset=dataset or "Dataset details are not explicit in the retrieved abstract.",
            findings=findings or "The abstract suggests promising results but does not provide a concise finding sentence.",
            limitations=limitations or "Limitations are not clearly stated in the retrieved abstract.",
            future_work=future_work or "Future work is not explicitly described in the retrieved abstract.",
            short_summary=" ".join(sentences[:2]) if sentences else paper.title,
            grounded=bool(paper.abstract.strip()),
            citations=[paper.url or "", paper.doi or ""],
        )

    def _find_sentence(self, sentences: List[str], keywords: List[str]) -> str:
        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in keywords):
                return sentence
        return ""
