"""Builds the FastMCP application, registers all tools, and provides the process entry point."""
from __future__ import annotations

import argparse
import hmac
import sys

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken, TokenVerifier

from .cache import ResponseCache
from .client import RejestrIoClient
from .config import Config, ConfigError
from .tools import account, financial, organizations, persons


class SharedSecretVerifier(TokenVerifier):
    """Verifies a single shared bearer token via constant-time comparison.

    Only the HTTP transport enforces this — FastMCP's stdio code path never
    consults the server's auth provider, so a configured token has no effect
    on the default stdio transport.
    """

    def __init__(self, token: str) -> None:
        super().__init__()
        self._token = token

    async def verify_token(self, token: str) -> AccessToken | None:
        # Compare as UTF-8 bytes: hmac.compare_digest raises TypeError on
        # non-ASCII str operands, which would turn a non-ASCII bearer header
        # into an HTTP 500 (and break auth outright for a non-ASCII configured
        # token). Byte comparison keeps the constant-time guarantee.
        if not hmac.compare_digest(token.encode("utf-8"), self._token.encode("utf-8")):
            return None
        return AccessToken(token=token, client_id="rejestr-io-mcp", scopes=[], expires_at=None)


def build_server(config: Config) -> FastMCP:
    auth = (
        SharedSecretVerifier(config.mcp_http_auth_token)
        if config.mcp_http_auth_token is not None
        else None
    )
    mcp = FastMCP("rejestr-io-mcp", auth=auth)
    cache = ResponseCache(maxsize=config.cache_max_size, ttl=config.cache_ttl_seconds)
    client = RejestrIoClient(api_key=config.api_key, base_url=config.base_url, cache=cache)

    organizations.register(mcp, client, config.download_dir)
    persons.register(mcp, client)
    financial.register(mcp, client, config.download_dir)
    account.register(mcp, client)

    return mcp


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="rejestr-io-mcp")
    parser.add_argument("--transport", choices=["stdio", "http"], default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--host", default=None)
    return parser.parse_args(argv)


def main() -> None:
    load_dotenv()
    try:
        config = Config.from_env()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    args = _parse_args()
    transport = args.transport or config.mcp_transport
    port = args.port if args.port is not None else config.mcp_http_port
    host = args.host if args.host is not None else config.mcp_http_host

    mcp = build_server(config)

    if transport == "http":
        mcp.run(transport="http", host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
