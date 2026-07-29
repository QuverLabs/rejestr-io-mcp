"""MCP tool for the rejestr.io account balance."""
from __future__ import annotations

from fastmcp import FastMCP

from ..client import RejestrIoClient
from ._shared import call_api


def register(mcp: FastMCP, client: RejestrIoClient) -> None:
    @mcp.tool
    async def get_account_balance() -> float:
        """Get the current rejestr.io API account balance in PLN. Free — does not consume account balance."""
        return await call_api(client.get_json("konto/stan"))
