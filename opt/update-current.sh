#!/bin/sh
set -eu
if [ $# -ne 3 ]; then echo "usage: $0 <tool> <pkg> <digest>" >&2; exit 2; fi
TOOL="$1"; PKG="$2"; DIGEST="$3"
SRC="/opt/mcp/${PKG}@${DIGEST}"
[ -d "$SRC" ] || { echo "no such package: $SRC" >&2; exit 1; }
mkdir -p "/opt/mcp/current/$TOOL"
rm -f "/opt/mcp/current/$TOOL/bin"
ln -s "$SRC/bin" "/opt/mcp/current/$TOOL/bin"
echo "current set: $TOOL -> $SRC"
