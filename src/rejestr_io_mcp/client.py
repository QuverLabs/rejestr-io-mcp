"""HTTP client for the rejestr.io API: authentication, response caching, and HTTP-status-to-exception mapping."""
from __future__ import annotations

from typing import Any

import httpx

from .cache import ResponseCache
from .errors import ApiError, AuthError, NotFoundError, PlanRequiredError, RateLimitError


class RejestrIoClient:
    def __init__(self, api_key: str, base_url: str, cache: ResponseCache) -> None:
        self._cache = cache
        self._client = httpx.AsyncClient(base_url=base_url, headers={"Authorization": api_key})

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        key = self._cache.make_key("GET", path, params)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        response = await self._client.get(path, params=params)
        self._raise_for_status(response)
        data = response.json()
        self._cache.set(key, data)
        return data

    async def get_binary(self, path: str, params: dict[str, Any] | None = None) -> bytes:
        response = await self._client.get(path, params=params)
        self._raise_for_status(response)
        # PDF endpoints can answer with a JSON error body and a 200-range status,
        # so a successful status alone does not mean the payload is a PDF.
        # Media types are case-insensitive (RFC 9110) and may carry parameters,
        # so compare the bare type rather than prefix-matching the raw header.
        content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type != "application/pdf":
            raise ApiError(f"Expected a PDF but got {content_type!r}: {response.text[:500]}")
        return response.content

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        if response.status_code in (401, 403):
            raise AuthError("Invalid or missing rejestr.io API key.")
        if response.status_code == 402:
            raise PlanRequiredError("This endpoint requires a higher rejestr.io plan (Premium or Biznes).")
        if response.status_code == 404:
            raise NotFoundError(f"Resource not found: {response.request.url}")
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded (1000 requests/min). Please wait and retry.")
        raise ApiError(f"rejestr.io API error {response.status_code}: {response.text}")
