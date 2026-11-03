#!/bin/sh
# Fetch Style's TMPx (Turbo Macro Pro cross assembler) into .tools/tmpx.
# https://turbo.style64.org/  -  release: http://style64.org/release/tmpx-v1.1.0-style
# TMPx 1.1.0 (2015) has no arm64 macOS build: on Apple Silicon the x86_64
# binary needs Rosetta 2. If that is unavailable, the Makefile falls back to
# 64tass in Turbo Assembler mode (ASM=64tass).
set -eu
URL=https://style64.org/file/TMPx_v1.1.0-STYLE.zip
SHA256=1f23932919293d1a27c94f185168c8ae684582fef9190516f340c4b5dac75199
DEST=$(cd "$(dirname "$0")/.." && pwd)/.tools

case "$(uname -s)-$(uname -m)" in
  Darwin-*)        PLAT=maxosx-x86_64 ;;   # sic, the archive's spelling
  Linux-x86_64)    PLAT=linux-x86_64 ;;
  Linux-i?86)      PLAT=linux-i386 ;;
  FreeBSD-amd64)   PLAT=freebsd-x86_64 ;;
  *) echo "no TMPx build for $(uname -s)-$(uname -m); use ASM=64tass" >&2; exit 1 ;;
esac

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
curl -fsSL -o "$TMP/tmpx.zip" "$URL"
echo "$SHA256  $TMP/tmpx.zip" | shasum -a 256 -c -
unzip -q "$TMP/tmpx.zip" -d "$TMP"
mkdir -p "$DEST"
cp "$TMP/TMPx_v1.1.0-STYLE/$PLAT/tmpx" "$DEST/tmpx"
chmod +x "$DEST/tmpx"
xattr -d com.apple.quarantine "$DEST/tmpx" 2>/dev/null || true
"$DEST/tmpx" --version | head -1
