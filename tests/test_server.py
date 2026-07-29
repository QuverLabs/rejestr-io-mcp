"""Tests for server assembly (all 12 tools registered), optional bearer auth, and CLI argument parsing."""
import dataclasses

import pytest
from fastmcp import Client
from fastmcp.server.auth import AccessToken, TokenVerifier

from rejestr_io_mcp.config import Config
from rejestr_io_mcp.server import SharedSecretVerifier, _parse_args, build_server


@pytest.fixture
def config(tmp_path, monkeypatch) -> Config:
    monkeypatch.setenv("REJESTR_IO_API_KEY", "test-key")
    monkeypatch.setenv("REJESTR_IO_DOWNLOAD_DIR", str(tmp_path / "downloads"))
    monkeypatch.delenv("MCP_HTTP_AUTH_TOKEN", raising=False)
    return Config.from_env()


async def test_build_server_registers_all_twelve_tools(config):
    mcp = build_server(config)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    tool_names = {tool.name for tool in tools}
    assert tool_names == {
        "search_organizations",
        "get_organization",
        "get_organization_krs_chapter",
        "get_organization_beneficial_owners",
        "get_organization_relations",
        "list_organization_krs_entries",
        "get_organization_krs_extract",
        "get_person",
        "get_person_relations",
        "list_organization_financial_documents",
        "get_organization_financial_document",
        "get_account_balance",
    }


def test_build_server_without_auth_token_has_no_auth(config):
    assert config.mcp_http_auth_token is None
    assert build_server(config).auth is None


def test_build_server_with_auth_token_installs_token_verifier(config):
    authed = dataclasses.replace(config, mcp_http_auth_token="s3cret")

    auth = build_server(authed).auth

    assert isinstance(auth, SharedSecretVerifier)
    assert isinstance(auth, TokenVerifier)


async def test_shared_secret_verifier_accepts_the_configured_token():
    verifier = SharedSecretVerifier("s3cret")

    access_token = await verifier.verify_token("s3cret")

    assert isinstance(access_token, AccessToken)
    assert access_token.token == "s3cret"


async def test_shared_secret_verifier_rejects_any_other_token():
    verifier = SharedSecretVerifier("s3cret")

    assert await verifier.verify_token("wrong") is None
    assert await verifier.verify_token("") is None
    assert await verifier.verify_token("s3cre") is None


async def test_shared_secret_verifier_rejects_non_ascii_token_without_raising():
    # hmac.compare_digest raises TypeError on non-ASCII *str* operands, so a
    # remote request carrying a non-ASCII bearer header would crash the handler
    # with an HTTP 500 instead of being rejected. Anyone able to reach the port
    # could trigger it.
    verifier = SharedSecretVerifier("s3cret")

    assert await verifier.verify_token("żółw") is None
    assert await verifier.verify_token("🔑") is None


async def test_shared_secret_verifier_supports_a_non_ascii_configured_token():
    # Worse than the above: a non-ASCII configured token broke auth outright —
    # even the correct token raised, rather than being compared.
    #
    # Note this is a guarantee about the verifier only. End to end over HTTP a
    # non-ASCII token is still unreliable, because the ASGI layer decodes header
    # bytes as latin-1: a client that sends the header UTF-8-encoded delivers
    # mojibake and is correctly rejected. That is why the documented example
    # token is ASCII. The verifier's job is to fail closed, never to raise.
    verifier = SharedSecretVerifier("twój-token")

    access_token = await verifier.verify_token("twój-token")

    assert isinstance(access_token, AccessToken)
    assert access_token.token == "twój-token"
    assert await verifier.verify_token("twoj-token") is None


def test_parse_args_defaults_to_none():
    args = _parse_args([])
    assert args.transport is None
    assert args.port is None
    assert args.host is None


def test_parse_args_reads_transport_and_port():
    args = _parse_args(["--transport", "http", "--port", "9001"])
    assert args.transport == "http"
    assert args.port == 9001


def test_parse_args_reads_host():
    args = _parse_args(["--transport", "http", "--host", "0.0.0.0"])
    assert args.host == "0.0.0.0"


def test_parse_args_preserves_explicit_port_zero():
    # Regression guard: main() resolves the port with
    # `args.port if args.port is not None else config.mcp_http_port`.
    # A naive `args.port or config.mcp_http_port` would silently discard an
    # explicit `--port 0` because 0 is falsy in Python. This test confirms
    # _parse_args itself keeps 0 intact; the None-check fix lives in main().
    args = _parse_args(["--port", "0"])
    assert args.port == 0
