from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    content_type: str
    uploaded_at: datetime
    chunk_count: int


class UploadResponse(BaseModel):
    document: DocumentRecord


class DocumentListResponse(BaseModel):
    documents: list[DocumentRecord]

