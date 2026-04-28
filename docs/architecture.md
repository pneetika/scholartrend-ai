# Architecture

## Overview

Atlas is a multi-agent NLP research assistant with two main surfaces:

- `backend/`: FastAPI API for retrieval, orchestration, memory, and report generation
- `frontend/`: React dashboard for running research workflows and inspecting outputs

The design intentionally shows portfolio-friendly concepts:

- multi-agent decomposition
- retrieval-augmented generation
- scholarly aggregation
- optional LLM structured outputs
- lightweight evaluation and memory

## Request flow

1. A user submits a research question from the dashboard.
2. `PlannerAgent` converts the question into:
   - a report title
   - a short research plan
   - provider-friendly search queries
   - focus areas
3. `ResearcherAgent` gathers evidence from:
   - arXiv
   - Semantic Scholar
   - Crossref
   - uploaded documents indexed in the local vector store
4. `CriticAgent` checks freshness, evidence diversity, grounding, and source bias.
5. `WriterAgent` returns:
   - executive summary
   - topic radar
   - markdown brief
   - next steps
6. The run is stored in SQLite memory for lightweight session continuity.

## Agents

### Planner

- Uses OpenAI structured outputs when `OPENAI_API_KEY` is present.
- Falls back to deterministic heuristics when running offline.
- Focuses on recent NLP research rather than generic web planning.

### Researcher

- Queries multiple scholarly providers concurrently.
- Deduplicates papers by DOI, URL, or title fingerprint.
- Adds supporting local RAG passages from uploaded files.
- Produces topic clusters and early findings.

### Critic

- Flags narrow evidence pools, stale papers, preprint-heavy runs, and missing uploaded context.
- Suggests validation steps before the brief is treated as final.

### Writer

- Produces a portfolio-grade research brief.
- Emphasizes what is active now in NLP, not only static background.

## Retrieval stack

### Local RAG

- Uploaded files are stored under `backend/data/uploads/`
- `TextChunker` splits content into overlapping passages
- `FileVectorStore` persists embeddings and chunk metadata as JSON

### Embeddings

- `hash` mode: dependency-light fallback for local demos
- `openai` mode: optional hosted embeddings via `text-embedding-3-small`

This makes the project easy to run offline while still showing how a production-grade embedding layer would plug in.

## LLM layer

The project uses OpenAI's `Responses` API pattern for structured outputs when enabled.

Current LLM tasks:

- plan generation
- topic extraction
- critique generation
- report writing

If no API key is provided, the app remains functional through heuristic fallbacks.

## Storage

- `backend/data/vector_store.json`: persisted chunk embeddings and document metadata
- `backend/data/memory.db`: SQLite store for session memory and recent runs
- `backend/data/logs/app.log`: application logs

## Why this architecture works for a resume project

- It is concrete enough to run locally.
- It demonstrates practical LLM system design, not just prompting.
- It includes both live retrieval and local-document grounding.
- It separates orchestration, retrieval, critique, and synthesis into understandable components.
