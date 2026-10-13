#!/usr/bin/env bash
# topdf.sh <file.pptx> [out_dir]  : 납품용 PDF 생성 (기본은 pptx 와 같은 폴더)
set -euo pipefail
PPTX="$1"; OUT="${2:-$(dirname "$PPTX")}"
mkdir -p "$OUT"
soffice --headless --convert-to pdf --outdir "$OUT" "$PPTX" >/dev/null 2>&1
PDF="$OUT/$(basename "${PPTX%.pptx}").pdf"
[ -f "$PDF" ] || { echo "PDF 변환 실패. LibreOffice 설치를 확인할 것" >&2; exit 1; }
echo "$PDF"
