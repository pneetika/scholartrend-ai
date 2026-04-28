from __future__ import annotations

import json
from pathlib import Path


def build_example(query: str, summary: str) -> dict[str, object]:
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are a research analyst who writes grounded, well-structured answers.",
            },
            {"role": "user", "content": query},
            {"role": "assistant", "content": summary},
        ]
    }


def convert_runs(input_path: Path, output_path: Path) -> None:
    runs = json.loads(input_path.read_text(encoding="utf-8"))
    rows = []

    for run in runs:
        query = run.get("query", "").strip()
        summary = run.get("executive_summary", "").strip()
        if query and summary:
            rows.append(build_example(query, summary))

    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row))
            handle.write("\n")


if __name__ == "__main__":
    source = Path("exported_runs.json")
    target = Path("research_assistant.generated.jsonl")
    convert_runs(source, target)
    print(f"Wrote {target}")

