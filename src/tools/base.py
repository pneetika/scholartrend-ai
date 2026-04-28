from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import List, Optional

from dateutil import parser as date_parser

from src.models.schemas import PaperAuthor, PaperRecord, ResearchRequest, SourceName
from src.utils.http import AsyncHTTPClient


def parse_optional_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date_parser.parse(value).date()
    except Exception:
        return None


def request_start_date(request: ResearchRequest) -> Optional[date]:
    if request.time_range.value == "custom":
        return request.custom_start_date
    if request.time_range.value == "6m":
        return (datetime.utcnow() - timedelta(days=183)).date()
    if request.time_range.value == "1y":
        return (datetime.utcnow() - timedelta(days=365)).date()
    if request.time_range.value == "3y":
        return (datetime.utcnow() - timedelta(days=1095)).date()
    return None


def safe_authors(names: List[str]) -> List[PaperAuthor]:
    return [PaperAuthor(name=name) for name in names if name]


class BaseAcademicClient(ABC):
    source_name: SourceName

    def __init__(self, http_client: AsyncHTTPClient) -> None:
        self.http_client = http_client

    @abstractmethod
    async def search(self, query: str, request: ResearchRequest) -> List[PaperRecord]:
        raise NotImplementedError
