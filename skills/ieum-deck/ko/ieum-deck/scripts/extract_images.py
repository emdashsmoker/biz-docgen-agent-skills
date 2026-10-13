#!/usr/bin/env python3
"""extract_images.py: 제출 원본(pdf, hwpx, pptx, docx)에서 삽입 가능한 이미지를 추출
사용: python3 extract_images.py <입력 파일> <출력 디렉터리> [--min-px 64] [--min-kb 2]
산출: 출력 디렉터리에 img_0001.png 형식 파일과 manifest.json
manifest.json 항목: {file, source, page, member, w, h, bytes, ratio, kind}
- page 는 PDF 쪽 번호이며 hwpx, docx, pptx 는 null (파일 안에 쪽 구분이 없음)
- member 는 hwpx, docx, pptx 의 ZIP 안 이미지 경로이며 PDF 는 null. 본문 XML 에서 이 파일을 참조하는 위치로 쓰임새를 확인
kind 판정: logo(작은 이미지와 가로형 CI), photo(사진), diagram(도식으로 추정), map(가로세로 비 1에 가까운 대형)
사용 지침 (SKILL.md 와 동일)
- 재사용 대상: 유사 실적 사진, 지도, 현장 사진, 회사·기관 로고, 재현이 어려운 복잡한 아키텍처 도식
- 재사용 금지: 본 스킬이 재현하는 방법론 도식, 차트, 모듈·Task 구조도, 표를 캡처한 이미지
- 판정은 사람이 수행. 스크립트는 후보만 제시
"""
import io
import json
import sys
import zipfile
from pathlib import Path

PNG_MODES = ("L", "LA", "P", "RGB", "RGBA")  # 이 목록 밖의 색 모드는 RGB 로 바꾸어 저장
THUMBNAIL_DIRS = ("preview/", "docprops/")  # 본문 이미지가 아닌 문서 썸네일 폴더 (hwpx Preview/PrvImage.png, docx 와 pptx docProps/thumbnail)


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


def resolved(obj, key):
    """PDF 사전에서 key 값을 간접 참조까지 풀어서 반환. 없으면 None"""
    value = obj.get(key) if isinstance(obj, dict) else None
    return value.get_object() if value is not None else None


def pdf_image_streams(holder, seen_forms):
    """쪽이나 양식(Form XObject) 리소스에 등록된 이미지 스트림 목록 [(객체 번호, 스트림)]. 양식 안의 이미지까지 탐색
    인라인 이미지는 제외. 쪽 내용 스트림 전체를 해석해야 하여 대용량 문서에서 수십 초가 걸림"""
    xobjects = resolved(resolved(holder, "/Resources"), "/XObject")
    if not isinstance(xobjects, dict):
        return []
    found = []
    for name in xobjects:
        raw = xobjects.raw_get(name)
        obj = raw.get_object()
        key = getattr(raw, "idnum", id(obj))
        subtype = obj.get("/Subtype") if isinstance(obj, dict) else None
        if subtype == "/Image":
            found.append((key, obj))
        elif subtype == "/Form" and key not in seen_forms:
            seen_forms.add(key)  # 서로 참조하는 양식의 무한 탐색 방지
            found.extend(pdf_image_streams(obj, seen_forms))
    return found


def from_pdf(src, out):
    """pypdf(BSD 라이선스)로 쪽 리소스의 이미지를 디코딩하여 PNG 로 변환. 디코딩할 수 없는 이미지는 건너뜀"""
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)  # 손상 PDF 의 경고 로그가 후보 목록 출력을 가리지 않도록
    items = []
    seen = set()
    skipped = 0
    for pno, page in enumerate(PdfReader(str(src)).pages, 1):
        try:
            streams = pdf_image_streams(page, set())
        except Exception:
            skipped += 1
            continue
        for key, xobj in streams:
            if key in seen:
                continue  # 같은 이미지가 여러 쪽에 재사용된 경우 1회만
            seen.add(key)
            try:
                pil = xobj.decode_as_image()
                if pil.mode not in PNG_MODES:
                    pil = pil.convert("RGB")  # CMYK 등 PNG 로 저장할 수 없는 색공간
                buf = io.BytesIO()
                pil.save(buf, "PNG")
            except Exception:
                skipped += 1
                continue
            items.append((None, buf.getvalue(), pil.width, pil.height, pno))
    if skipped:
        print(f"읽지 못한 쪽 또는 이미지 {skipped}건 제외", file=sys.stderr)
    return items


def bmp_to_png(data):
    """BMP 를 PNG 로 변환 (크기 판독과 PPTX 삽입을 PNG 기준으로 통일). 변환에 실패하면 원본을 돌려주며 크기 판독 단계에서 제외됨"""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        if img.mode not in PNG_MODES:
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()
    except Exception:
        return data


def from_zip(src, out, prefix):
    """hwpx, pptx, docx 는 ZIP 내부의 미디어 파일을 사용. 한글 문서에 많은 BMP 삽입 이미지는 PNG 로 변환"""
    items = []
    with zipfile.ZipFile(src) as zf:
        for name in zf.namelist():
            low = name.lower()
            if not low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".emf", ".wmf")):
                continue
            if low.startswith(THUMBNAIL_DIRS) or not any(k in low for k in ("media", "bindata", "image")):
                continue
            data = zf.read(name)
            if data[:2] == b"BM":
                data = bmp_to_png(data)
            # 쪽 번호가 없는 형식은 ZIP 안 경로(예: BinData/image3.bmp)로 본문의 참조 위치를 찾음
            items.append((name, data, 0, 0, None))
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
    for member, data, w, h, page in items:
        if not w or not h:
            w, h = size_of(data)
        if len(data) < min_kb * 1024 or min(w, h) < min_px or w * h < min_px * min_px * 2:
            continue  # 불릿과 배경 조각 제외 (한 변 64px 미만이거나 면적이 매우 작은 이미지)
        k += 1
        suffix = ".png" if data[:2] == b"\x89P" else ".jpg" if data[:2] == b"\xff\xd8" else ".gif" if data[:3] == b"GIF" else ".bin"
        name = f"img_{k:04d}{suffix}"
        (out / name).write_bytes(data)
        manifest.append({"file": str(out / name), "source": src.name, "page": page, "member": member, "w": w, "h": h,
                         "bytes": len(data), "ratio": round(w / h, 2) if h else 0, "kind": kind_of(w, h, len(data))})
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out}/manifest.json images={len(manifest)} (전체 {len(items)}건 중 하한 미달 제외)")
    for m in manifest[:20]:
        print(f"  {Path(m['file']).name} {m['w']}x{m['h']} {m['bytes'] // 1024}KB {m['kind']}" + (f" p{m['page']}" if m['page'] else ""))


if __name__ == "__main__":
    main()
