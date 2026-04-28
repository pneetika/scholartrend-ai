from __future__ import annotations

import argparse
import asyncio

from src.api.deps import build_container
from src.models.schemas import LLMProviderName, ResearchRequest, SourceName, TimeRange
from src.utils.config import get_settings


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run ScholarTrend AI from the command line.")
    parser.add_argument("topic", help="Research topic")
    parser.add_argument("--provider", default="mock", choices=[item.value for item in LLMProviderName])
    parser.add_argument("--paper-limit", type=int, default=10)
    args = parser.parse_args()

    settings = get_settings()
    container = build_container(settings)
    try:
        report = await container.workflow.run(
            ResearchRequest(
                topic=args.topic,
                paper_limit=args.paper_limit,
                llm_provider=LLMProviderName(args.provider),
                time_range=TimeRange.ONE_YEAR,
                sources=[
                    SourceName.ARXIV,
                    SourceName.SEMANTIC_SCHOLAR,
                    SourceName.CROSSREF,
                    SourceName.OPENALEX,
                ],
            )
        )
        print(report.report_markdown)
    finally:
        await container.aclose()


if __name__ == "__main__":
    asyncio.run(main())
