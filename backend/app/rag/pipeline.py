from __future__ import annotations

from datetime import datetime, timezone

from app.rag.chunking import TextChunker
from app.rag.vector_store import FileVectorStore, RetrievedChunk
from app.schemas.upload import DocumentRecord


class RAGPipeline:
    def __init__(self, chunker: TextChunker, vector_store: FileVectorStore) -> None:
        self.chunker = chunker
        self.vector_store = vector_store

    def ingest_document(
        self,
        document_id: str,
        filename: str,
        content_type: str,
        text: str,
    ) -> DocumentRecord:
        chunks = self.chunker.chunk_text(document_id=document_id, document_name=filename, text=text)
        document = DocumentRecord(
            document_id=document_id,
            filename=filename,
            content_type=content_type,
            uploaded_at=datetime.now(timezone.utc),
            chunk_count=len(chunks),
        )
        self.vector_store.add_document(document=document, chunks=chunks)
        return document

    def retrieve(self, query: str, limit: int) -> list[RetrievedChunk]:
        return self.vector_store.search(query=query, limit=limit)

    def list_documents(self) -> list[DocumentRecord]:
        return self.vector_store.list_documents()

