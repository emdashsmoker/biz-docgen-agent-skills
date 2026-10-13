#!/usr/bin/env python3
"""extract_images.py: extracts insertable images from submitted originals (pdf, hwpx, pptx, docx)
Usage: python3 extract_images.py <input file> <output directory> [--min-px 64] [--min-kb 2]
Output: img_0001.png style files and manifest.json in the output directory
manifest.json entries: {file, page(or slide), w, h, bytes, ratio, kind}
kind verdict: logo (small images and landscape CI), photo (photographs), diagram (presumed diagram), map (large, aspect ratio near 1)
Usage guidance (same as SKILL.md)
- Adopt: the client's project concept and implementation structure diagrams, field photos and result screens from similar track records, charts, structure and architecture diagrams, maps, company and agency logos
- Do not adopt: images capturing tables (rebuild as tables), bullet and background fragments, low-resolution images, other proposers' diagrams
- A person makes the verdict. The script only presents candidates
"""
import json
import sys
import zipfile
from pathlib import Path


def kind_of(w, h, nbytes):
    r = w / h if h else 1
    if max(w, h) < 260 and 0.5 <= r <= 6.0:
        return "logo"  # CI and agency logos are often inserted small
    if w < 400 and r > 1.6:
        return "logo"
    if 0.8 <= r <= 1.3 and w >= 800:
        return "map"
    if nbytes / max(1, w * h) > 0.6:
        return "photo"
    return "diagram"


PNG_SAFE_MODES = ("1", "L", "LA", "P", "RGB", "RGBA", "I;16")  # color modes PNG can store. Others (CMYK, etc.) are converted to RGB
MAX_OBJECT_DEPTH = 15   # depth for finding images inside shape groups (Form XObject)


def from_pdf(src, out):
    """Extract image objects actually placed in the page body at original resolution. Image masks (transparency) are not applied"""
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
                    continue  # an image reused on several pages is taken once
                seen.add(key)
                try:
                    image = obj.get_bitmap(render=False).to_pil()
                except Exception:
                    continue  # image formats that cannot be decoded are excluded from candidates
                if image.mode not in PNG_SAFE_MODES:
                    image = image.convert("RGB")
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                items.append((f"p{pno + 1}_{n + 1}", buf.getvalue(), image.width, image.height, pno + 1))
    finally:
        doc.close()
    return items


def from_zip(src, out, prefix):
    """hwpx, pptx, and docx use the media files inside the ZIP as is"""
    items = []
    with zipfile.ZipFile(src) as zf:
        for name in zf.namelist():
            low = name.lower()
            if not low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".emf", ".wmf")):
                continue
            if not any(k in low for k in ("media", "bindata", "image")) or low.startswith("preview/"):
                continue  # hwpx Preview/PrvImage.png is a first-page preview, not an insertion candidate
            data = zf.read(name)
            items.append((Path(name).stem, data, 0, 0, None))
    return items


def size_of(data):
    """Pixel size of PNG, JPEG, GIF. (0, 0) on failure"""
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
    # logos and CI go in small, so the lower bound is lowered. Bullet and background fragments are filtered by minimum side length and area
    min_px = int(args[args.index("--min-px") + 1]) if "--min-px" in args else 64
    min_kb = int(args[args.index("--min-kb") + 1]) if "--min-kb" in args else 2
    out.mkdir(parents=True, exist_ok=True)
    ext = src.suffix.lower()
    if ext == ".pdf":
        items = from_pdf(src, out)
    elif ext in (".hwpx", ".pptx", ".docx", ".xlsx"):
        items = from_zip(src, out, ext[1:])
    else:
        raise SystemExit(f"Unsupported format {ext}. Only pdf, hwpx, pptx, docx are supported")
    manifest = []
    k = 0
    for tag, data, w, h, page in items:
        if not w or not h:
            w, h = size_of(data)
        if len(data) < min_kb * 1024 or min(w, h) < min_px or w * h < min_px * min_px * 2:
            continue  # exclude bullet and background fragments (one side under 64px or a very small area)
        k += 1
        suffix = ".png" if data[:2] == b"\x89P" else (".jpg" if data[:2] == b"\xff\xd8" else Path(tag).suffix or ".bin")
        name = f"img_{k:04d}{suffix}"
        (out / name).write_bytes(data)
        manifest.append({"file": str(out / name), "source": src.name, "page": page, "w": w, "h": h,
                         "bytes": len(data), "ratio": round(w / h, 2) if h else 0, "kind": kind_of(w, h, len(data))})
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out}/manifest.json images={len(manifest)} (out of {len(items)} total, below-threshold images excluded)")
    for m in manifest[:20]:
        print(f"  {Path(m['file']).name} {m['w']}x{m['h']} {m['bytes'] // 1024}KB {m['kind']}" + (f" p{m['page']}" if m['page'] else ""))


if __name__ == "__main__":
    main()
