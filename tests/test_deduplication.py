from __future__ import annotations

from copy import deepcopy

from src.retrieval.deduplication import deduplicate_papers


def test_deduplicate_papers_prefers_richer_abstract(sample_papers):
    duplicate = deepcopy(sample_papers[0])
    duplicate.abstract = sample_papers[0].abstract + " Additional details."
    duplicate.doi = sample_papers[0].doi
    papers = [sample_papers[0], duplicate, sample_papers[1]]

    result = deduplicate_papers(papers)

    assert len(result) == 2
    assert any("Additional details" in paper.abstract for paper in result)
