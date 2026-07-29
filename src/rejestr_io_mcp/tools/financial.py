"""MCP tools for organization financial documents."""
from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import RejestrIoClient
from ..mappings import DOCUMENT_FORMAT_MAP
from ._shared import build_pdf_tool_result, call_api, enum_param


def register(mcp: FastMCP, client: RejestrIoClient, download_dir: str) -> None:
    @mcp.tool
    async def list_organization_financial_documents(id: str) -> list:
        """List financial document groups (by accounting period) available in the KRS for an organization. Requires a Premium+ plan."""
        return await call_api(client.get_json(f"org/{id}/krs-dokumenty"))

    @mcp.tool
    async def get_organization_financial_document(
        id: str,
        document_id: int,
        format: Annotated[
            str,
            Field(
                description=(
                    "Format of the returned document: 'pdf' (default, requires Premium+) returns the raw "
                    "PDF file; 'json' (requires Biznes plan, higher per-request cost than PDF) returns the "
                    "parsed document content directly."
                )
            ),
        ] = "pdf",
        return_base64: Annotated[
            bool,
            Field(
                description=(
                    "Whether to also return the PDF content inline (as a base64-encoded file content block) "
                    "in addition to saving it to disk and returning the file path. Only applies when "
                    "format='pdf' — ignored for format='json'."
                )
            ),
        ] = False,
    ) -> Any:
        """Get one financial document for an organization by document id. format='pdf' (default) requires Premium+ and saves the file to the downloads directory, returning its absolute path (pass return_base64=True to also receive the content inline). format='json' requires a Biznes plan and returns the parsed document content directly, at a higher per-request cost."""
        format = enum_param(format, DOCUMENT_FORMAT_MAP, "format")

        if format == "json":
            return await call_api(
                client.get_json(f"org/{id}/krs-dokumenty/{document_id}", params={"format": "json"})
            )

        content = await call_api(
            client.get_binary(f"org/{id}/krs-dokumenty/{document_id}", params={"format": "pdf"})
        )
        return await build_pdf_tool_result(
            download_dir, "financial_document", id, content, return_base64, f"financial_document_{id}_{document_id}"
        )
