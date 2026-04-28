from __future__ import annotations

from typing import List

from src.providers.llm import BaseLLMProvider
from src.utils.config import Settings


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        model = self._load()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()


class EmbeddingService:
    def __init__(self, settings: Settings, llm_provider: BaseLLMProvider) -> None:
        self.settings = settings
        self.llm_provider = llm_provider
        self._sentence_transformer = SentenceTransformerEmbedder(settings.sentence_transformer_model)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if self.settings.embedding_provider == "sentence_transformers":
            return await self._sentence_transformer.embed_texts(texts)
        return await self.llm_provider.embed_texts(texts)
