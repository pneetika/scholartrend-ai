# ScholarTrend AI

ScholarTrend AI is a multi-agent LLM research assistant that discovers recent scholarly papers, ranks the most relevant evidence, summarizes key workstreams, clusters emerging themes, and produces executive-ready research briefs with citations.

It is designed as a resume-grade systems project that demonstrates:

- multi-agent orchestration with LangGraph
- retrieval-augmented generation over paper abstracts
- hybrid search and ranking across academic APIs
- grounded summarization with critic validation
- FastAPI backend plus Streamlit frontend
- LLM provider switching across OpenAI, Anthropic, and Ollama

## Key Features

- Query Planner Agent expands a user topic into domain-aware academic queries.
- Literature Search Agent retrieves papers from arXiv, Semantic Scholar, Crossref, OpenAlex, and PubMed when relevant.
- Relevance Ranking Agent applies hybrid ranking using semantic similarity, recency, keyword overlap, citation signal, and source credibility.
- Paper Summarization Agent extracts problem, method, datasets, findings, limitations, and future work.
- Trend Discovery Agent clusters papers into themes and identifies repeated methods and research gaps.
- Critic / Validation Agent checks grounding, citation completeness, and weak claims.
- Report Writer Agent composes a structured research trend brief in Markdown and PDF.

## Repository Structure

```text
src/
  agents/
  api/
  evaluation/
  models/
  providers/
  retrieval/
  storage/
  tools/
  utils/
  workflows/
tests/
frontend/
notebooks/
docs/
samples/
```

## Local Setup

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn src.api.main:app --reload
streamlit run frontend/app.py
```

The FastAPI server runs on `http://127.0.0.1:8000` by default and the Streamlit app runs on `http://127.0.0.1:8501`.

## API Quick Start

Sample request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/research/report \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Agentic AI in financial services",
    "time_range": "1y",
    "paper_limit": 12,
    "sources": ["arxiv", "semantic_scholar", "crossref", "openalex"],
    "llm_provider": "mock"
  }'
```

See [docs/api.md](/Users/shailendra/Documents/New%20project/docs/api.md:1) for full request and response documentation.

## Sample Output

- Sample report: [samples/reports/agentic_ai_financial_services.md](/Users/shailendra/Documents/New%20project/samples/reports/agentic_ai_financial_services.md:1)
- Sample API response: [samples/api/sample_response.json](/Users/shailendra/Documents/New%20project/samples/api/sample_response.json:1)

## Architecture

- Architecture diagram: [docs/architecture.md](/Users/shailendra/Documents/New%20project/docs/architecture.md:1)
- System design: [docs/system_design.md](/Users/shailendra/Documents/New%20project/docs/system_design.md:1)

## Resume Talking Points

- Built a multi-agent LLM research assistant using LangGraph, hybrid scholarly retrieval, semantic ranking, and RAG over paper abstracts to identify emerging research trends.
- Implemented query planning, literature retrieval, deduplication, ranking, grounded summarization, critic validation, and trend clustering agents in Python.
- Designed an LLM provider abstraction to switch between OpenAI, Anthropic, Ollama, and deterministic mock mode for local development.
- Developed a FastAPI backend, Streamlit frontend, SQLite-backed caching and metadata persistence, Markdown/PDF report export, and CI-ready pytest suite.

## Interview Explanation

ScholarTrend AI is structured as a stateful research pipeline instead of a single prompt. The workflow starts with topic expansion and academic source selection, then gathers papers asynchronously from multiple APIs, deduplicates them, ranks them with both semantic and symbolic signals, summarizes each paper in a grounded format, clusters themes with embeddings, and finally asks a critic stage to verify that the brief is still supported by retrieved evidence. The report writer is intentionally downstream of validation so the final business-facing brief is built on curated evidence rather than raw search output.

From a systems-design angle, the project shows how to separate orchestration, provider abstractions, retrieval, ranking, evaluation, and presentation layers. That separation makes it easier to swap LLMs, add sources, or move from SQLite to Postgres without rewriting the full pipeline.

## Future Enhancements

- Add authenticated multi-user workspaces and saved research collections.
- Support background jobs with Celery or Arq for large literature reviews.
- Add real citation graph analytics using OpenAlex related-work endpoints.
- Introduce human approval checkpoints directly inside the LangGraph workflow.
- Expand evaluation with graded relevance judgments and summary-faithfulness benchmarks.
- Add benchmark dashboards for trend quality over time.
