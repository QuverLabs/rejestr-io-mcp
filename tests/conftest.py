"""Shared pytest fixtures: a mocked rejestr.io client and a temp downloads directory."""
from __future__ import annotations

import pytest

from rejestr_io_mcp.cache import ResponseCache
from rejestr_io_mcp.client import RejestrIoClient

BASE_URL = "https://rejestr.io/api/v2/"


@pytest.fixture
def download_dir(tmp_path) -> str:
    return str(tmp_path / "downloads")


@pytest.fixture
async def rejestr_client():
    client = RejestrIoClient(
        api_key="test-key",
        base_url=BASE_URL,
        cache=ResponseCache(maxsize=512, ttl=300),
    )
    yield client
    await client.aclose()
