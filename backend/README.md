# Backend

FastAPI backend for Atlas NLP Research Radar.

## Responsibilities

- agent orchestration
- scholarly paper retrieval
- local RAG ingestion and search
- memory and recent-run storage
- evaluation metrics
- optional OpenAI structured-output generation

## Run

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Key environment variables

- `SCHOLARLY_SEARCH_PROVIDERS`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `EMBEDDING_PROVIDER`
- `OPENAI_EMBEDDING_MODEL`
