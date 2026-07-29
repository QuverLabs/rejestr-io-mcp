"""MCP tools for person data: profile and KRS relations."""
from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from ..client import RejestrIoClient
from ..mappings import RELATION_STATUS_MAP
from ._shared import call_api, enum_param


def register(mcp: FastMCP, client: RejestrIoClient) -> None:
    @mcp.tool
    async def get_person(id: int) -> dict:
        """Get current data for a person appearing in the KRS by their person id."""
        return await call_api(client.get_json(f"osoby/{id}"))

    @mcp.tool
    async def get_person_relations(
        id: int,
        status: Annotated[
            str,
            Field(
                description=(
                    "Whether to return current ('current', default) or historical ('historical') relations."
                )
            ),
        ] = "current",
    ) -> list:
        """Get a person's current or historical relations with organizations recorded in the KRS."""
        polish_status = enum_param(status, RELATION_STATUS_MAP, "status")
        return await call_api(client.get_json(f"osoby/{id}/krs-powiazania", params={"aktualnosc": polish_status}))
