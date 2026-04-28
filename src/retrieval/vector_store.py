from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from src.models.schemas import PaperRecord


@dataclass
class VectorDocument:
    document_id: str
    text: str
    metadata: Dict[str, object]
    embedding: List[float]


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._documents: List[VectorDocument] = []

    def upsert(self, documents: List[VectorDocument]) -> None:
        existing = {doc.document_id: doc for doc in self._documents}
        for document in documents:
            existing[document.document_id] = document
        self._documents = list(existing.values())

    def query(self, embedding: List[float], top_k: int = 5) -> List[VectorDocument]:
        if not self._documents:
            return []
        query_vector = np.array(embedding)
        scored = []
        for document in self._documents:
            doc_vector = np.array(document.embedding)
            score = float(np.dot(query_vector, doc_vector))
            scored.append((score, document))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored[:top_k]]


class ChromaVectorStore:
    def __init__(self, persist_dir: str, collection_name: str = "scholartrend_abstracts") -> None:
        import chromadb

        client = chromadb.PersistentClient(path=persist_dir)
        self.collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, documents: List[VectorDocument]) -> None:
        if not documents:
            return
        self.collection.upsert(
            ids=[doc.document_id for doc in documents],
            documents=[doc.text for doc in documents],
            metadatas=[doc.metadata for doc in documents],
            embeddings=[doc.embedding for doc in documents],
        )

    def query(self, embedding: List[float], top_k: int = 5) -> List[VectorDocument]:
        result = self.collection.query(query_embeddings=[embedding], n_results=top_k)
        docs = []
        for idx, document_id in enumerate(result.get("ids", [[]])[0]):
            docs.append(
                VectorDocument(
                    document_id=document_id,
                    text=result.get("documents", [[]])[0][idx],
                    metadata=result.get("metadatas", [[]])[0][idx],
                    embedding=[],
                )
            )
        return docs


def build_vector_store(backend: str, persist_dir: str):
    if backend == "chroma":
        try:
            return ChromaVectorStore(persist_dir=persist_dir)
        except Exception:
            return InMemoryVectorStore()
    return InMemoryVectorStore()
