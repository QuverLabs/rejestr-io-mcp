#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

merge() {
  osascript -l JavaScript "$SCRIPT_DIR/merge_claude_config.js" "$@" > /dev/null
}

assert_json_field() {
  local file="$1" py_expr="$2" expected="$3"
  local actual
  actual="$(python3 -c "import json; d = json.load(open('$file')); print($py_expr)")"
  if [ "$actual" != "$expected" ]; then
    echo "FAIL: $py_expr in $file: expected '$expected', got '$actual'" >&2
    exit 1
  fi
}

# Case 1: fresh/missing file
CONFIG1="$TMP_DIR/fresh.json"
merge "$CONFIG1" "rejestr-io" "/bin/rejestr-io-mcp" "REJESTR_IO_API_KEY" "key1"
assert_json_field "$CONFIG1" "d['mcpServers']['rejestr-io']['command']" "/bin/rejestr-io-mcp"
assert_json_field "$CONFIG1" "d['mcpServers']['rejestr-io']['env']['REJESTR_IO_API_KEY']" "key1"
echo "PASS: fresh file"

# Case 2: existing unrelated entry preserved
CONFIG2="$TMP_DIR/existing.json"
cat > "$CONFIG2" << 'EOF'
{"mcpServers":{"other-server":{"command":"foo"}}}
EOF
merge "$CONFIG2" "rejestr-io" "/bin/rejestr-io-mcp" "REJESTR_IO_API_KEY" "key2"
assert_json_field "$CONFIG2" "d['mcpServers']['other-server']['command']" "foo"
assert_json_field "$CONFIG2" "d['mcpServers']['rejestr-io']['command']" "/bin/rejestr-io-mcp"
echo "PASS: existing entry preserved"

# Case 3: re-run replaces, does not duplicate, still preserves unrelated entry
merge "$CONFIG2" "rejestr-io" "/new/path" "REJESTR_IO_API_KEY" "key3"
assert_json_field "$CONFIG2" "d['mcpServers']['other-server']['command']" "foo"
assert_json_field "$CONFIG2" "d['mcpServers']['rejestr-io']['command']" "/new/path"
assert_json_field "$CONFIG2" "d['mcpServers']['rejestr-io']['env']['REJESTR_IO_API_KEY']" "key3"
echo "PASS: re-run replaces without duplicating"

# Case 4: backup file created on merge into an existing config
CONFIG3="$TMP_DIR/backup_test.json"
echo '{"mcpServers":{"other-server":{"command":"foo"}}}' > "$CONFIG3"
merge "$CONFIG3" "rejestr-io" "/bin/rejestr-io-mcp" "REJESTR_IO_API_KEY" "key1"
if [ ! -f "$CONFIG3.bak" ]; then
  echo "FAIL: backup file $CONFIG3.bak was not created" >&2
  exit 1
fi
if ! grep -q '"other-server"' "$CONFIG3.bak"; then
  echo "FAIL: backup file does not contain the pre-merge content" >&2
  exit 1
fi
echo "PASS: backup file created on merge"

echo "All merge_claude_config.js tests passed."
