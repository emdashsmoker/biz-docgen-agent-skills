#!/usr/bin/env bash
# render.sh <file.pptx> <out_dir> [dpi]  : pptx → pdf → png (per slide). For review
set -euo pipefail
PPTX="$1"; OUT="$2"; DPI="${3:-60}"
mkdir -p "$OUT"
soffice --headless --convert-to pdf --outdir "$OUT" "$PPTX" >/dev/null 2>&1
PDF="$OUT/$(basename "${PPTX%.pptx}").pdf"
pdftoppm -r "$DPI" -png "$PDF" "$OUT/s"
ls "$OUT"/s-*.png | wc -l
