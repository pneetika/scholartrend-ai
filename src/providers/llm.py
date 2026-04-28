from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from src.models.schemas import LLMProviderName
from src.utils.config import Settings
from src.utils.logging import get_logger

LOGGER = get_logger(__name__)


class BaseLLMProvider(ABC):
    provider_name = "base"

    @abstractmethod
    async def generate_json(
        self,
        *,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: str,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_text(self, *, prompt: str, system_prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    async def aclose(self) -> None:
        return None


class MockLLMProvider(BaseLLMProvider):
    provider_name = "mock"

    async def generate_json(
        self,
        *,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: str,
    ) -> Dict[str, Any]:
        lowered = prompt.lower()
        keywords = sorted({token for token in re.findall(r"[a-zA-Z][a-zA-Z\-]+", lowered) if len(token) > 4})
        if "search queries" in lowered or "academic" in system_prompt.lower():
            return {
                "domains": keywords[:4],
                "keyword_variants": keywords[:6],
                "search_queries": [
                    " ".join(keywords[:3]) or "language models research",
                    "recent " + (" ".join(keywords[:2]) or "AI systems"),
                    "evaluation " + (" ".join(keywords[:2]) or "retrieval generation"),
                ],
                "recommended_sources": ["arxiv", "semantic_scholar", "crossref", "openalex"],
                "notes": ["Mock planner output generated without an external LLM."],
            }

        return {}

    async def generate_text(self, *, prompt: str, system_prompt: str) -> str:
        return f"Mock response generated for prompt: {prompt[:180]}"

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            vector = [0.0] * 16
            for token in re.findall(r"[a-zA-Z0-9']+", text.lower()):
                vector[hash(token) % 16] += 1.0
            norm = sum(value * value for value in vector) ** 0.5 or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, model: str, embedding_model: str, timeout_seconds: int) -> None:
        self.model = model
        self.embedding_model = embedding_model
        self.client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def generate_json(
        self,
        *,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: str,
    ) -> Dict[str, Any]:
        response = await self.client.post(
            "https://api.openai.com/v1/responses",
            json={
                "model": self.model,
                "instructions": system_prompt,
                "input": prompt,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "scholartrend_output",
                        "strict": True,
                        "schema": schema,
                    }
                },
            },
        )
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return json.loads(content.get("text", "{}"))
        return {}

    async def generate_text(self, *, prompt: str, system_prompt: str) -> str:
        response = await self.client.post(
            "https://api.openai.com/v1/responses",
            json={
                "model": self.model,
                "instructions": system_prompt,
                "input": prompt,
            },
        )
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")
        return ""

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.post(
            "https://api.openai.com/v1/embeddings",
            json={"model": self.embedding_model, "input": texts},
        )
        response.raise_for_status()
        payload = response.json()
        return [item["embedding"] for item in payload.get("data", [])]

    async def aclose(self) -> None:
        await self.client.aclose()


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
        self.model = model
        self.client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        self._mock_embedder = MockLLMProvider()

    async def generate_json(
        self,
        *,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: str,
    ) -> Dict[str, Any]:
        message = await self.generate_text(
            prompt=f"{prompt}\n\nReturn JSON matching this schema exactly:\n{json.dumps(schema)}",
            system_prompt=system_prompt,
        )
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            LOGGER.warning("Anthropic provider returned non-JSON text; falling back to empty object.")
            return {}

    async def generate_text(self, *, prompt: str, system_prompt: str) -> str:
        response = await self.client.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model": self.model,
                "max_tokens": 1200,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        payload = response.json()
        texts = [item.get("text", "") for item in payload.get("content", []) if item.get("type") == "text"]
        return "\n".join(texts)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return await self._mock_embedder.embed_texts(texts)

    async def aclose(self) -> None:
        await self.client.aclose()


class OllamaProvider(BaseLLMProvider):
    provider_name = "ollama"

    def __init__(self, base_url: str, model: str, embedding_model: str, timeout_seconds: int) -> None:
        self.model = model
        self.embedding_model = embedding_model
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=timeout_seconds)

    async def generate_json(
        self,
        *,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: str,
    ) -> Dict[str, Any]:
        text = await self.generate_text(
            prompt=f"{prompt}\n\nReturn JSON matching this schema:\n{json.dumps(schema)}",
            system_prompt=system_prompt,
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    async def generate_text(self, *, prompt: str, system_prompt: str) -> str:
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "system": system_prompt,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("response", "")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.post(
            f"{self.base_url}/api/embed",
            json={
                "model": self.embedding_model,
                "input": texts,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("embeddings", [])

    async def aclose(self) -> None:
        await self.client.aclose()


def build_llm_provider(settings: Settings, override: Optional[LLMProviderName] = None) -> BaseLLMProvider:
    provider_name = override or settings.llm_provider
    if provider_name == LLMProviderName.OPENAI and settings.openai_api_key:
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            embedding_model=settings.openai_embedding_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    if provider_name == LLMProviderName.ANTHROPIC and settings.anthropic_api_key:
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    if provider_name == LLMProviderName.OLLAMA:
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            embedding_model=settings.ollama_embedding_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    return MockLLMProvider()
