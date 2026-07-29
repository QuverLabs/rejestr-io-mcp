"""Tests for Config.from_env(): required vars, defaults, overrides, and validation."""
import pytest

from rejestr_io_mcp.config import Config, ConfigError


def test_from_env_requires_api_key(monkeypatch):
    monkeypatch.delenv("REJESTR_IO_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="REJESTR_IO_API_KEY"):
        Config.from_env()


def test_from_env_applies_defaults(monkeypatch):
    monkeypatch.setenv("REJESTR_IO_API_KEY", "secret")
    for var in (
        "REJESTR_IO_BASE_URL", "REJESTR_IO_CACHE_TTL_SECONDS", "REJESTR_IO_CACHE_MAX_SIZE",
        "REJESTR_IO_DOWNLOAD_DIR", "MCP_TRANSPORT", "MCP_HTTP_PORT",
        "MCP_HTTP_HOST", "MCP_HTTP_AUTH_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)

    config = Config.from_env()

    assert config.api_key == "secret"
    assert config.base_url == "https://rejestr.io/api/v2/"
    assert config.cache_ttl_seconds == 300
    assert config.cache_max_size == 512
    assert config.download_dir == "./downloads"
    assert config.mcp_transport == "stdio"
    assert config.mcp_http_port == 8000
    assert config.mcp_http_host == "127.0.0.1"
    assert config.mcp_http_auth_token is None


def test_from_env_reads_overrides(monkeypatch):
    monkeypatch.setenv("REJESTR_IO_API_KEY", "secret")
    monkeypatch.setenv("REJESTR_IO_BASE_URL", "https://example.test/v2/")
    monkeypatch.setenv("REJESTR_IO_CACHE_TTL_SECONDS", "60")
    monkeypatch.setenv("REJESTR_IO_CACHE_MAX_SIZE", "10")
    monkeypatch.setenv("REJESTR_IO_DOWNLOAD_DIR", "/tmp/dl")
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("MCP_HTTP_PORT", "9000")
    monkeypatch.setenv("MCP_HTTP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "s3cret")

    config = Config.from_env()

    assert config.base_url == "https://example.test/v2/"
    assert config.cache_ttl_seconds == 60
    assert config.cache_max_size == 10
    assert config.download_dir == "/tmp/dl"
    assert config.mcp_transport == "http"
    assert config.mcp_http_port == 9000
    assert config.mcp_http_host == "0.0.0.0"
    assert config.mcp_http_auth_token == "s3cret"


def test_from_env_treats_empty_auth_token_as_unset(monkeypatch):
    # `MCP_HTTP_AUTH_TOKEN=` in a .env file must mean "no auth configured",
    # never "require an empty token".
    monkeypatch.setenv("REJESTR_IO_API_KEY", "secret")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "")

    assert Config.from_env().mcp_http_auth_token is None


def test_from_env_treats_empty_http_host_as_unset(monkeypatch):
    monkeypatch.setenv("REJESTR_IO_API_KEY", "secret")
    monkeypatch.setenv("MCP_HTTP_HOST", "")

    assert Config.from_env().mcp_http_host == "127.0.0.1"


def test_repr_hides_every_secret_field(monkeypatch):
    # Any future log line, or a pytest failure rendered with --showlocals,
    # would otherwise print the raw billed API key and the HTTP bearer token.
    monkeypatch.setenv("REJESTR_IO_API_KEY", "super-secret-key")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "super-secret-token")
    monkeypatch.setenv("REJESTR_IO_DOWNLOAD_DIR", "/tmp/dl")

    config = Config.from_env()
    rendered = repr(config)

    assert "super-secret-key" not in rendered
    assert "api_key" not in rendered
    assert "super-secret-token" not in rendered
    assert "mcp_http_auth_token" not in rendered
    # Non-secret fields must still be rendered, so that a repr=False applied
    # too broadly (or a plain `__repr__` override) would fail this test.
    assert "/tmp/dl" in rendered
    # Hiding a field from the repr must not hide it from the object itself.
    assert config.api_key == "super-secret-key"
    assert config.mcp_http_auth_token == "super-secret-token"


def test_from_env_rejects_invalid_transport(monkeypatch):
    monkeypatch.setenv("REJESTR_IO_API_KEY", "secret")
    monkeypatch.setenv("MCP_TRANSPORT", "carrier-pigeon")
    with pytest.raises(ConfigError, match="MCP_TRANSPORT"):
        Config.from_env()


def test_from_env_rejects_malformed_int_vars(monkeypatch):
    monkeypatch.setenv("REJESTR_IO_API_KEY", "secret")
    monkeypatch.setenv("REJESTR_IO_CACHE_TTL_SECONDS", "abc")
    with pytest.raises(ConfigError, match="REJESTR_IO_CACHE_TTL_SECONDS"):
        Config.from_env()
