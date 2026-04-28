# API Documentation

## Base URL

`http://127.0.0.1:8000/api/v1`

## Endpoints

### `GET /health`

Returns service health and configuration summary.

### `GET /sources`

Returns the supported scholarly sources and whether they are enabled.

### `POST /research/report`

Runs the full multi-agent workflow.

#### Request body

```json
{
  "topic": "Agentic AI in financial services",
  "time_range": "1y",
  "paper_limit": 12,
  "sources": ["arxiv", "semantic_scholar", "crossref", "openalex"],
  "llm_provider": "mock",
  "require_human_review": false
}
```

#### Response fields

- `run_id`
- `topic`
- `executive_summary`
- `themes`
- `top_papers`
- `paper_summaries`
- `methods_and_techniques`
- `research_gaps`
- `business_implications`
- `references`
- `evaluation`
- `agent_steps`
- `report_markdown`
- `report_pdf_path`

### `GET /reports/{run_id}`

Returns the previously stored report payload.

### `GET /reports/{run_id}/markdown`

Downloads the Markdown artifact.

### `GET /reports/{run_id}/pdf`

Downloads the PDF artifact.
