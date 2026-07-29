"""Tests for financial document MCP tools: listing and fetching (JSON/PDF)."""
import httpx
import pytest
import respx
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from rejestr_io_mcp.tools import financial

BASE_URL = "https://rejestr.io/api/v2/"


@pytest.fixture
def mcp_client(rejestr_client, download_dir) -> Client:
    mcp = FastMCP("test-server")
    financial.register(mcp, rejestr_client, download_dir)
    return Client(mcp)


@respx.mock
async def test_list_organization_financial_documents_returns_list(mcp_client):
    respx.get(f"{BASE_URL}org/12345/krs-dokumenty").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "data_start": "2023-01-01",
                    "data_koniec": "2023-12-31",
                    "dokumenty": [{"id": 1, "nazwa": "bilans", "czy_ma_json": True}],
                }
            ],
        )
    )
    async with mcp_client as client:
        result = await client.call_tool("list_organization_financial_documents", {"id": "12345"})
    assert result.data[0]["dokumenty"][0]["nazwa"] == "bilans"


@respx.mock
async def test_list_organization_financial_documents_requires_premium(mcp_client):
    respx.get(f"{BASE_URL}org/12345/krs-dokumenty").mock(return_value=httpx.Response(402))
    async with mcp_client as client:
        with pytest.raises(ToolError, match="Premium"):
            await client.call_tool("list_organization_financial_documents", {"id": "12345"})


from pathlib import Path


@respx.mock
async def test_get_organization_financial_document_json_returns_parsed_content(mcp_client):
    respx.get(f"{BASE_URL}org/12345/krs-dokumenty/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id_organizacji": 12345,
                "id_dokumentu": 1,
                "nazwa": "bilans",
                "okres_data_start": "2023-01-01",
                "okres_data_koniec": "2023-12-31",
                "zawartosc": {"nazwa_wezla": "root"},
            },
        )
    )
    async with mcp_client as client:
        result = await client.call_tool(
            "get_organization_financial_document", {"id": "12345", "document_id": 1, "format": "json"}
        )
    assert result.data["nazwa"] == "bilans"


@respx.mock
async def test_get_organization_financial_document_json_requires_biznes_plan(mcp_client):
    respx.get(f"{BASE_URL}org/12345/krs-dokumenty/1").mock(return_value=httpx.Response(402))
    async with mcp_client as client:
        with pytest.raises(ToolError, match="Premium"):
            await client.call_tool(
                "get_organization_financial_document", {"id": "12345", "document_id": 1, "format": "json"}
            )


@respx.mock
async def test_get_organization_financial_document_pdf_saves_file_and_returns_path(mcp_client, download_dir):
    respx.get(f"{BASE_URL}org/12345/krs-dokumenty/1").mock(
        return_value=httpx.Response(200, content=b"%PDF-1.4 fake", headers={"content-type": "application/pdf"})
    )
    async with mcp_client as client:
        result = await client.call_tool(
            "get_organization_financial_document", {"id": "12345", "document_id": 1}
        )
    saved_path = result.data
    assert saved_path.startswith(download_dir)
    assert Path(saved_path).read_bytes() == b"%PDF-1.4 fake"


@respx.mock
async def test_get_organization_financial_document_pdf_return_base64_includes_file_content(mcp_client):
    respx.get(f"{BASE_URL}org/12345/krs-dokumenty/1").mock(
        return_value=httpx.Response(200, content=b"%PDF-1.4 fake", headers={"content-type": "application/pdf"})
    )
    async with mcp_client as client:
        result = await client.call_tool(
            "get_organization_financial_document",
            {"id": "12345", "document_id": 1, "return_base64": True},
        )
    assert result.data["file_path"].endswith(".pdf")
    assert len(result.content) == 2


async def test_get_organization_financial_document_rejects_invalid_format(mcp_client):
    async with mcp_client as client:
        with pytest.raises(ToolError, match="Invalid value"):
            await client.call_tool(
                "get_organization_financial_document", {"id": "12345", "document_id": 1, "format": "xml"}
            )
