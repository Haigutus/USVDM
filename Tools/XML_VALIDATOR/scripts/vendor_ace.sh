#!/usr/bin/env bash
# Download Ace editor files into assets/ace/ for offline use.
# Usage: ./scripts/vendor_ace.sh [version]
set -euo pipefail
cd "$(dirname "$0")/.."
VER="${1:-1.36.5}"
BASE="https://cdnjs.cloudflare.com/ajax/libs/ace/${VER}"
DEST="assets/ace"
mkdir -p "$DEST"

files=(
  ace.min.js
  mode-xml.js
  mode-text.js
  theme-monokai.js
  worker-xml.js
  worker-base.js
  ext-searchbox.js
  ext-language_tools.js
  ext-prompt.js
  ext-keybinding_menu.js
  ext-settings_menu.js
  ext-error_marker.js
)

echo "Vendoring Ace ${VER} -> ${DEST}"
for f in "${files[@]}"; do
  echo -n "  $f ... "
  if curl -fsSL -o "$DEST/$f" "$BASE/$f"; then
    echo "ok ($(wc -c < "$DEST/$f") bytes)"
  else
    echo "FAILED" >&2
    exit 1
  fi
done
echo "Done. Commit assets/ace/ after upgrading."
