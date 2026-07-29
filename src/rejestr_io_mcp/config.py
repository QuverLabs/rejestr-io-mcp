"""Reads and validates rejestr.io MCP server configuration from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def _parse_int(name: str, default: str) -> int:
    """Parse an environment variable as an integer, raising ConfigError on failure."""
    raw = os.environ.get(name, default)
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from None


@dataclass(frozen=True)
class Config:
    # repr=False keeps secrets (the billed API key and the HTTP bearer token)
    # out of any log line or pytest --showlocals rendering. It is not a default
    # value, so field order is unaffected.
    api_key: str = field(repr=False)
    base_url: str
    cache_ttl_seconds: int
    cache_max_size: int
    download_dir: str
    mcp_transport: str
    mcp_http_port: int
    mcp_http_host: str
    mcp_http_auth_token: str | None = field(repr=False)

    @classmethod
    def from_env(cls) -> "Config":
        api_key = os.environ.get("REJESTR_IO_API_KEY")
        if not api_key:
            raise ConfigError("REJESTR_IO_API_KEY environment variable is required")

        mcp_transport = os.environ.get("MCP_TRANSPORT", "stdio")
        if mcp_transport not in ("stdio", "http"):
            raise ConfigError(f"MCP_TRANSPORT must be 'stdio' or 'http', got {mcp_transport!r}")

        return cls(
            api_key=api_key,
            base_url=os.environ.get("REJESTR_IO_BASE_URL", "https://rejestr.io/api/v2/"),
            cache_ttl_seconds=_parse_int("REJESTR_IO_CACHE_TTL_SECONDS", "300"),
            cache_max_size=_parse_int("REJESTR_IO_CACHE_MAX_SIZE", "512"),
            download_dir=os.environ.get("REJESTR_IO_DOWNLOAD_DIR", "./downloads"),
            mcp_transport=mcp_transport,
            mcp_http_port=_parse_int("MCP_HTTP_PORT", "8000"),
            # Loopback only unless explicitly overridden. For both variables below,
            # an empty value (e.g. a bare `MCP_HTTP_AUTH_TOKEN=` line in .env) means
            # "unset" — never "bind to an empty host" or "require an empty token".
            mcp_http_host=os.environ.get("MCP_HTTP_HOST") or "127.0.0.1",
            mcp_http_auth_token=os.environ.get("MCP_HTTP_AUTH_TOKEN") or None,
        )
