"""Tests for the account balance MCP tool."""
import httpx
import pytest
import respx
from fastmcp import Client, FastMCP

from rejestr_io_mcp.tools import account

BASE_URL = "https://rejestr.io/api/v2/"


@pytest.fixture
def mcp_client(rejestr_client) -> Client:
    mcp = FastMCP("test-server")
    account.register(mcp, rejestr_client)
    return Client(mcp)


@respx.mock
async def test_get_account_balance_returns_number(mcp_client):
    route = respx.get(f"{BASE_URL}konto/stan").mock(return_value=httpx.Response(200, json=123.45))
    async with mcp_client as client:
        result = await client.call_tool("get_account_balance", {})
    assert result.data == 123.45
    assert route.calls.last.request.headers["Authorization"] == "test-key"
