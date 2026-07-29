#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "$SCRIPT_DIR/lib.sh"

SOURCE_BINARY="$SCRIPT_DIR/rejestr-io-mcp"
INSTALL_DIR="$HOME/Library/Application Support/rejestr-io-mcp"
INSTALL_BINARY="$INSTALL_DIR/rejestr-io-mcp"
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
CODEX_CONFIG="$HOME/.codex/config.toml"

echo "=== Instalator rejestr-io-mcp ==="
echo ""

if [ ! -f "$SOURCE_BINARY" ]; then
  echo "BŁĄD: nie znaleziono pliku rejestr-io-mcp w tym samym folderze co instalator." >&2
  echo "Upewnij się, że rozpakowałeś/aś całe archiwum ZIP, a nie tylko ten plik." >&2
  read -r -p "Naciśnij Enter, aby zamknąć to okno..." _
  exit 1
fi

mkdir -p "$INSTALL_DIR"
cp "$SOURCE_BINARY" "$INSTALL_BINARY"
chmod +x "$INSTALL_BINARY"
xattr -d com.apple.quarantine "$INSTALL_BINARY" 2>/dev/null || true
echo "Skopiowano rejestr-io-mcp do: $INSTALL_BINARY"

API_KEY=""
while [ -z "$API_KEY" ]; do
  read -r -s -p "Podaj swój klucz API rejestr.io: " API_KEY
  echo ""
  if [ -z "$API_KEY" ]; then
    echo "Klucz nie może być pusty, spróbuj ponownie."
  fi
done

osascript -l JavaScript "$SCRIPT_DIR/merge_claude_config.js" \
  "$CLAUDE_CONFIG" "rejestr-io" "$INSTALL_BINARY" "REJESTR_IO_API_KEY" "$API_KEY" > /dev/null
echo "Skonfigurowano Claude Desktop."

merge_codex_toml "$CODEX_CONFIG" "$INSTALL_BINARY" "$API_KEY"
echo "Skonfigurowano ChatGPT desktop / Codex CLI."

echo ""
echo "Gotowe! Uruchom ponownie Claude Desktop i/lub aplikację ChatGPT, aby zmiany zaczęły działać."
echo "W ChatGPT wpisz /mcp w oknie rozmowy, aby sprawdzić, czy serwer rejestr-io jest widoczny."
read -r -p "Naciśnij Enter, aby zamknąć to okno..." _
