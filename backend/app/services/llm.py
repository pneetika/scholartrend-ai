from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.logging import get_logger

LOGGER = get_logger(__name__)


class StructuredLLMClient:
    endpoint = "https://api.openai.com/v1/responses"

    def __init__(self, api_key: str | None, model: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.model = model
        self.client: httpx.AsyncClient | None = None
        if api_key:
            self.client = httpx.AsyncClient(
                timeout=timeout_seconds,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

    @property
    def is_enabled(self) -> bool:
        return self.client is not None

    async def generate_json(
        self,
        *,
        instructions: str,
        prompt: str,
        schema_name: str,
        schema: dict[str, Any],
        max_output_tokens: int = 1400,
    ) -> dict[str, Any] | None:
        if self.client is None:
            return None

        try:
            response = await self.client.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "instructions": instructions,
                    "input": prompt,
                    "max_output_tokens": max_output_tokens,
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": schema_name,
                            "schema": schema,
                            "strict": True,
                        }
                    },
                },
            )
            response.raise_for_status()
            payload = response.json()
            text = self._extract_output_text(payload)
            if not text:
                return None
            return json.loads(text)
        except Exception as exc:  # pragma: no cover - depends on network/runtime keys
            LOGGER.warning(
                "LLM structured generation failed",
                extra={"extra_payload": {"schema_name": schema_name, "error": str(exc)}},
            )
            return None

    def _extract_output_text(self, payload: dict[str, Any]) -> str:
        output = payload.get("output", [])
        for item in output:
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")
        return ""

    async def aclose(self) -> None:
        if self.client is not None:
            await self.client.aclose()
