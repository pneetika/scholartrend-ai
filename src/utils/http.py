from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any, Dict, Optional

import httpx

from src.utils.cache import ResponseCache


class AsyncHTTPClient:
    def __init__(
        self,
        *,
        timeout_seconds: int,
        cache: Optional[ResponseCache] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.cache = cache
        self.client = httpx.AsyncClient(timeout=timeout_seconds, headers=default_headers or {})

    async def get_json(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        cache_namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        cache_key = None
        if self.cache and cache_namespace:
            serialized = json.dumps({"url": url, "params": params}, sort_keys=True, default=str)
            cache_key = hashlib.sha256(f"{cache_namespace}:{serialized}".encode("utf-8")).hexdigest()
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        last_error = None
        for attempt in range(3):
            try:
                response = await self.client.get(url, params=params, headers=headers)
                response.raise_for_status()
                payload = response.json()
                if cache_key and self.cache:
                    self.cache.set(cache_key, payload)
                return payload
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(0.5 * (attempt + 1))

        raise RuntimeError(f"Request failed for {url}: {last_error}")

    async def get_text(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        last_error = None
        for attempt in range(3):
            try:
                response = await self.client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.text
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"Text request failed for {url}: {last_error}")

    async def aclose(self) -> None:
        await self.client.aclose()
