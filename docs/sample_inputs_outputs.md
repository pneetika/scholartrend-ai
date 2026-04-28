# Sample Inputs and Outputs

## Example Topics

- Agentic AI in financial services
- LLMs for healthcare summarization
- Retrieval-augmented generation evaluation
- AI agents for sales analytics

## Example CLI Usage

```bash
python -m src.cli "Agentic AI in financial services" --provider mock --paper-limit 10
```

## Example API Usage

Request:

```json
{
  "topic": "Retrieval-augmented generation evaluation",
  "time_range": "1y",
  "paper_limit": 15,
  "sources": ["arxiv", "semantic_scholar", "crossref", "openalex"],
  "llm_provider": "mock"
}
```

Response:

See [samples/api/sample_response.json](/Users/shailendra/Documents/New%20project/samples/api/sample_response.json:1).
