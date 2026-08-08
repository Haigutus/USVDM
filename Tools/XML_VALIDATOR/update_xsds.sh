#!/usr/bin/env bash
# Refresh ENTSO-E ESMP / CIM XSD package under XSD/CIM_*
# Other trees (EDIGAS, CGMES, OPDM, …) are left untouched.
set -euo pipefail

cd "$(dirname "$0")"

# Override when ENTSO-E renames the package:
#   XSD_URL=https://... ./update_xsds.sh
# See: https://www.entsoe.eu/publications/electronic-data-interchange-edi-library/
XSD_URL="${XSD_URL:-https://www.entsoe.eu/Documents/EDI/Library/CIM_xsd_package_v2026.7z}"

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

ARCHIVE="$TMPDIR/package"
echo "Downloading: $XSD_URL"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL -o "$ARCHIVE" "$XSD_URL"
elif command -v wget >/dev/null 2>&1; then
  wget -q -O "$ARCHIVE" "$XSD_URL"
else
  echo "ERROR: need curl or wget" >&2
  exit 1
fi

EXTRACT="$TMPDIR/extract"
mkdir -p "$EXTRACT"

_extract_7z() {
  local bin
  bin="$(command -v 7z || command -v 7za || true)"
  if [[ -z "$bin" ]]; then
    echo "ERROR: archive needs 7z — install p7zip-full" >&2
    exit 1
  fi
  "$bin" x -y -o"$EXTRACT" "$ARCHIVE" >/dev/null
}

kind="$(file -b "$ARCHIVE" 2>/dev/null || echo unknown)"
case "$kind" in
  *7-zip*|*7z*)
    _extract_7z
    ;;
  *Zip*|*zip*)
    unzip -qo "$ARCHIVE" -d "$EXTRACT"
    ;;
  *)
    # Try 7z first (handles many formats), then unzip
    if command -v 7z >/dev/null 2>&1 || command -v 7za >/dev/null 2>&1; then
      _extract_7z
    else
      unzip -qo "$ARCHIVE" -d "$EXTRACT"
    fi
    ;;
esac

# Remove previous CIM packages only
rm -rf XSD/CIM_*

shopt -s nullglob
cim_dirs=("$EXTRACT"/CIM_*)
if ((${#cim_dirs[@]})); then
  for d in "${cim_dirs[@]}"; do
    mv "$d" XSD/
    echo "Installed: XSD/$(basename "$d")"
  done
else
  dest="XSD/CIM_updated"
  mkdir -p "$dest"
  tops=("$EXTRACT"/*)
  if ((${#tops[@]} == 1)) && [[ -d "${tops[0]}" ]]; then
    # single top-level folder — keep its name if it looks like CIM_*, else flatten
    name="$(basename "${tops[0]}")"
    if [[ "$name" == CIM_* ]]; then
      rmdir "$dest"
      mv "${tops[0]}" "XSD/$name"
      echo "Installed: XSD/$name"
    else
      mv "${tops[0]}"/* "$dest/" 2>/dev/null || true
      echo "Installed: $dest (from $name)"
    fi
  else
    mv "$EXTRACT"/* "$dest/" 2>/dev/null || true
    echo "Installed: $dest"
  fi
fi

echo "Done. Restart the app or rebuild the image to reload the XSD index."
