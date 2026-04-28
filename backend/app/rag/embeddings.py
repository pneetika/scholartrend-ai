from __future__ import annotations

import math
import re
from typing import Protocol

import httpx


class EmbeddingModel(Protocol):
    def encode(self, text: str) -> list[float]:
        ...


class HashingEmbeddingModel:
    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def encode(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-zA-Z0-9']+", text.lower())

        for token in tokens:
            index = hash(token) % self.dimensions
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]


class OpenAIEmbeddingModel:
    endpoint = "https://api.openai.com/v1/embeddings"

    def __init__(self, api_key: str, model: str, timeout_seconds: float) -> None:
        self.model = model
        self.client = httpx.Client(
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    def encode(self, text: str) -> list[float]:
        response = self.client.post(
            self.endpoint,
            json={
                "model": self.model,
                "input": text,
            },
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", [])
        if not data:
            return []
        return [float(value) for value in data[0].get("embedding", [])]

    def close(self) -> None:
        self.client.close()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))
