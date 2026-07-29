"""Thin wrapper around cachetools.TTLCache for caching rejestr.io JSON responses."""
from __future__ import annotations

from typing import Any

from cachetools import TTLCache


class ResponseCache:
    def __init__(self, maxsize: int, ttl: float) -> None:
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)

    @staticmethod
    def make_key(method: str, path: str, params: dict[str, Any] | None) -> tuple:
        return (method, path, tuple(sorted((params or {}).items())))

    def get(self, key: tuple) -> Any | None:
        return self._cache.get(key)

    def set(self, key: tuple, value: Any) -> None:
        self._cache[key] = value
