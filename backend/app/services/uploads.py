from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings
from app.rag.pipeline import RAGPipeline
from app.schemas.upload import DocumentRecord

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional at runtime
    PdfReader = None


class UploadService:
    def __init__(self, settings: Settings, rag_pipeline: RAGPipeline) -> None:
        self.settings = settings
        self.rag_pipeline = rag_pipeline

    async def save(self, upload: UploadFile) -> DocumentRecord:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in self.settings.allowed_upload_suffixes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {suffix or 'unknown'}",
            )

        raw_bytes = await upload.read()
        size_mb = len(raw_bytes) / (1024 * 1024)
        if size_mb > self.settings.max_upload_size_mb:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds {self.settings.max_upload_size_mb} MB limit.",
            )

        document_id = f"doc-{uuid.uuid4().hex[:10]}"
        target_path = self.settings.upload_dir / f"{document_id}{suffix}"
        target_path.write_bytes(raw_bytes)

        text = self._extract_text(target_path=target_path, suffix=suffix, raw_bytes=raw_bytes)
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file did not contain extractable text.",
            )

        return self.rag_pipeline.ingest_document(
            document_id=document_id,
            filename=upload.filename or target_path.name,
            content_type=upload.content_type or "application/octet-stream",
            text=text,
        )

    def list_documents(self) -> list[DocumentRecord]:
        return self.rag_pipeline.list_documents()

    def _extract_text(self, target_path: Path, suffix: str, raw_bytes: bytes) -> str:
        if suffix in {".txt", ".md", ".csv"}:
            return raw_bytes.decode("utf-8", errors="ignore")

        if suffix == ".json":
            payload = json.loads(raw_bytes.decode("utf-8", errors="ignore"))
            return json.dumps(payload, indent=2)

        if suffix == ".pdf":
            if PdfReader is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="PDF support is unavailable because pypdf is not installed.",
                )
            reader = PdfReader(str(target_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)

        return raw_bytes.decode("utf-8", errors="ignore")

