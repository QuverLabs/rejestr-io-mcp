"""Tests for person MCP tools: profile and KRS relations."""
import httpx
import pytest
import respx
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from rejestr_io_mcp.tools import persons

BASE_URL = "https://rejestr.io/api/v2/"


@pytest.fixture
def mcp_client(rejestr_client) -> Client:
    mcp = FastMCP("test-server")
    persons.register(mcp, rejestr_client)
    return Client(mcp)


@respx.mock
async def test_get_person_returns_data(mcp_client):
    respx.get(f"{BASE_URL}osoby/42").mock(
        return_value=httpx.Response(200, json={"id": 42, "typ": "osoba"})
    )
    async with mcp_client as client:
        result = await client.call_tool("get_person", {"id": 42})
    assert result.data == {"id": 42, "typ": "osoba"}


@respx.mock
async def test_get_person_not_found_raises_readable_error(mcp_client):
    respx.get(f"{BASE_URL}osoby/999").mock(return_value=httpx.Response(404))
    async with mcp_client as client:
        with pytest.raises(ToolError, match="not found"):
            await client.call_tool("get_person", {"id": 999})


@respx.mock
async def test_get_person_relations_defaults_to_current_status(mcp_client):
    route = respx.get(f"{BASE_URL}osoby/42/krs-powiazania").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "typ": "organizacja"}])
    )
    async with mcp_client as client:
        result = await client.call_tool("get_person_relations", {"id": 42})
    assert result.data == [{"id": 1, "typ": "organizacja"}]
    assert route.calls.last.request.url.params["aktualnosc"] == "aktualne"


@respx.mock
async def test_get_person_relations_accepts_historical_status(mcp_client):
    route = respx.get(f"{BASE_URL}osoby/42/krs-powiazania").mock(
        return_value=httpx.Response(200, json=[])
    )
    async with mcp_client as client:
        await client.call_tool("get_person_relations", {"id": 42, "status": "historical"})
    assert route.calls.last.request.url.params["aktualnosc"] == "historyczne"


async def test_get_person_relations_rejects_invalid_status(mcp_client):
    async with mcp_client as client:
        with pytest.raises(ToolError, match="Invalid value"):
            await client.call_tool("get_person_relations", {"id": 42, "status": "bogus"})
