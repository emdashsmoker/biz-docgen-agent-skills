#!/usr/bin/env bash
# topdf.sh <file.pptx> [out_dir]  : creates the delivery PDF (default: same folder as the pptx)
set -euo pipefail
PPTX="$1"; OUT="${2:-$(dirname "$PPTX")}"
mkdir -p "$OUT"
soffice --headless --convert-to pdf --outdir "$OUT" "$PPTX" >/dev/null 2>&1
PDF="$OUT/$(basename "${PPTX%.pptx}").pdf"
[ -f "$PDF" ] || { echo "PDF conversion failed. Check the LibreOffice installation" >&2; exit 1; }
echo "$PDF"
