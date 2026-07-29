# AGENTS.md — Installing rejestr-io-mcp

This file is written for AI coding assistants and agents — Claude, Claude Code, ChatGPT/Codex, GitHub Copilot, and similar tools — that are asked to set up the `rejestr-io-mcp` server for a user. It gives concrete, executable steps rather than prose explanation. If you are an agent following this file: work through the steps in order, and stop to ask the human at every point marked **ASK THE HUMAN** — those steps require information or a decision only they can provide.

MCP client configuration formats change over time and differ per tool. The steps below reflect each tool's documented format as of this writing. If a step fails because the config schema has moved, consult that tool's current MCP documentation rather than guessing at a new schema.

## What this server provides

A local MCP server exposing 12 tools for the Polish company registry API (rejestr.io): KRS company search/lookup, CRBR beneficial-owner data, financial documents, and account balance. Tool names and parameters are English; the server translates them to the Polish parameter names rejestr.io's API expects. See [README.md](README.md) for the full tool list, configuration reference, and legal notes about rejestr.io.

**If the user is non-technical and just wants this working in Claude Desktop
or the ChatGPT desktop app on Windows or macOS (Apple Silicon), point them at
the prebuilt release instead of walking them through the steps below** — see
[README.md § Szybka instalacja](README.md#szybka-instalacja-bez-pythonauv).
It's a downloadable installer that needs no Python/`uv` and configures both
clients automatically. The rest of this file remains the right path for
Linux, Intel Mac, contributors, or any agent-driven setup that needs
fine-grained control.

## Prerequisites

- Python >= 3.11
- [`uv`](https://docs.astral.sh/uv/) installed and on `PATH`
- A local clone of this repository (if you don't already have one, clone it before continuing — this file assumes you're running from inside the repo root)
- A rejestr.io API key — **ASK THE HUMAN** for this (see Step 2). Do not attempt to generate, guess, or invent one.

## Step 1: Install dependencies

```bash
uv sync --extra dev
```

This creates `.venv` and installs `fastmcp`, `httpx`, `cachetools`, `python-dotenv`, `pydantic`, plus the test toolchain. Confirm it completes with no errors before continuing.

## Step 2: Obtain and store the API key — **ASK THE HUMAN**

rejestr.io requires a paid API key tied to a human-owned account (sign-up and plan selection happen at https://rejestr.io — this cannot be automated by an agent). Ask the user:

> "You'll need a rejestr.io API key to use this server. If you don't have one yet, sign up at https://rejestr.io and generate one from your account. What's your `REJESTR_IO_API_KEY`?"

Once you have it:

```bash
cp .env.example .env
```

Then set `REJESTR_IO_API_KEY=<the key the human gave you>` in `.env`. Do not print the key back to the user in plaintext in a shared/logged context if you can avoid it, and never commit `.env` to version control (it's already gitignored).

## Step 3: Note the absolute path to this repo

Every client config below needs the absolute filesystem path to this repository (the directory containing `pyproject.toml`). Resolve it now, e.g.:

```bash
pwd
```

Substitute that path everywhere `<REPO_PATH>` appears below.

## Step 4: Choose a transport

- **stdio** (default) — the client spawns this server as a subprocess and talks to it over stdin/stdout. Use this for Claude Desktop, Claude Code, and VS Code/Copilot agent mode — anything that runs on the same machine as the client.
- **http** — the server listens on a TCP port. Use this only if the client cannot spawn local subprocesses (e.g. a remote MCP connector) or if you're centralizing one server instance for multiple clients. Defaults to `127.0.0.1:8000` (loopback-only, no auth). To expose it beyond localhost, set `MCP_HTTP_AUTH_TOKEN` (an ASCII-only shared secret) and `MCP_HTTP_HOST` — see [README.md § Zmienne środowiskowe](README.md#zmienne-środowiskowe) for the full security notes before doing this. **ASK THE HUMAN** before binding to anything other than `127.0.0.1`, since it changes their network exposure.

Most tools below use stdio. Only fall back to http if the tool you're configuring genuinely requires a network endpoint.

## Step 5: Register the server with your specific tool

Pick the section matching the tool you're operating as (or the tool the human asked you to configure).

### Claude Desktop

Edit the app's config file — **ASK THE HUMAN** to confirm their OS if you can't detect it, since the path differs:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Add (or merge into an existing `mcpServers` object):

```json
{
  "mcpServers": {
    "rejestr-io": {
      "command": "uv",
      "args": ["run", "--directory", "<REPO_PATH>", "rejestr-io-mcp"],
      "env": {
        "REJESTR_IO_API_KEY": "<the human's key>"
      }
    }
  }
}
```

Restart Claude Desktop for the change to take effect.

### Claude Code

Two equivalent options:

**CLI (preferred — no manual JSON editing):**

```bash
claude mcp add rejestr-io --env REJESTR_IO_API_KEY=<the human's key> -- uv run --directory <REPO_PATH> rejestr-io-mcp
```

**Or a project-level `.mcp.json`** at the repo root the user is working in (same schema as Claude Desktop above, `mcpServers` key). Prefer the CLI form unless the human specifically wants the config checked into a project.

### GitHub Copilot (VS Code agent mode)

VS Code's native MCP support (Copilot Chat, agent mode) reads `.vscode/mcp.json` in the workspace. Its schema uses a top-level `servers` key (not `mcpServers`) and an explicit `type` field:

```json
{
  "servers": {
    "rejestr-io": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "<REPO_PATH>", "rejestr-io-mcp"],
      "env": {
        "REJESTR_IO_API_KEY": "<the human's key>"
      }
    }
  }
}
```

If VS Code prompts for confirmation before starting the server, that's expected — approve it once the config is correct.

### OpenAI Codex CLI

Codex reads `~/.codex/config.toml`. Add a table under `mcp_servers`:

```toml
[mcp_servers.rejestr-io]
command = "uv"
args = ["run", "--directory", "<REPO_PATH>", "rejestr-io-mcp"]

[mcp_servers.rejestr-io.env]
REJESTR_IO_API_KEY = "<the human's key>"
```

### ChatGPT (Connectors)

ChatGPT's MCP connector support expects a network-reachable server (it cannot spawn a local stdio subprocess the way desktop clients do), configured through the ChatGPT UI (Settings → Connectors), not a config file. This means you must run this server with `--transport http` and make it reachable from wherever ChatGPT's servers can reach it — typically via a reverse proxy or tunnel (e.g. `ngrok`, `cloudflared`), not by exposing your home network directly. **ASK THE HUMAN** how they want to expose it before doing anything network-facing; setting up a public tunnel is a decision they should confirm, not one to make unilaterally.

Once the server is reachable at some `https://<public-host>/mcp` URL with `MCP_HTTP_AUTH_TOKEN` set:

1. In ChatGPT: Settings → Connectors → add a custom connector.
2. Server URL: `https://<public-host>/mcp`.
3. Auth: bearer token, value = your `MCP_HTTP_AUTH_TOKEN`.

Connector UI details change fairly often on OpenAI's side — if the flow above doesn't match what's on screen, follow ChatGPT's current in-app instructions for adding a custom MCP connector with bearer-token auth.

## Step 6: Verify

After registering with any client, verify the server actually starts and authenticates correctly by calling the free, side-effect-free `get_account_balance` tool through that client — it requires no parameters and confirms both that the process starts and that `REJESTR_IO_API_KEY` is valid. If it fails, check:

- `Configuration error: REJESTR_IO_API_KEY environment variable is required` → the key wasn't passed through in the client's `env` block — re-check Step 5.
- The server exits immediately → confirm `uv sync --extra dev` (Step 1) completed and `<REPO_PATH>` is correct and absolute.
- A 401/`AuthError` from rejestr.io itself → the key is present but invalid/expired — go back to Step 2 and **ASK THE HUMAN** to confirm the key.

If it works, list the available tools and confirm all 12 from [README.md § Narzędzia MCP](README.md#narzędzia-mcp) are present.
