from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    environment: str
    timestamp: datetime


class MemoryEntry(BaseModel):
    role: str
    content: str
    created_at: datetime

