from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.rag.chunking import Chunk
from app.rag.embeddings import EmbeddingModel, cosine_similarity
from app.schemas.upload import DocumentRecord


@dataclass(slots=True)
class RetrievedChunk:
    document_id: str
    document_name: str
    chunk_id: str
    text: str
    score: float


@dataclass(slots=True)
class _StoredChunk:
    document_id: str
    document_name: str
    chunk_id: str
    text: str
    embedding: list[float]


class FileVectorStore:
    def __init__(self, path: Path, embedding_model: EmbeddingModel) -> None:
        self.path = path
        self.embedding_model = embedding_model
        self._lock = threading.Lock()
        self._records: list[_StoredChunk] = []
        self._documents: dict[str, DocumentRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self._records = [_StoredChunk(**record) for record in payload.get("records", [])]
        self._documents = {
            document["document_id"]: DocumentRecord.model_validate(document)
            for document in payload.get("documents", [])
        }

    def _persist(self) -> None:
        payload = {
            "records": [asdict(record) for record in self._records],
            "documents": [document.model_dump(mode="json") for document in self._documents.values()],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add_document(self, document: DocumentRecord, chunks: list[Chunk]) -> None:
        with self._lock:
            self._documents[document.document_id] = document
            for chunk in chunks:
                self._records.append(
                    _StoredChunk(
                        document_id=chunk.document_id,
                        document_name=chunk.document_name,
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        embedding=self.embedding_model.encode(chunk.text),
                    )
                )
            self._persist()

    def list_documents(self) -> list[DocumentRecord]:
        return sorted(
            self._documents.values(),
            key=lambda document: document.uploaded_at,
            reverse=True,
        )

    def search(self, query: str, limit: int = 5) -> list[RetrievedChunk]:
        if not query.strip():
            return []

        query_vector = self.embedding_model.encode(query)
        scored: list[RetrievedChunk] = []

        for record in self._records:
            score = cosine_similarity(query_vector, record.embedding)
            if score <= 0:
                continue
            scored.append(
                RetrievedChunk(
                    document_id=record.document_id,
                    document_name=record.document_name,
                    chunk_id=record.chunk_id,
                    text=record.text,
                    score=round(score, 4),
                )
            )

        return sorted(scored, key=lambda chunk: chunk.score, reverse=True)[:limit]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
