#!/usr/bin/env python3
"""extract_images.py: extracts insertable images from submitted source files (pdf, hwpx, pptx, docx)
Usage: python3 extract_images.py <input file> <output dir> [--min-px 64] [--min-kb 2]
Output: img_0001.png style files and manifest.json in the output dir
manifest.json entries: {file, source, page, member, w, h, bytes, ratio, kind}
- page is the PDF page number; hwpx, docx and pptx give null (the files hold no page breaks)
- member is the image path inside the ZIP for hwpx, docx and pptx, and null for PDF. Check how an image is used where the body XML references this file
kind judgment: logo (small images and horizontal CI), photo, diagram (estimated), map (large with an aspect ratio near 1)
Usage guidance (same as SKILL.md)
- Reuse: track record photos, maps, site photos, company and agency logos, complex architecture diagrams that are hard to reproduce
- Do not reuse: images capturing method diagrams, charts, module and Task structure charts or tables that this skill reproduces
- A person makes the judgment. The script only offers candidates
"""
import io
import json
import sys
import zipfile
from pathlib import Path

PNG_MODES = ("L", "LA", "P", "RGB", "RGBA")  # Color modes outside this list are saved after conversion to RGB
THUMBNAIL_DIRS = ("preview/", "docprops/")  # Document thumbnail folders that are not body images (hwpx Preview/PrvImage.png, docx and pptx docProps/thumbnail)


def kind_of(w, h, nbytes):
    r = w / h if h else 1
    if max(w, h) < 260 and 0.5 <= r <= 6.0:
        return "logo"  # CIs and agency logos are often inserted small
    if w < 400 and r > 1.6:
        return "logo"
    if 0.8 <= r <= 1.3 and w >= 800:
        return "map"
    if nbytes / max(1, w * h) > 0.6:
        return "photo"
    return "diagram"


def resolved(obj, key):
    """Returns the key value of a PDF dictionary with indirect references resolved. None if absent"""
    value = obj.get(key) if isinstance(obj, dict) else None
    return value.get_object() if value is not None else None


def pdf_image_streams(holder, seen_forms):
    """List of image streams registered in page or form (Form XObject) resources [(object number, stream)]. Also searches images inside forms
    Inline images are excluded. They would require parsing the whole page content stream, which takes tens of seconds on large documents"""
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
            seen_forms.add(key)  # Prevents endless search through forms that reference each other
            found.extend(pdf_image_streams(obj, seen_forms))
    return found


def from_pdf(src, out):
    """Decodes images in page resources with pypdf (BSD license) and converts them to PNG. Images that cannot be decoded are skipped"""
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)  # Keeps warning logs from damaged PDFs from hiding the candidate list output
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
                continue  # An image reused on several pages is taken once
            seen.add(key)
            try:
                pil = xobj.decode_as_image()
                if pil.mode not in PNG_MODES:
                    pil = pil.convert("RGB")  # Color spaces PNG cannot store, such as CMYK
                buf = io.BytesIO()
                pil.save(buf, "PNG")
            except Exception:
                skipped += 1
                continue
            items.append((None, buf.getvalue(), pil.width, pil.height, pno))
    if skipped:
        print(f"Skipped {skipped} unreadable pages or images", file=sys.stderr)
    return items


def bmp_to_png(data):
    """Converts BMP to PNG (size reading and PPTX insertion both work on PNG). On failure it returns the original, which the size reading step then drops"""
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
    """hwpx, pptx and docx use the media files inside the ZIP. BMP images, common in Hangul (hwp) documents, are converted to PNG"""
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
            # Formats without page numbers locate the reference in the body by the path inside the ZIP (e.g. BinData/image3.bmp)
            items.append((name, data, 0, 0, None))
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
    # Logos and CIs are inserted small, so the minimum is low. Bullets and background fragments are filtered by minimum side length and area
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
    for member, data, w, h, page in items:
        if not w or not h:
            w, h = size_of(data)
        if len(data) < min_kb * 1024 or min(w, h) < min_px or w * h < min_px * min_px * 2:
            continue  # Drops bullets and background fragments (images with a side under 64px or a very small area)
        k += 1
        suffix = ".png" if data[:2] == b"\x89P" else ".jpg" if data[:2] == b"\xff\xd8" else ".gif" if data[:3] == b"GIF" else ".bin"
        name = f"img_{k:04d}{suffix}"
        (out / name).write_bytes(data)
        manifest.append({"file": str(out / name), "source": src.name, "page": page, "member": member, "w": w, "h": h,
                         "bytes": len(data), "ratio": round(w / h, 2) if h else 0, "kind": kind_of(w, h, len(data))})
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out}/manifest.json images={len(manifest)} (out of {len(items)}, those under the minimum excluded)")
    for m in manifest[:20]:
        print(f"  {Path(m['file']).name} {m['w']}x{m['h']} {m['bytes'] // 1024}KB {m['kind']}" + (f" p{m['page']}" if m['page'] else ""))


if __name__ == "__main__":
    main()
