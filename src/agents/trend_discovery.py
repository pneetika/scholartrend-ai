from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from src.agents.base import BaseAgent
from src.models.schemas import PaperSummary, RankedPaper, ThemeCluster
from src.retrieval.embeddings import EmbeddingService


class TrendDiscoveryAgent(BaseAgent):
    name = "Trend Discovery Agent"

    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service

    async def _run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ranked_papers: List[RankedPaper] = state.get("ranked_papers", [])
        summaries: List[PaperSummary] = state.get("paper_summaries", [])
        if not ranked_papers:
            return {"themes": [], "_trace_details": ["No ranked papers available for clustering."]}

        texts = [f"{paper.paper.title}. {summary.short_summary}" for paper, summary in zip(ranked_papers, summaries)]
        embeddings = await self.embedding_service.embed_texts(texts)
        clusters = self._cluster_texts(embeddings, ranked_papers, summaries)
        methods = self._collect_methods(summaries)
        gaps = self._collect_gaps(summaries)

        return {
            "themes": clusters,
            "methods_and_techniques": methods,
            "research_gaps": gaps,
            "_trace_details": [
                f"Clustered {len(ranked_papers)} papers into {len(clusters)} themes.",
                f"Extracted {len(methods)} repeated methods and {len(gaps)} candidate research gaps.",
            ],
        }

    def _cluster_texts(
        self,
        embeddings: List[List[float]],
        ranked_papers: List[RankedPaper],
        summaries: List[PaperSummary],
    ) -> List[ThemeCluster]:
        total = len(embeddings)
        if total == 1:
            return [
                ThemeCluster(
                    theme_id="theme-1",
                    label="Single Emerging Direction",
                    description="Only one paper cluster is available, so the theme is based on the strongest retrieved paper.",
                    representative_paper_ids=[ranked_papers[0].paper.paper_id],
                    repeated_methods=[summaries[0].method],
                    evaluation_patterns=[summaries[0].dataset],
                    research_gaps=[summaries[0].limitations],
                    trend_signal="emerging",
                )
            ]

        cluster_count = min(max(2, total // 4 + 1), 4, total)
        model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        labels = model.fit_predict(np.array(embeddings))
        grouped_indices = defaultdict(list)
        for idx, label in enumerate(labels):
            grouped_indices[int(label)].append(idx)

        vectorizer = TfidfVectorizer(stop_words="english", max_features=12)
        themes = []
        for cluster_number, indices in grouped_indices.items():
            cluster_texts = [ranked_papers[idx].paper.title + " " + summaries[idx].short_summary for idx in indices]
            matrix = vectorizer.fit_transform(cluster_texts)
            terms = vectorizer.get_feature_names_out()
            weights = np.asarray(matrix.mean(axis=0)).ravel()
            top_terms = [terms[idx] for idx in weights.argsort()[::-1][:3] if idx < len(terms)]
            label = " / ".join(term.title() for term in top_terms) or f"Theme {cluster_number + 1}"
            papers = [ranked_papers[idx] for idx in indices]
            theme_summaries = [summaries[idx] for idx in indices]
            trend_signal = self._trend_signal(papers)
            themes.append(
                ThemeCluster(
                    theme_id=f"theme-{cluster_number + 1}",
                    label=label,
                    description=f"This cluster groups {len(indices)} papers around {label.lower()} and related methods.",
                    representative_paper_ids=[paper.paper.paper_id for paper in papers[:3]],
                    repeated_methods=self._most_common([item.method for item in theme_summaries]),
                    evaluation_patterns=self._most_common([item.dataset for item in theme_summaries]),
                    research_gaps=self._most_common([item.limitations for item in theme_summaries]),
                    trend_signal=trend_signal,
                )
            )
        return sorted(themes, key=lambda theme: theme.label)

    def _most_common(self, values: List[str]) -> List[str]:
        normalized = [value for value in values if value and "not explicit" not in value.lower()]
        counts = Counter(normalized)
        return [value for value, _ in counts.most_common(3)]

    def _trend_signal(self, papers: List[RankedPaper]) -> str:
        recent_count = 0
        citation_signal = 0
        for item in papers:
            if item.paper.publication_date:
                age_days = (datetime.utcnow().date() - item.paper.publication_date).days
                if age_days <= 180:
                    recent_count += 1
            citation_signal += item.paper.citation_count or 0
        if recent_count >= max(1, len(papers) - 1):
            return "emerging"
        if citation_signal >= 50:
            return "established"
        return "accelerating"

    def _collect_methods(self, summaries: List[PaperSummary]) -> List[str]:
        return self._most_common([summary.method for summary in summaries])[:6]

    def _collect_gaps(self, summaries: List[PaperSummary]) -> List[str]:
        return self._most_common([summary.limitations for summary in summaries] + [summary.future_work for summary in summaries])[:6]
