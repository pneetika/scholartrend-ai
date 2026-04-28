# System Design

## Objectives

ScholarTrend AI is designed to answer one central question: what is happening right now in a research area, and which papers best explain it?

The system prioritizes:

- recent literature coverage
- explainable ranking
- grounded summaries
- modular agent boundaries
- provider flexibility
- local reproducibility

## Core Components

### 1. Orchestration Layer

`src/workflows/research_graph.py` uses LangGraph to define the multi-agent execution graph. Each node is an agent stage with structured state updates.

### 2. Academic Retrieval Layer

`src/tools/` contains API clients for:

- arXiv
- Semantic Scholar
- Crossref
- OpenAlex
- PubMed

These clients share consistent request, retry, parsing, and normalization behavior.

### 3. Ranking and Retrieval Layer

The ranking pipeline combines:

- semantic similarity between topic and paper text
- keyword overlap
- recency score
- citation score
- source credibility score

Abstracts are then indexed into a Chroma-backed vector store for local retrieval over the discovered evidence set.

### 4. LLM Provider Abstraction

`src/providers/llm.py` defines a provider interface for:

- OpenAI
- Anthropic
- Ollama
- deterministic mock mode

This abstraction keeps prompts and agent logic independent from any single model vendor.

### 5. Persistence Layer

SQLite stores:

- cached API responses
- research run metadata
- serialized report outputs
- evaluation metrics

Markdown and PDF artifacts are stored on disk.

### 6. Presentation Layer

FastAPI exposes the research workflow programmatically, while Streamlit provides a lightweight interactive UI for researchers, hiring managers, and demos.

## Design Choices

### Why LangGraph

LangGraph is used because the project is a stateful, multi-step research workflow rather than a single stateless prompt. It makes agent boundaries explicit and easier to reason about in interviews.

### Why Multiple Scholarly Sources

No single source covers all research equally well. arXiv is strong for recency, Semantic Scholar adds metadata and citation signals, Crossref helps with DOI and venue coverage, OpenAlex broadens discovery, and PubMed improves healthcare literature coverage.

### Why Hybrid Ranking

Pure semantic similarity can over-rank generic papers. Pure keyword ranking can miss conceptually relevant work. Hybrid ranking keeps the system more explainable and robust.
