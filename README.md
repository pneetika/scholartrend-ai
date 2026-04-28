# Atlas NLP Research Radar

Atlas is a resume-ready multi-agent research assistant for tracking recent NLP topics. It combines scholarly search, local-document RAG, short-term memory, evaluation metrics, and an optional OpenAI synthesis layer to explain what researchers are working on right now.

## What it demonstrates

- Multi-agent orchestration with `Planner`, `Researcher`, `Critic`, and `Writer` agents.
- Retrieval-augmented generation over uploaded PDFs, notes, and local files.
- Scholarly aggregation from arXiv, Semantic Scholar, and Crossref.
- Optional OpenAI structured outputs for planning, topic extraction, critique, and report writing.
- A frontend dashboard for running research workflows and reviewing results.

## Repo layout

- `backend/`: FastAPI service, agent orchestration, RAG, memory, and evaluation.
- `frontend/`: React + TypeScript dashboard for submitting queries and reading reports.
- `docs/architecture.md`: high-level system design and request flow.
- `evals/`: starter evaluation scenarios for future quality checks.
- `fine_tuning/`: placeholder assets for later supervised tuning experiments.

## How the workflow works

1. The `Planner` turns the user question into focus areas and paper-search queries.
2. The `Researcher` gathers recent papers plus supporting passages from uploaded documents.
3. The `Critic` checks for weak evidence, stale sources, and overclaiming.
4. The `Writer` produces a markdown brief with a topic radar, evidence base, and next steps.

## Running locally

### 1. Environment

Create a `.env` file from `.env.example`.

Important settings:

- `SCHOLARLY_SEARCH_PROVIDERS=arxiv,semantic_scholar,crossref`
- `OPENAI_API_KEY=` to enable structured-output planning and synthesis
- `EMBEDDING_PROVIDER=hash` for offline local demos, or `openai` for hosted embeddings

### 2. Backend

```bash
cd backend
python3 -m pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

### 4. Docker

```bash
docker compose up --build
```

## Suggested demo flow

1. Upload 1-2 survey papers or lab notes in PDF or Markdown format.
2. Ask a question such as:
   - `What recent topics are researchers actively exploring in NLP around reasoning, tool use, and retrieval-augmented generation?`
   - `Summarize recent multilingual NLP trends and open evaluation gaps.`
3. Review the generated `Topic Radar`, risks, and evidence base.

## Resume pitch

If you want to describe this project on your resume or LinkedIn, a concise version could be:

> Built a multi-agent NLP research assistant with FastAPI + React that aggregates recent papers from scholarly APIs, applies RAG over uploaded documents, and uses structured LLM outputs to generate evidence-grounded research briefings.
