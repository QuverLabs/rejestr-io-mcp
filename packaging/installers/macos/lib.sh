#!/usr/bin/env bash
# Shared helpers for the macOS installer. Sourced, not executed directly.

toml_basic_string() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  printf '"%s"' "$s"
}

merge_codex_toml() {
  local toml_path="$1"
  local bin_path="$2"
  local api_key="$3"

  mkdir -p "$(dirname "$toml_path")"
  if [ -f "$toml_path" ]; then
    cp "$toml_path" "$toml_path.bak"
  fi
  touch "$toml_path"

  local kept
  kept=$(awk -v h1="[mcp_servers.rejestr-io]" -v h2="[mcp_servers.rejestr-io.env]" '
    {
      if ($0 == h1 || $0 == h2) { skip = 1; next }
      if (skip && substr($0,1,1) == "[") { skip = 0 }
      if (skip) { next }
      print $0
    }
  ' "$toml_path")

  {
    if [ -n "$kept" ]; then
      printf '%s\n\n' "$kept"
    fi
    echo "[mcp_servers.rejestr-io]"
    printf 'command = %s\n' "$(toml_basic_string "$bin_path")"
    echo ""
    echo "[mcp_servers.rejestr-io.env]"
    printf 'REJESTR_IO_API_KEY = %s\n' "$(toml_basic_string "$api_key")"
  } > "$toml_path"
}
