"""Tests for organization MCP tools: search, KRS chapters, relations, extracts, and entries."""
import httpx
import pytest
import respx
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from rejestr_io_mcp.tools import organizations

BASE_URL = "https://rejestr.io/api/v2/"


@pytest.fixture
def mcp_client(rejestr_client, download_dir) -> Client:
    mcp = FastMCP("test-server")
    organizations.register(mcp, rejestr_client, download_dir)
    return Client(mcp)


@respx.mock
async def test_search_organizations_translates_params_and_returns_results(mcp_client):
    route = respx.get(f"{BASE_URL}org").mock(
        return_value=httpx.Response(200, json={"liczba_wszystkich_wynikow": 1, "wyniki": [{"id": 1}]})
    )
    async with mcp_client as client:
        result = await client.call_tool(
            "search_organizations", {"name": "Example", "size": "micro", "address_type": "branch"}
        )
    assert result.data == {"liczba_wszystkich_wynikow": 1, "wyniki": [{"id": 1}]}
    sent = route.calls.last.request.url.params
    assert sent["nazwa"] == "Example"
    assert sent["wielkosc"] == "mikro"
    assert sent["typ_adresu"] == "oddzial"


async def test_search_organizations_rejects_invalid_size(mcp_client):
    async with mcp_client as client:
        with pytest.raises(ToolError, match="huge"):
            await client.call_tool("search_organizations", {"size": "huge"})


@respx.mock
async def test_get_organization_returns_basic_data(mcp_client):
    respx.get(f"{BASE_URL}org/12345").mock(
        return_value=httpx.Response(200, json={"id": 12345, "typ": "organizacja"})
    )
    async with mcp_client as client:
        result = await client.call_tool("get_organization", {"id": "12345"})
    assert result.data == {"id": 12345, "typ": "organizacja"}


@respx.mock
async def test_get_organization_not_found_raises_readable_error(mcp_client):
    respx.get(f"{BASE_URL}org/999").mock(return_value=httpx.Response(404))
    async with mcp_client as client:
        with pytest.raises(ToolError, match="not found"):
            await client.call_tool("get_organization", {"id": "999"})


@respx.mock
async def test_list_organization_krs_entries_returns_list(mcp_client):
    respx.get(f"{BASE_URL}org/12345/krs-wpisy").mock(
        return_value=httpx.Response(200, json=[{"numer": 1, "sygnatura": "X/1"}])
    )
    async with mcp_client as client:
        result = await client.call_tool("list_organization_krs_entries", {"id": "12345"})
    assert result.data == [{"numer": 1, "sygnatura": "X/1"}]


@respx.mock
async def test_get_organization_krs_chapter_translates_chapter_and_entry_number(mcp_client):
    route = respx.get(f"{BASE_URL}org/12345/krs-rozdzialy/ogolny").mock(
        return_value=httpx.Response(200, json={"nazwa_krotka": {"_wartosc": "EXAMPLE"}})
    )
    async with mcp_client as client:
        result = await client.call_tool(
            "get_organization_krs_chapter", {"id": "12345", "chapter": "general", "entry_number": 7}
        )
    assert result.data == {"nazwa_krotka": {"_wartosc": "EXAMPLE"}}
    assert route.calls.last.request.url.params["nr_wpisu"] == "7"


@respx.mock
async def test_get_organization_krs_chapter_requiring_premium_raises_plan_required(mcp_client):
    respx.get(f"{BASE_URL}org/12345/krs-rozdzialy/oddzialy").mock(return_value=httpx.Response(402))
    async with mcp_client as client:
        with pytest.raises(ToolError, match="Premium"):
            await client.call_tool("get_organization_krs_chapter", {"id": "12345", "chapter": "branches"})


@respx.mock
async def test_get_organization_beneficial_owners_returns_list(mcp_client):
    respx.get(f"{BASE_URL}org/12345/crbr").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "typ": "osoba"}])
    )
    async with mcp_client as client:
        result = await client.call_tool("get_organization_beneficial_owners", {"id": "12345"})
    assert result.data == [{"id": 1, "typ": "osoba"}]


@respx.mock
async def test_get_organization_relations_defaults_to_current_status(mcp_client):
    route = respx.get(f"{BASE_URL}org/12345/krs-powiazania").mock(
        return_value=httpx.Response(200, json=[{"id": 2, "typ": "organizacja"}])
    )
    async with mcp_client as client:
        result = await client.call_tool("get_organization_relations", {"id": "12345"})
    assert result.data == [{"id": 2, "typ": "organizacja"}]
    assert route.calls.last.request.url.params["aktualnosc"] == "aktualne"


@respx.mock
async def test_get_organization_relations_accepts_historical_status(mcp_client):
    route = respx.get(f"{BASE_URL}org/12345/krs-powiazania").mock(
        return_value=httpx.Response(200, json=[])
    )
    async with mcp_client as client:
        await client.call_tool("get_organization_relations", {"id": "12345", "status": "historical"})
    assert route.calls.last.request.url.params["aktualnosc"] == "historyczne"


from pathlib import Path


@respx.mock
async def test_get_organization_krs_extract_saves_pdf_and_returns_path(mcp_client, download_dir):
    respx.get(f"{BASE_URL}org/12345/krs-odpisy").mock(
        return_value=httpx.Response(200, content=b"%PDF-1.4 fake", headers={"content-type": "application/pdf"})
    )
    async with mcp_client as client:
        result = await client.call_tool("get_organization_krs_extract", {"id": "12345"})
    saved_path = result.data
    assert saved_path.startswith(download_dir)
    assert saved_path.endswith(".pdf")
    assert Path(saved_path).read_bytes() == b"%PDF-1.4 fake"


@respx.mock
async def test_get_organization_krs_extract_return_base64_includes_file_content(mcp_client):
    respx.get(f"{BASE_URL}org/12345/krs-odpisy").mock(
        return_value=httpx.Response(200, content=b"%PDF-1.4 fake", headers={"content-type": "application/pdf"})
    )
    async with mcp_client as client:
        result = await client.call_tool(
            "get_organization_krs_extract", {"id": "12345", "return_base64": True}
        )
    assert result.data["file_path"].endswith(".pdf")
    assert len(result.content) == 2


@respx.mock
async def test_get_organization_krs_extract_full_type_translates_to_pelny(mcp_client):
    route = respx.get(f"{BASE_URL}org/12345/krs-odpisy").mock(
        return_value=httpx.Response(200, content=b"%PDF-1.4 fake", headers={"content-type": "application/pdf"})
    )
    async with mcp_client as client:
        await client.call_tool("get_organization_krs_extract", {"id": "12345", "extract_type": "full"})
    assert route.calls.last.request.url.params["typ"] == "pelny"


@respx.mock
async def test_get_organization_krs_extract_deregistered_current_raises_readable_404(mcp_client):
    respx.get(f"{BASE_URL}org/999/krs-odpisy").mock(return_value=httpx.Response(404))
    async with mcp_client as client:
        with pytest.raises(ToolError, match="not found"):
            await client.call_tool("get_organization_krs_extract", {"id": "999"})
