from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_container
from app.schemas.upload import DocumentListResponse, UploadResponse
from app.services.container import ServiceContainer

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    container: ServiceContainer = Depends(get_container),
) -> UploadResponse:
    document = await container.upload_service.save(file)
    return UploadResponse(document=document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(container: ServiceContainer = Depends(get_container)) -> DocumentListResponse:
    return DocumentListResponse(documents=container.upload_service.list_documents())

