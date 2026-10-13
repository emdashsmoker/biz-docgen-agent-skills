#!/usr/bin/env python3
"""extract_images.py: 제출 원본(pdf, hwpx, pptx, docx)에서 삽입 가능한 이미지를 추출
사용: python3 extract_images.py <입력 파일> <출력 디렉터리> [--min-px 64] [--min-kb 2]
산출: 출력 디렉터리에 img_0001.png 형식 파일과 manifest.json
manifest.json 항목: {file, page(또는 slide), w, h, bytes, ratio, kind}
kind 판정: logo(작은 이미지와 가로형 CI), photo(사진), diagram(도식으로 추정), map(가로세로 비 1에 가까운 대형)
사용 지침 (SKILL.md 와 동일)
- 채택 대상: 발주처 사업 개념도와 추진체계도, 유사 실적의 현장 사진과 결과물 화면, 차트, 구조도와 아키텍처 도식, 지도, 회사·기관 로고
- 미채택 대상: 표를 캡처한 이미지(표로 재구성), 불릿과 배경 조각, 저해상도 이미지, 다른 제안사의 도식
- 판정은 사람이 수행. 스크립트는 후보만 제시
"""
import json
import sys
import zipfile
from pathlib import Path


def kind_of(w, h, nbytes):
    r = w / h if h else 1
    if max(w, h) < 260 and 0.5 <= r <= 6.0:
        return "logo"  # CI 와 기관 로고는 작게 삽입되는 경우가 많음
    if w < 400 and r > 1.6:
        return "logo"
    if 0.8 <= r <= 1.3 and w >= 800:
        return "map"
    if nbytes / max(1, w * h) > 0.6:
        return "photo"
    return "diagram"


PNG_SAFE_MODES = ("1", "L", "LA", "P", "RGB", "RGBA", "I;16")  # PNG로 저장 가능한 색 모드. 그 밖(CMYK 등)은 RGB로 변환
MAX_OBJECT_DEPTH = 15   # 도형 묶음(Form XObject) 안의 이미지까지 찾는 깊이


def from_pdf(src, out):
    """쪽 본문에 실제로 배치된 이미지 객체를 원본 해상도로 추출. 이미지 마스크(투명도)는 적용하지 않음"""
    import hashlib
    import io
    import pypdfium2 as pdfium
    import pypdfium2.raw as pdfium_c
    doc = pdfium.PdfDocument(str(src))
    items = []
    seen = set()
    try:
        for pno in range(len(doc)):
            objs = doc[pno].get_objects(filter=(pdfium_c.FPDF_PAGEOBJ_IMAGE,), max_depth=MAX_OBJECT_DEPTH)
            for n, obj in enumerate(objs):
                key = hashlib.sha1(obj.get_data(decode_simple=False)).hexdigest()
                if key in seen:
                    continue  # 같은 이미지가 여러 쪽에 재사용된 경우 1회만
                seen.add(key)
                try:
                    image = obj.get_bitmap(render=False).to_pil()
                except Exception:
                    continue  # 해석할 수 없는 이미지 형식은 후보에서 제외
                if image.mode not in PNG_SAFE_MODES:
                    image = image.convert("RGB")
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                items.append((f"p{pno + 1}_{n + 1}", buf.getvalue(), image.width, image.height, pno + 1))
    finally:
        doc.close()
    return items


def from_zip(src, out, prefix):
    """hwpx, pptx, docx 는 ZIP 내부의 미디어 파일을 그대로 사용"""
    items = []
    with zipfile.ZipFile(src) as zf:
        for name in zf.namelist():
            low = name.lower()
            if not low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".emf", ".wmf")):
                continue
            if not any(k in low for k in ("media", "bindata", "image")) or low.startswith("preview/"):
                continue  # hwpx의 Preview/PrvImage.png는 첫 쪽 미리보기라 삽입 후보가 아님
            data = zf.read(name)
            items.append((Path(name).stem, data, 0, 0, None))
    return items


def size_of(data):
    """PNG, JPEG, GIF 의 픽셀 크기. 실패 시 (0, 0)"""
    try:
        if data[:2] == b"\x89P":
            return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        if data[:2] == b"GI":
            return int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little")
        if data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                m = data[i + 1]
                if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                    return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
                i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    except Exception:
        pass
    return 0, 0


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        raise SystemExit(__doc__)
    src, out = Path(args[0]), Path(args[1])
    # 로고와 CI 는 작게 들어가므로 하한을 낮춤. 불릿과 배경 조각은 최소 변 길이와 면적으로 거름
    min_px = int(args[args.index("--min-px") + 1]) if "--min-px" in args else 64
    min_kb = int(args[args.index("--min-kb") + 1]) if "--min-kb" in args else 2
    out.mkdir(parents=True, exist_ok=True)
    ext = src.suffix.lower()
    if ext == ".pdf":
        items = from_pdf(src, out)
    elif ext in (".hwpx", ".pptx", ".docx", ".xlsx"):
        items = from_zip(src, out, ext[1:])
    else:
        raise SystemExit(f"미지원 형식 {ext}. pdf, hwpx, pptx, docx 만 지원")
    manifest = []
    k = 0
    for tag, data, w, h, page in items:
        if not w or not h:
            w, h = size_of(data)
        if len(data) < min_kb * 1024 or min(w, h) < min_px or w * h < min_px * min_px * 2:
            continue  # 불릿과 배경 조각 제외 (한 변 64px 미만이거나 면적이 매우 작은 이미지)
        k += 1
        suffix = ".png" if data[:2] == b"\x89P" else (".jpg" if data[:2] == b"\xff\xd8" else Path(tag).suffix or ".bin")
        name = f"img_{k:04d}{suffix}"
        (out / name).write_bytes(data)
        manifest.append({"file": str(out / name), "source": src.name, "page": page, "w": w, "h": h,
                         "bytes": len(data), "ratio": round(w / h, 2) if h else 0, "kind": kind_of(w, h, len(data))})
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out}/manifest.json images={len(manifest)} (전체 {len(items)}건 중 하한 미달 제외)")
    for m in manifest[:20]:
        print(f"  {Path(m['file']).name} {m['w']}x{m['h']} {m['bytes'] // 1024}KB {m['kind']}" + (f" p{m['page']}" if m['page'] else ""))


if __name__ == "__main__":
    main()
