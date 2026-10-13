#!/usr/bin/env python3
"""deck_source.py: converts a proposal deck (pptx, pdf) into material for proposal manuscripts

Usage
  python3 deck_source.py parse  deck(pptx|pdf) output_folder [--dpi 110]
  python3 deck_source.py grid   output_folder page
  python3 deck_source.py figure output_folder page [--crop left,top,right,bottom] [--name name] [--no-trim]

Why a single path: in pptx, shapes, groups, SmartArt, charts, and tables are scattered across different XML, so per-format parsers multiply the paths.
  Converting pptx to PDF first reduces body text, tables, embedded images, and diagram capture to a single PDF process.
Output (output folder)
  발표자료.pdf          copy of the input pdf or the pptx conversion. The reference copy for all later processing
  pages/p001.png        per-page PNG for review (low resolution. For inserting figures, use the output of the figure command)
  sheets/sheet_01.png   page thumbnail sheets. When choosing diagram candidates, check this file first instead of opening every page PNG
  img/                  PDF embedded images and manifest.json (output of extract_images.py)
  pages/p001_grid.png   page PNG with a 10% grid drawn by the grid command. Used for reading --crop values
  figures/              diagram captures redrawn at high resolution from the PDF by the figure command
  pages.json            per-page title, estimated type, character count, counts of tables, images, and shapes, restored character count
  원문.md               per-page body text and tables (text in table areas is recorded only as tables)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from enum import Enum

# ── Settings ─────────────────────────────────────────────────────────────
REVIEW_DPI = 110            # page PNG for review. Kept at the minimum level where text is legible to cut viewing cost
FIGURE_DPI = 220            # diagram capture for insertion. A level without jagged edges when printed 140mm wide
SHEET_COLS, SHEET_ROWS = 4, 3
SHEET_THUMB_WIDTH = 480
SHEET_LABEL_HEIGHT = 22
PDF_CONVERT_TIMEOUT_SEC = 600
TITLE_ZONE_RATIO = 0.30     # slide titles usually sit in the top 30%
DIVIDER_MAX_CHARS = 60      # character cap for cover, divider, and thank-you pages
TABLE_AREA_RATIO = 0.35     # a table covering this share of the page area or more makes a table-centered page
DIAGRAM_MIN_DRAWINGS = 15   # absolute lower bound on the number of shapes (lines, boxes, arrows)
DIAGRAM_MEDIAN_FACTOR = 1.5  # template header bands and footers are shapes too, so a diagram candidate must exceed this multiple of the document median
IMAGE_AREA_RATIO = 0.12     # an embedded image area share at or above this value makes a diagram candidate
SHIFT_REPAIR_OFFSET = 0x100  # ToUnicode error of PowerPoint PDF export. Some syllables are recorded with codes 0x100 lower
GARBLE_WARN_RATIO = 0.02    # if uncommon syllables exceed this ratio, the text layer is not trusted
SHIFT_ACCEPT_RARE_RATIO = 0.005  # accept the 0x100 shift hypothesis only if the document-wide uncommon syllable ratio after restoration is at or below this value
BOILERPLATE_PAGE_RATIO = 0.4  # lines repeated on this share of all pages or more are treated as headers and footers and removed
BOILERPLATE_MIN_PAGES = 5     # lower bound so that body lines are not mistaken for headers in documents with few pages
BULLET_ONLY_RE = r"^[•·▪■□○●◦§üØ✓ü\-–]+$"   # a line with only bullet symbols. PDFs export bullets and body text as separate lines
PAGE_NUMBER_RE = r"^\d{1,3}$"
LONG_TOKEN_SYLLABLES = 8    # Korean words with intact spacing rarely reach 8 syllables
LONG_TOKEN_WARN_RATIO = 0.15  # if the share of long words exceeds this value, the text layer is missing spaces
FRAME_TABLE_AREA_RATIO = 0.85  # a table covering the whole page is the slide template frame mistaken for a table
TABLE_MIN_FILLED_RATIO = 0.40  # a table with mostly empty cells is a shape layout mistaken for a table
MAX_OBJECT_DEPTH = 15       # depth for finding objects inside shape groups (Form XObject)
POINTS_PER_INCH = 72        # PDF coordinate unit. Render scale = DPI ÷ 72
GRID_STEP_PERCENT = 10      # grid spacing. --crop values are percentages read from the grid
GRID_COLOR = (220, 0, 0)
TRIM_TOLERANCE = 12         # channel difference treated as the background color when trimming margins
RECOMPRESSOR_PRODUCERS = ("ghostscript", "ilovepdf", "smallpdf", "pdfcompressor", "sejda")  # producer markers of size compression and re-saving tools (for guidance text. The text check makes the stop verdict)
METRIC_COMPATIBLE_FONTS = ("arial", "calibri", "cambria", "times new roman", "courier new")  # LibreOffice substitutes fonts with the same character widths (Liberation, Carlito, Caladea), so layout is kept
EXIT_GARBLED = 2            # exit code so the caller can tell a stop due to an incomplete text layer
F_PDF, F_PAGES_JSON, F_TEXT = "발표자료.pdf", "pages.json", "원문.md"
D_PAGES, D_SHEETS, D_IMG, D_FIGURES = "pages", "sheets", "img", "figures"


def say(*parts) -> None:
    """Why: if a call that cuts stdout with head stops on BrokenPipe, the file outputs that follow (embedded images, state records) are lost"""
    try:
        print(*parts, flush=True)
    except BrokenPipeError:
        sys.stdout = open(os.devnull, "w")


class PageKind(str, Enum):
    DIVIDER = "간지"
    EMPTY = "빈 쪽"       # a page with only body template shapes and no content. An unfinished page of material still being written
    IMAGE = "이미지 쪽"   # a page with almost no text and a large image. May be a cover or divider with a background picture, or a content page with a table or financial statement pasted as an image
    TABLE = "표"
    DIAGRAM = "도식 후보"
    TEXT = "본문"


# ── Securing the PDF ─────────────────────────────────────────────────────────
def substituted_fonts(pptx: str) -> list[str]:
    """Fonts specified by the pptx that are missing in this environment. Why: substitute fonts have different character widths and cause line break changes in the conversion and text overflow inside diagrams"""
    if not shutil.which("fc-list") or not zipfile.is_zipfile(pptx):
        return []
    used = set()
    with zipfile.ZipFile(pptx) as zf:
        for name in zf.namelist():
            # theme files hold font tables per script that are not used (Thai, Khmer, and so on), so they are excluded. Only fonts specified by slide bodies are checked
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                used.update(re.findall(r'typeface="([^"+][^"]*)"', zf.read(name).decode("utf-8", "replace")))
    installed = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout.lower()
    return sorted(f for f in used if f.lower() not in installed and f.lower() not in METRIC_COMPATIBLE_FONTS)


def to_pdf(src: str, out_dir: str) -> str:
    """Normalize the input into a reference PDF. pdf is copied, pptx is converted with LibreOffice"""
    target = os.path.join(out_dir, F_PDF)
    if not os.path.isfile(src):
        sys.exit(f"ERROR: input file not found {src}")
    ext = os.path.splitext(src)[1].lower()
    if ext == ".pdf":
        shutil.copyfile(src, target)
        return target
    if ext not in (".pptx", ".ppt"):
        sys.exit(f"ERROR: unsupported input format {ext} (pptx, pdf)")
    missing = substituted_fonts(src)
    if missing:
        say(f"  WARN fonts missing in this environment: {len(missing)} {missing[:5]}. No effect on body extraction. Substitute fonts have different character widths, so text inside diagrams may overflow. "
            "Check the capture results of diagram capture pages. For pages with overflow, get the PDF saved from PowerPoint and capture with figure --pdf")
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("ERROR: could not convert pptx to PDF because LibreOffice is missing. "
                 "Install LibreOffice and rerun, or submit a PDF saved from PowerPoint as input")
    with tempfile.TemporaryDirectory() as tmp:
        # Why a separate profile: a conflict with an existing soffice process or a locked profile ends the conversion without response
        cmd = [soffice, f"-env:UserInstallation=file://{tmp}/profile", "--headless",
               "--convert-to", "pdf", "--outdir", tmp, os.path.abspath(src)]
        subprocess.run(cmd, check=False, capture_output=True, timeout=PDF_CONVERT_TIMEOUT_SEC)
        made = os.path.join(tmp, os.path.splitext(os.path.basename(src))[0] + ".pdf")
        if not os.path.exists(made):
            sys.exit("ERROR: pptx to PDF conversion failed. Submit a PDF saved from PowerPoint as input")
        shutil.move(made, target)
    return target


# ── Text ───────────────────────────────────────────────────────────
def _is_common_hangul(ch: str) -> bool:
    # Why a length test: Python's euc-kr codec encodes syllables outside KS X 1001 as 8-byte sequences without raising an exception
    return len(ch.encode("euc-kr", "ignore")) == 2


def repair_shifted_hangul(text: str) -> tuple[str, int, int, int]:
    """Restore uncommon Hangul syllables whose +0x100 is a common syllable. Returns (text, restored count, unrestorable uncommon count, Hangul count)"""
    out, fixed, hangul, rare = [], 0, 0, 0
    for ch in text:
        if "가" <= ch <= "힣":
            hangul += 1
            if not _is_common_hangul(ch):
                cand = chr(ord(ch) + SHIFT_REPAIR_OFFSET)
                if cand <= "힣" and _is_common_hangul(cand):
                    ch, fixed = cand, fixed + 1
                else:
                    rare += 1
        out.append(ch)
    return "".join(out), fixed, rare, hangul


def clean_lines(lines: list[str], boilerplate: set[str]) -> list[str]:
    """Remove headers, footers, and page numbers, and join lines holding only bullet symbols with the next line"""
    out, pending_bullet = [], False
    for ln in lines:
        if ln in boilerplate or re.match(PAGE_NUMBER_RE, ln):
            continue
        if re.match(BULLET_ONLY_RE, ln):
            pending_bullet = True
            continue
        if out and out[-1].removeprefix("- ") == ln:
            continue  # text with shadow and outline effects is recorded twice on the same line in the PDF
        out.append(("- " if pending_bullet else "") + ln)
        pending_bullet = False
    return out


def find_boilerplate(pages: list[dict]) -> set[str]:
    if len(pages) < BOILERPLATE_MIN_PAGES:
        return set()
    seen = Counter(ln for p in pages for ln in set(p["lines"]))
    return {ln for ln, n in seen.items() if n / len(pages) >= BOILERPLATE_PAGE_RATIO}


def finalize_text(pages: list[dict]) -> bool:
    """Document-level post-processing. Returns whether the 0x100 shift hypothesis is accepted
    Why document level: character code errors come from the export method, so they appear with the same pattern across the whole document.
      Applying restoration to errors of another pattern only turns one typo into another, so it is accepted only when uncommon syllables disappear after restoration"""
    boilerplate = find_boilerplate(pages)
    fixed_total = rare_total = hangul_total = 0
    for p in pages:
        p["lines"] = clean_lines(p["lines"], boilerplate)
        raw = "\n".join(p["lines"] + p["table_md"] + [p["title"]])
        _, fixed, rare, hangul = repair_shifted_hangul(raw)
        p["_fixed"], p["_rare"], p["_hangul"] = fixed, rare, hangul
        fixed_total, rare_total, hangul_total = fixed_total + fixed, rare_total + rare, hangul_total + hangul
    accept = fixed_total > 0 and rare_total / max(1, hangul_total) <= SHIFT_ACCEPT_RARE_RATIO
    for p in pages:
        fixed, rare, hangul = p.pop("_fixed"), p.pop("_rare"), p.pop("_hangul")
        if accept:
            p["lines"] = [repair_shifted_hangul(ln)[0] for ln in p["lines"]]
            p["table_md"] = [repair_shifted_hangul(md)[0] for md in p["table_md"]]
            p["title"] = repair_shifted_hangul(p["title"])[0]
        p["repaired"] = fixed if accept else 0
        p["body"] = "\n".join(p["lines"])
        p["garbled"] = (rare if accept else rare + fixed) / max(1, hangul) > GARBLE_WARN_RATIO or p["repaired"] > 0
        p["unspaced"] = spaces_missing(p["body"])
        p["chars"] = len(p["body"].replace("\n", "")) + sum(len(t) for t in p["table_md"])
        del p["lines"]
    return accept


def spaces_missing(text: str) -> bool:
    tokens = re.findall(r"[가-힣]+", text)
    long_tokens = sum(1 for t in tokens if len(t) >= LONG_TOKEN_SYLLABLES)
    return bool(tokens) and long_tokens / len(tokens) > LONG_TOKEN_WARN_RATIO


def _inside(inner, outer) -> bool:
    cx, cy = (inner[0] + inner[2]) / 2, (inner[1] + inner[3]) / 2
    return outer[0] <= cx <= outer[2] and outer[1] <= cy <= outer[3]


def page_tables(page) -> list[tuple[tuple, str]]:
    """List of (area, markdown table). Area is (left, top, right, bottom). Table recognition failure is treated as an empty list so body extraction is not blocked"""
    found = []
    try:
        tables = page.find_tables()
    except Exception:
        return found
    page_area = _area(page_box(page)) or 1.0
    for tb in tables:
        if _area(tb.bbox) / page_area >= FRAME_TABLE_AREA_RATIO:
            continue
        rows = [[(c or "").replace("\n", "<br>").replace("|", "/").strip() for c in r] for r in tb.extract()]
        rows = [r for r in rows if any(r)]
        cells = [c for r in rows for c in r]
        if len(rows) < 2 or len(rows[0]) < 2 or sum(1 for c in cells if c) / len(cells) < TABLE_MIN_FILLED_RATIO:
            continue
        md = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
        md += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        found.append((tuple(tb.bbox), "\n".join(md)))
    return found


def page_title(boxes: list[dict], page_height: float, body_lines: list[str]) -> str:
    """Estimate the title as the line with the largest text in the top zone. Otherwise the first body line
    Pieces at the same height and size (a number and a title, and so on) are joined from the left into one line. If several lines share the size, the top line is chosen"""
    limit = page_height * TITLE_ZONE_RATIO
    rows: dict[tuple, list] = {}
    for box in boxes:
        for top, x0, text, size in box["lines"]:
            if top <= limit and text:
                rows.setdefault((round(top), round(size, 1)), []).append((x0, text))
    best = None
    for (top, size), parts in rows.items():
        text = squeeze(" ".join(t for _, t in sorted(parts)))
        if len(text) >= 2 and (best is None or size > best[0] or (size == best[0] and top < best[1])):
            best = (size, top, text)
    return best[2] if best else (body_lines[0] if body_lines else "")


def classify(page: dict, diagram_threshold: float) -> PageKind:
    # Why the shape count condition: in PDFs where text is saved as outlines, body pages also register few characters
    if page["chars"] < DIVIDER_MAX_CHARS and page["table_area"] == 0 and page["drawings"] < diagram_threshold:
        if page["image_area"] >= IMAGE_AREA_RATIO:
            return PageKind.IMAGE
        # divider pages do not use the body template, so they have few shapes. A page with shapes at template level but no text is a page whose content was not filled
        return PageKind.EMPTY if page["drawings"] >= DIAGRAM_MIN_DRAWINGS and not page["garbled"] else PageKind.DIVIDER
    if page["table_area"] >= TABLE_AREA_RATIO:
        return PageKind.TABLE
    if page["drawings"] >= diagram_threshold or page["image_area"] >= IMAGE_AREA_RATIO:
        return PageKind.DIAGRAM
    return PageKind.TEXT


def _area(box) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def squeeze(line: str) -> str:
    """Reduce consecutive spaces to one. Why: pdfminer turns both space characters and character gaps into spaces, creating double spaces"""
    return re.sub(r"[ \t]{2,}", " ", line).strip()


def page_box(page) -> tuple:
    return (0.0, 0.0, float(page.width), float(page.height))


def text_boxes(page) -> list[dict]:
    """List of text boxes. Items are box (left, top, right, bottom from the page top), text (body), lines (per line: top position, left position, text, max font size)
    Order is top to bottom, left to right
    Why text box units: uses pdfminer's layout analysis so side-by-side slide text boxes are not merged into one line"""
    from pdfminer.layout import LTChar, LTFigure, LTTextBox, LTTextLine
    height = float(page.height)
    boxes = []

    def walk(objs):
        for obj in objs:
            if isinstance(obj, LTTextBox):
                lines = [(height - ln.y1, ln.x0, squeeze(ln.get_text()),
                          max((c.size for c in ln if isinstance(c, LTChar)), default=0))
                         for ln in obj if isinstance(ln, LTTextLine)]
                boxes.append({"box": (obj.x0, height - obj.y1, obj.x1, height - obj.y0),
                              "text": obj.get_text(), "lines": lines})
            elif isinstance(obj, LTFigure):
                walk(obj)
    walk(page.layout)
    return sorted(boxes, key=lambda b: (round(b["box"][1], 1), b["box"][0]))


def count_paths(pdfium_page) -> int:
    """Number of vector path (line, box, arrow) objects. Also counts paths inside shape groups (Form XObject)"""
    import pypdfium2.raw as pdfium_c
    return len(list(pdfium_page.get_objects(filter=(pdfium_c.FPDF_PAGEOBJ_PATH,), max_depth=MAX_OBJECT_DEPTH)))


def parse_page(page, pdfium_page) -> dict:
    """page is the pdfplumber page (body, tables, image positions), pdfium_page is the pypdfium2 page (vector path count)"""
    tables = page_tables(page)
    boxes = [b for b, _ in tables]
    text_items = text_boxes(page)
    lines = []
    for item in text_items:
        if any(_inside(item["box"], b) for b in boxes):
            continue  # text inside tables is excluded (tables are recorded as tables below)
        lines += [squeeze(ln) for ln in item["text"].splitlines() if ln.strip()]
    table_mds = [md for _, md in tables]
    title = page_title(text_items, float(page.height), lines)
    page_area = _area(page_box(page)) or 1.0
    image_boxes = [(i["x0"], i["top"], i["x1"], i["bottom"]) for i in page.images]
    image_area = sum(_area(b) for b in image_boxes) / page_area
    drawings = count_paths(pdfium_page)
    return {"title": title, "kind": "", "chars": 0, "table_area": round(sum(_area(b) for b in boxes) / page_area, 2),
            "image_area": round(image_area, 2), "tables": len(table_mds),
            "images": len(image_boxes), "drawings": drawings,
            "repaired": 0, "garbled": False, "unspaced": False, "lines": lines, "body": "", "table_md": table_mds}


# ── Page PNGs and thumbnail sheets ─────────────────────────────────────────────
def render_pages(pdf: str, out_dir: str, dpi: int) -> list[str]:
    import pypdfium2 as pdfium
    os.makedirs(os.path.join(out_dir, D_PAGES), exist_ok=True)
    paths = []
    doc = pdfium.PdfDocument(pdf)
    try:
        for i in range(len(doc)):
            path = os.path.join(out_dir, D_PAGES, f"p{i + 1:03d}.png")
            doc[i].render(scale=dpi / POINTS_PER_INCH).to_pil().save(path)
            paths.append(path)
    finally:
        doc.close()
    return paths


def contact_sheets(page_pngs: list[str], out_dir: str) -> int:
    from PIL import Image, ImageDraw
    os.makedirs(os.path.join(out_dir, D_SHEETS), exist_ok=True)
    per_sheet = SHEET_COLS * SHEET_ROWS
    count = 0
    for start in range(0, len(page_pngs), per_sheet):
        chunk = page_pngs[start:start + per_sheet]
        thumbs = []
        for p in chunk:
            im = Image.open(p).convert("RGB")
            thumbs.append(im.resize((SHEET_THUMB_WIDTH, round(im.height * SHEET_THUMB_WIDTH / im.width))))
        cell_h = max(t.height for t in thumbs) + SHEET_LABEL_HEIGHT
        rows = -(-len(chunk) // SHEET_COLS)
        sheet = Image.new("RGB", (SHEET_COLS * SHEET_THUMB_WIDTH, rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for k, t in enumerate(thumbs):
            x, y = (k % SHEET_COLS) * SHEET_THUMB_WIDTH, (k // SHEET_COLS) * cell_h
            draw.text((x + 6, y + 4), f"p{start + k + 1}", fill="black")
            sheet.paste(t, (x, y + SHEET_LABEL_HEIGHT))
        count += 1
        sheet.save(os.path.join(out_dir, D_SHEETS, f"sheet_{count:02d}.png"))
    return count


# ── Output records ────────────────────────────────────────────────────────
def write_text(out_dir: str, src: str, pages: list[dict]) -> None:
    repaired = sum(p["repaired"] for p in pages)
    layer = "불완전 (글자 누락과 오자 가능. 쪽 PNG가 기준이고 이 파일은 보조 자료)" if text_layer_unreliable(pages) else "정상"
    out = ["# 발표자료 원문", f"- 입력 파일 {os.path.basename(src)}", f"- 쪽수 {len(pages)}",
           f"- 텍스트 레이어 {layer}", f"- 글자 코드 자동 복원 {repaired}자", ""]
    for n, p in enumerate(pages, 1):
        out.append(f"## p{n} {p['title']}")
        note = (", 텍스트 불완전" if p["garbled"] else "") + (", 공백 누락(띄어쓰기를 복원하여 이관)" if p["unspaced"] else "")
        out.append(f"- (추정 유형) {p['kind']}, 글자 {p['chars']}, 표 {p['tables']}, 이미지 {p['images']}, 도형 {p['drawings']}{note}")
        out += ["", p["body"], ""]
        for md in p["table_md"]:
            out += [md, ""]
    open(os.path.join(out_dir, F_TEXT), "w", encoding="utf-8").write("\n".join(out))


def text_layer_unreliable(pages: list[dict]) -> bool:
    """The export method is the same across the document, so if even one page is incomplete the whole document is treated as incomplete"""
    return any(p["garbled"] for p in pages)


def write_manifest(out_dir: str, pages: list[dict]) -> None:
    slim = [{"page": n, **{k: v for k, v in p.items() if k not in ("body", "table_md")}} for n, p in enumerate(pages, 1)]
    json.dump(slim, open(os.path.join(out_dir, F_PAGES_JSON), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def extract_embedded_images(pdf: str, out_dir: str) -> None:
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extract_images.py")
    done = subprocess.run([sys.executable, script, pdf, os.path.join(out_dir, D_IMG)], capture_output=True, text=True)
    first = (done.stdout or done.stderr).strip().splitlines()
    say("  Embedded images:", first[0] if first else "no extraction results")


def probe_text_layer(doc) -> tuple[bool, str]:
    """Check the text layer before rendering pages. Returns (incomplete or not, guidance text)
    Why a prior check: in PDFs re-saved with size compression tools, characters change into arbitrary codes or outlines, making body extraction meaningless.
      Reporting after rendering dozens of pages has already spent time and viewing cost, so it is judged first"""
    text = "\n".join((page.extract_text() or "") for page in doc.pages)
    _, fixed, rare, hangul = repair_shifted_hangul(text)
    # Why only typos stop: body text missing only spaces has intact characters and can be transferred with spacing restored. Body text changed into other syllables cannot be restored
    if (fixed + rare) / max(1, hangul) <= GARBLE_WARN_RATIO:
        return False, ""
    producer = (doc.metadata.get("Producer") or "").strip()
    cause = f"producer is '{producer}', presumed a file that went through size compression or re-saving" if any(
        k in producer.lower().replace(" ", "") for k in RECOMPRESSOR_PRODUCERS) else f"producer '{producer or 'unknown'}'"
    detail = f"of {hangul} Hangul characters, {fixed + rare} uncommon syllables, missing spaces {'yes' if spaces_missing(text) else 'no'}"
    return True, f"{cause} (modified {doc.metadata.get('ModDate') or 'unknown'}). {detail}"


def parse(src: str, out_dir: str, dpi: int = REVIEW_DPI, allow_garbled: bool = False) -> list[dict]:
    import pdfplumber
    os.makedirs(out_dir, exist_ok=True)
    pdf = to_pdf(src, out_dir)
    import pypdfium2 as pdfium
    doc = pdfplumber.open(pdf, laparams={"all_texts": True})  # all_texts: text inside shape groups is also analyzed as text boxes
    broken, reason = probe_text_layer(doc)
    if broken:
        say(f"Warning: incomplete text layer. {reason}")
        if not allow_garbled:
            say("Stop: a PDF whose body text cannot be extracted. Ask the user for the pptx original or the PDF before compression (a file saved directly from PowerPoint). "
                  "Rerun with --allow-garbled only if the user decided to proceed by reading page PNGs because there is no original")
            doc.close()
            sys.exit(EXIT_GARBLED)
    vector_doc = pdfium.PdfDocument(pdf)
    try:
        pages = [parse_page(page, vector_doc[i]) for i, page in enumerate(doc.pages)]
    finally:
        vector_doc.close()
        doc.close()
    finalize_text(pages)
    threshold = max(DIAGRAM_MIN_DRAWINGS, DIAGRAM_MEDIAN_FACTOR * statistics.median(p["drawings"] for p in pages))
    for p in pages:
        p["kind"] = classify(p, threshold).value
    sheets = contact_sheets(render_pages(pdf, out_dir, dpi), out_dir)
    write_text(out_dir, src, pages)
    write_manifest(out_dir, pages)
    kinds = {k.value: sum(1 for p in pages if p["kind"] == k.value) for k in PageKind}
    say(f"OK: {pdf} pages {len(pages)}, types {kinds}, thumbnail sheets {sheets}, restored {sum(p['repaired'] for p in pages)} characters")
    unspaced = [n for n, p in enumerate(pages, 1) if p["unspaced"]]
    if unspaced:
        say(f"  WARN pages missing spaces: {len(unspaced)} {unspaced[:12]}{' and more' if len(unspaced) > 12 else ''}. Characters are intact, so transfer with spacing restored")
    empty = [n for n, p in enumerate(pages, 1) if p["kind"] == PageKind.EMPTY.value]
    if empty:
        say(f"  WARN empty pages {empty}. Presumed material still being written. Tell the user the page numbers and confirm what to fill")
    if text_layer_unreliable(pages):
        say("  WARN incomplete text layer (missing characters, typos, missing spaces). Read by the page PNGs and use 원문.md as auxiliary material")
    extract_embedded_images(pdf, out_dir)
    return pages


# ── Diagram capture ────────────────────────────────────────────────────────
def trim_margin(image):
    """Treat the color of the four corners as background and remove outer margins of the same color"""
    from PIL import Image, ImageChops
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
    diff = ImageChops.difference(rgb, background).point(lambda v: 255 if v > TRIM_TOLERANCE else 0)
    box = diff.getbbox()
    return rgb.crop(box) if box else rgb


def grid(out_dir: str, page_no: int) -> str:
    """Draw a percentage grid over a page PNG. Why: crop values guessed from thumbnails easily miss, causing repeated retries"""
    from PIL import Image, ImageDraw
    src = os.path.join(out_dir, D_PAGES, f"p{page_no:03d}.png")
    if not os.path.exists(src):
        sys.exit(f"ERROR: {src} not found. Run parse first")
    image = Image.open(src).convert("RGB")
    draw = ImageDraw.Draw(image)
    for percent in range(GRID_STEP_PERCENT, 100, GRID_STEP_PERCENT):
        x, y = image.width * percent // 100, image.height * percent // 100
        draw.line([(x, 0), (x, image.height)], fill=GRID_COLOR, width=1)
        draw.line([(0, y), (image.width, y)], fill=GRID_COLOR, width=1)
        draw.text((x + 3, 2), str(percent), fill=GRID_COLOR)
        draw.text((2, y + 2), str(percent), fill=GRID_COLOR)
    path = os.path.join(out_dir, D_PAGES, f"p{page_no:03d}_grid.png")
    image.save(path)
    say(f"OK: {path}")
    return path


def figure(out_dir: str, page_no: int, crop: str | None, name: str | None, trim: bool = True, pdf: str | None = None) -> str:
    """Redraw the whole page or part of it from the PDF at high resolution and save. crop is left,top,right,bottom as percentages of the page size
    pdf replaces the capture source. Used to capture from the PDF saved by PowerPoint a diagram whose text overflowed in the pptx conversion (assumes the same page numbers)"""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf or os.path.join(out_dir, F_PDF))
    if not 1 <= page_no <= len(doc):
        sys.exit(f"ERROR: page number {page_no} is out of range (1-{len(doc)})")
    page = doc[page_no - 1]
    width, height = page.get_size()
    margins = (0, 0, 0, 0)  # widths to cut from left, bottom, right, top (points)
    if crop:
        try:
            left, top, right, bottom = (float(v) / 100 for v in crop.split(","))
        except ValueError:
            sys.exit("ERROR: --crop format is left,top,right,bottom percentages (e.g. 5,20,95,88)")
        if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
            sys.exit("ERROR: --crop values must be in 0-100 with left<right and top<bottom")
        margins = (width * left, height * (1 - bottom), width * (1 - right), height * top)
    image = page.render(scale=FIGURE_DPI / POINTS_PER_INCH, crop=margins).to_pil().convert("RGB")
    doc.close()
    if trim:
        image = trim_margin(image)
    os.makedirs(os.path.join(out_dir, D_FIGURES), exist_ok=True)
    safe = "".join(c for c in (name or "") if c.isalnum() or c in "-_")
    path = os.path.join(out_dir, D_FIGURES, f"p{page_no:03d}" + (f"_{safe}" if safe else "") + ".png")
    image.save(path)
    say(f"OK: {path} {image.width}x{image.height}")
    return path


def main():
    ap = argparse.ArgumentParser(description="proposal deck (pptx, pdf) → manuscript material")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse")
    p.add_argument("input")
    p.add_argument("out")
    p.add_argument("--dpi", type=int, default=REVIEW_DPI)
    p.add_argument("--allow-garbled", action="store_true", help="proceed on the premise of reading page PNGs even if the text layer is incomplete (only on the user's decision)")
    p = sub.add_parser("grid")
    p.add_argument("out")
    p.add_argument("page", type=int)
    p = sub.add_parser("figure")
    p.add_argument("out")
    p.add_argument("page", type=int)
    p.add_argument("--crop")
    p.add_argument("--name")
    p.add_argument("--no-trim", action="store_true")
    p.add_argument("--pdf", help="replacement capture source PDF (saved from PowerPoint)")
    a = ap.parse_args()
    if a.cmd == "parse":
        parse(a.input, a.out, a.dpi, a.allow_garbled)
    elif a.cmd == "grid":
        grid(a.out, a.page)
    else:
        figure(a.out, a.page, a.crop, a.name, not a.no_trim, a.pdf)


if __name__ == "__main__":
    main()
