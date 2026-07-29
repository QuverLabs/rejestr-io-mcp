#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "$SCRIPT_DIR/lib.sh"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# Case 1: fresh/missing file
TOML1="$TMP_DIR/fresh.toml"
merge_codex_toml "$TOML1" "/bin/rejestr-io-mcp" "key1"
grep -q '^\[mcp_servers.rejestr-io\]$' "$TOML1" || { echo "FAIL: missing header (fresh)"; exit 1; }
grep -q 'command = "/bin/rejestr-io-mcp"' "$TOML1" || { echo "FAIL: missing command (fresh)"; exit 1; }
echo "PASS: fresh file"

# Case 2: existing unrelated entry preserved
TOML2="$TMP_DIR/existing.toml"
cat > "$TOML2" << 'EOF'
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]

[mcp_servers.context7.env]
FOO = "bar"
EOF
merge_codex_toml "$TOML2" "/bin/rejestr-io-mcp" "key2"
grep -q '^\[mcp_servers.context7\]$' "$TOML2" || { echo "FAIL: context7 header dropped"; exit 1; }
grep -q 'FOO = "bar"' "$TOML2" || { echo "FAIL: context7 env dropped"; exit 1; }
grep -q 'command = "/bin/rejestr-io-mcp"' "$TOML2" || { echo "FAIL: rejestr-io command missing"; exit 1; }
echo "PASS: existing entry preserved"

# Case 3: re-run replaces, does not duplicate, still preserves unrelated entry
merge_codex_toml "$TOML2" "/new/path" "key3"
context7_count=$(grep -c '^\[mcp_servers.context7\]$' "$TOML2")
rejestr_count=$(grep -c '^\[mcp_servers.rejestr-io\]$' "$TOML2")
[ "$context7_count" -eq 1 ] || { echo "FAIL: context7 header count is $context7_count"; exit 1; }
[ "$rejestr_count" -eq 1 ] || { echo "FAIL: rejestr-io header count is $rejestr_count (expected 1, no duplicate)"; exit 1; }
grep -q 'command = "/new/path"' "$TOML2" || { echo "FAIL: rejestr-io command not updated"; exit 1; }
echo "PASS: re-run replaces without duplicating"

# Case 4: quote/backslash escaping
TOML4="$TMP_DIR/escaping.toml"
merge_codex_toml "$TOML4" "/bin/rejestr-io-mcp" 'key with "quote" and \backslash'
grep -F 'REJESTR_IO_API_KEY = "key with \"quote\" and \\backslash"' "$TOML4" > /dev/null || { echo "FAIL: escaping incorrect"; cat "$TOML4"; exit 1; }
echo "PASS: quote/backslash escaping"

# Case 5: backup file created on merge into an existing TOML file
TOML5="$TMP_DIR/backup_test.toml"
cat > "$TOML5" << 'EOF'
[mcp_servers.context7]
command = "npx"
EOF
merge_codex_toml "$TOML5" "/bin/rejestr-io-mcp" "key1"
if [ ! -f "$TOML5.bak" ]; then
  echo "FAIL: backup file $TOML5.bak was not created"; exit 1
fi
if ! grep -q 'context7' "$TOML5.bak"; then
  echo "FAIL: backup file does not contain the pre-merge content"; exit 1
fi
echo "PASS: backup file created on merge (TOML)"

echo "All lib.sh tests passed."
