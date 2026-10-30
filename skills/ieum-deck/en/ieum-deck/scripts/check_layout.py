#!/usr/bin/env python3
"""check_layout.py: structural review of a built pptx (python-pptx is used for review only).
Usage: python3 check_layout.py <deck.pptx> [--layout 16:9|A4|10.83|4:3]
Checks: estimated text overflow (needed height from the build's measured NanumGothic widths and word wrapping, FAIL), icon and text overlap (FAIL), headline font consistency (WARN), mixed alignment in table columns and side-by-side boxes (WARN), edge margin (0.42 inch), band intrusion (body shapes entering the headline band), body text under 11pt (footnotes, sources and page numbers excluded. Custom slide playback slides are excluded through ownSlides in build.json, and uppercase English structure labels such as VISION and SCOPE by their original size),
        text boxes overlapping each other (WARN over 20%, FAIL over 30% or when a picture is involved), line-level glyph overlap between a label and body text inside a content box (WARN over 30%), tables, charts, pictures and filled boxes overlapping each other (FAIL over 15%), estimated mid-word line breaks (a word wider than the inner width of a text box or table cell, WARN. Skipped when lineBreak in the build record is char), estimated line breaks inside a word (where LibreOffice splits a word caught at the line end, for example between a number and its unit or before a closing bracket or comma. Text boxes and table cells, WARN. Skipped when lineBreak in the build record is char), excessive body margin on one side (content crowded to one side), thin box content (fill ratio under 45% for bordered boxes and text boxes inside bordered panels), low body vertical fill (content group under 70% of the body height), empty panels (no text inside a bordered box), accent color in 2 or more places, missing bullets on multi-line text
Result: FAIL and WARN lists. Exit code 1 means a FAIL exists
"""
import json
import re
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Emu
from text_metrics import FM, para_width_in, text_width_in, wrap_lines, wrap_paragraph  # Same text width model as the build (shared module in this folder)

HERE = Path(__file__).resolve().parent
LIM = json.load(open(HERE / "limits.json", encoding="utf-8")) if (HERE / "limits.json").exists() else {}
EDGE = LIM.get("BAND", {}).get("EDGE_MIN", 0.42)
BODY_MIN = LIM.get("SIZE", {}).get("BODY_MIN", 11)
ACCENT = "C0392B"
LABEL_INK_RATIO = 0.3  # Overlap threshold between a label and body glyphs inside a box (relative to the smaller glyph area)
# Text at or above this size is a title and is excluded from the multi-line no-bullet check (the 40pt cover title shrunk to the 0.6 floor is 24pt; the largest body-family size is the 20pt contents item)
TITLE_PT = 24
# Base fill colors allowed in table cells (navy and mono theme colors, tints, grays, white). At run time the palette in the build record (applied theme colors) is added. Other colors go to visual review
PALETTE = {"1F3864", "17294A", "6B8EC2", "A9B9D9", "D5DDEC", "E9EBF0", "F7F8FA", "F2F2F2", "C9CDD8",
           "FFFFFF", "BFBFBF", "A6A6A6", "595959", "333333", "2B2B2B", "4D4D4D", "808080", "D9D9D9", "C0392B", "8B93A7",
           "EBEBEB", "F8F8F8", "939393"}

def _build_record(pptx_path):
    """Build record (<file name>.build.json). Must be in the same folder as the pptx. Empty record if absent"""
    f = Path(str(pptx_path)[:-5] + ".build.json") if str(pptx_path).endswith(".pptx") else None
    if not f or not f.exists(): return {}
    try:
        return json.load(open(f, encoding="utf-8"))
    except Exception:
        return {}


def _own_small_boxes(record):
    """Coordinate set of shapes typeset below the body minimum font size in the custom slide source.

    Custom slide playback keeps the source font sizes, so these shapes are excluded from the body minimum check.
    Slot substitution keeps the source coordinates, so shapes are identified by coordinates. Empty set without registered custom slides.
    """
    f = record.get("ownDeck")
    if not f or not Path(f).exists(): return set()
    out = set()
    for sl in json.load(open(f, encoding="utf-8")).get("slides", []):
        for a in sl.get("atoms", []):
            for para in a.get("paras", []) or []:
                if any((r.get("sz") or 18) < BODY_MIN for r in para.get("runs", []) or []):
                    out.add((round(a.get("x", 0), 2), round(a.get("y", 0), 2), round(a.get("w", 0), 2), round(a.get("h", 0), 2)))
                    break
    return out


NSA = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

def para_runs(p):
    """Runs of a paragraph (text, size pt, bold). 18pt when the size is unset"""
    return [(r.text, r.font.size.pt if r.font.size else 18, bool(r.font.bold)) for r in p.runs]


WORD_FIT_TOL = 0.02  # Tolerance for word width comparison (inches)


def too_wide_word(paras, inner):
    """First word wider than the inner width (minus the indent for bulleted paragraphs). (word, word width, inner width) or None"""
    for p in paras:
        runs = [r for r in p.runs if r.text]
        if not runs: continue
        # A line break run is a word boundary, so put spaces between runs
        txt = " ".join(r.text for r in runs).replace("\n", " ").replace("\x0b", " ")
        pt = max((r.font.size.pt for r in runs if r.font.size), default=12)
        bold = any(r.font.bold for r in runs)
        pxml = p._p.xml
        indent = 0.0
        if "buChar" in pxml or "buAutoNum" in pxml:
            pr = p._p.find(NSA + "pPr")
            indent = int(pr.get("marL")) / 914400 if pr is not None and pr.get("marL") else 0.28
        eff = inner - indent
        for tok in txt.split():
            tw = text_width_in(tok, pt, bold)
            if tw > eff + WORD_FIT_TOL: return tok, tw, eff
    return None


def bullet_indent(p):
    """Indent (inches) of a bulleted paragraph. 0 without a bullet"""
    pxml = p._p.xml
    if "buChar" not in pxml and "buAutoNum" not in pxml: return 0.0
    pr = p._p.find(NSA + "pPr")
    return int(pr.get("marL")) / 914400 if pr is not None and pr.get("marL") else 0.28


def token_splits(paras, inner):
    """Places where LibreOffice is estimated to break inside a word at the inner width ['60|분', ...]. Same line breaking as the build (wrap_paragraph)
    Words wider than the line are left out (too_wide_word reports them)"""
    out = []
    for p in paras:
        runs = [r for r in para_runs(p) if r[0]]
        if not runs: continue
        out += [f"{w[:cut]}|{w[cut:]}" for w, cut in wrap_paragraph(runs, max(0.1, inner - bullet_indent(p)))[2]]
    return out


def overflow_estimate(sh):
    """Compares the estimated needed height of a text box with the box height. Returns (need_in, avail_in, wrap)"""
    tf = sh.text_frame
    bp = tf._txBody.find(NSA + "bodyPr")
    ins = lambda k, d: int(bp.get(k)) / 914400 if bp is not None and bp.get(k) else d
    l, r, t, b = ins("lIns", 0.1), ins("rIns", 0.1), ins("tIns", 0.05), ins("bIns", 0.05)
    wrap = bp is None or bp.get("wrap") != "none"
    w, h = sh.width / 914400, sh.height / 914400
    inner_w = max(0.1, w - l - r)
    need = 0.0
    for p in tf.paragraphs:
        runs = para_runs(p)
        if not runs:
            continue
        pt = max(x[1] for x in runs)
        # Bulleted paragraphs lose width by their indent
        pxml = p._p.xml
        indent = 0.0
        if "buChar" in pxml or "buAutoNum" in pxml:
            pr = p._p.find(NSA + "pPr")
            indent = int(pr.get("marL")) / 914400 if pr is not None and pr.get("marL") else 0.28
        eff_w = max(0.1, inner_w - indent)
        lines = wrap_lines(runs, eff_w)[0] if wrap else 1
        spc = p._p.find(NSA + "pPr/" + NSA + "spcBef/" + NSA + "spcPts")
        need += lines * pt * 1.2 / 72 + (int(spc.get("val")) / 100 / 72 if spc is not None else 0)
    # PowerPoint shows short labels without line breaks centered and ignores box insets, so compare against the height with insets included
    lines_total = 0
    for p in tf.paragraphs:
        runs = para_runs(p)
        if not runs:
            continue
        lines_total += wrap_lines(runs, inner_w)[0] if wrap else 1
    paras_n = sum(1 for p in tf.paragraphs if p.runs)
    if lines_total <= paras_n:
        return need, h, wrap
    return need, h - t - b, wrap
RULE_TOP_Y = 1.05  # Top rule of the headline band (16:9 base, scaled by page height ratio)
RULE_Y = 1.8  # Bottom rule of the headline band
NOTE_Y = 6.78
CONTENT_Y = LIM.get("BAND", {}).get("CONTENT_Y", 2.32)  # Body baseline for layouts with a marker band
CONTENT_Y_NO_MARKER = 2.07  # Body baseline for layouts without a marker band
BODY_PAD = LIM.get("BAND", {}).get("BODY_PAD", 0.1)  # Gap from the baseline to the top of the body group
CONTENT_BOTTOM = LIM.get("BAND", {}).get("CONTENT_BOTTOM", 6.92)  # Lowest point the body can reach without a source line


def inch(v):
    return v / 914400


def main():
    args = sys.argv[1:]
    if not args: raise SystemExit(__doc__)
    prs = Presentation(args[0])
    record = _build_record(args[0])
    own_slides = set(record.get("ownSlides") or [])
    OWN_SMALL = _own_small_boxes(record)
    # Add the theme colors in the build record (custom themes included) to the allowed table cell colors
    palette = PALETTE | {str(c).upper() for c in record.get("palette") or []}
    # A character-level deck (meta.lineBreak=char) is one where the user allowed mid-word breaks, so the mid-word line break estimate is skipped
    word_break = record.get("lineBreak", "word") != "char"
    W, H = inch(prs.slide_width), inch(prs.slide_height)
    sy = H / 7.5
    sx = W / 13.333  # Horizontal scale against the 16:9 base
    fails, warns, headline_pts = [], [], []
    for n, slide in enumerate(prs.slides, start=1):
        rects, texts, icons, ink, ink_lines = [], [], [], [], []
        accent = 0
        for sh in slide.shapes:
            if sh.left is None: continue
            x, y, w, h = inch(sh.left), inch(sh.top), inch(sh.width), inch(sh.height)
            r = (x, y, x + w, y + h)
            is_band = y < RULE_Y * sy + 0.35 or y > NOTE_Y * sy - 0.05
            if x < EDGE - 0.02 or r[2] > W - EDGE + 0.02 or y < 0.2 or r[3] > H - 0.2:
                if not is_band: fails.append(f"[{n}] Edge margin intrusion {sh.name} ({x:.2f},{y:.2f},{w:.2f},{h:.2f})")
            if sh.has_text_frame and sh.text_frame.text.strip():
                tf = sh.text_frame
                over = 0.0
                if FM and not is_band:
                    need, avail, wrap = overflow_estimate(sh)
                    if need > avail + max(0.15, avail * 0.12):  # 12% of the box height allows for renderer line spacing differences
                        fails.append(f"[{n}] Estimated text overflow {need:.2f}in > box {avail:.2f}in '{tf.text[:15]}'")
                    over = max(0.0, need - avail)
                paras = [p for p in tf.paragraphs if p.text.strip()]
                small_done = False
                for p in tf.paragraphs:
                    prev_accent = False  # Consecutive accent-colored pieces in one paragraph count as 1 place (finalize resave splits "36억원" into "36" and "억원")
                    for run in p.runs:
                        sz = run.font.size.pt if run.font.size else None
                        # Structure labels (standalone uppercase English such as VISION, SCOPE) keep the custom slide source size, so they are excluded
                        txt_all = tf.text.strip()
                        struct_label = bool(re.fullmatch(r"[A-Z][A-Z0-9&/. -]{1,13}", txt_all))
                        # Text starting with ※ already carries the note mark, so its use needs no check
                        note_marked = txt_all.startswith("※") or bool(re.match(r"^\d+\)\s", txt_all))  # includes footnote numbers 1) 2)
                        own_origin = n in own_slides or struct_label or note_marked or (round(x / sx, 2), round(y / sy, 2), round(w / sx, 2), round(h / sy, 2)) in OWN_SMALL
                        if sz and sz < BODY_MIN and not is_band and y < NOTE_Y * sy - 0.05 and not small_done and not own_origin:
                            small_done = True
                            # Text smaller than body text reads as a note, so check the ※ mark
                            warns.append(f"[{n}] {sz}pt text (body minimum {BODY_MIN}) '{run.text[:15]}' → check its use in visual review")
                        col = run.font.color
                        try:
                            is_accent = bool(col and col.type is not None and str(col.rgb) == ACCENT)
                        except Exception:
                            is_accent = False
                        if is_accent and not prev_accent: accent += 1
                        if is_accent or run.text.strip(): prev_accent = is_accent  # Whitespace-only pieces do not break the run
                if len(paras) > 1 and not is_band:
                    bulleted = any(p._p.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}buChar") is not None or p._p.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}buAutoNum") is not None for p in paras)
                    # If every line is centered, treat it as a label (role and name, title and subtitle) and skip it
                    label_like = len(paras) <= 3 and all(p.alignment is not None and int(p.alignment) == 2 for p in paras)
                    # Footnotes (1), 2)) and ※ notes are skipped because the number or symbol acts as the bullet
                    note_like = all(re.match(r"^\s*(\d+\)|※)", p.text or "") for p in paras if (p.text or "").strip())
                    # Title-size text such as a two-line cover title is not a list
                    title_like = all(r.font.size is not None and r.font.size.pt >= TITLE_PT for p in paras for r in p.runs if r.text.strip())
                    # When every line starts with a number (1., 1-1.), the number replaces the bullet (grid cell numbered)
                    enum_like = all(re.match(r"^\s*\d{1,2}(-\d{1,2})*[.)]\s", p.text or "") for p in paras)
                    if not bulleted and w > 2.5 and not label_like and not note_like and not title_like and not enum_like: warns.append(f"[{n}] Multi-line text without bullets '{paras[0].text[:15]}'")
                # Extend the box by the overflow height to check overlap with neighboring elements
                if not is_band:
                    texts.append(((r[0], r[1], r[2], r[3] + over), sh.name, tf.text[:15]))
                    # Area actually covered by glyphs (for icon overlap)
                    ink_w = 0.0
                    for p in tf.paragraphs:
                        runs = para_runs(p)
                        if runs: ink_w = max(ink_w, para_width_in(runs))
                    # Reflect the horizontal position of glyphs by alignment
                    # Left and right box insets hold no glyphs, so exclude them (covers slides that reserve number badge space as insets)
                    bp = tf._txBody.find(NSA + "bodyPr")
                    ins = lambda k, d: int(bp.get(k)) / 914400 if bp is not None and bp.get(k) else d
                    lIns, rIns = ins("lIns", 0.1), ins("rIns", 0.1)
                    inner_x, inner_w = x + lIns, max(0.05, w - lIns - rIns)
                    iw = min(inner_w, ink_w + 0.1)
                    al = {str(p.alignment) for p in tf.paragraphs if p.runs and p.alignment is not None}
                    if al == {"RIGHT (3)"}: ix0 = inner_x + inner_w - iw
                    elif al == {"CENTER (2)"}: ix0 = inner_x + (inner_w - iw) / 2
                    else: ix0 = inner_x
                    # Limit the vertical glyph range by the needed height and vertical alignment too (excludes empty space above and below)
                    anchor = bp.get("anchor") if bp is not None else None
                    ih = min(h + over, (need if FM and not is_band else h) + 0.08)
                    if anchor == "b": iy0 = y + h + over - ih
                    elif anchor == "t": iy0 = y
                    else: iy0 = y + (h + over - ih) / 2
                    ink.append(((ix0, iy0, ix0 + iw, iy0 + ih), sh.name, tf.text[:15]))
                    # Glyph area per line (one rectangle per line avoids misjudgments caused by one long line in multi-line boxes)
                    lines_box, cur = [], iy0
                    for p in tf.paragraphs:
                        runs = para_runs(p)
                        if not runs: continue
                        pt = max(v[1] for v in runs)
                        lh = pt * 1.2 / 72
                        spc = p._p.find(NSA + "pPr/" + NSA + "spcBef/" + NSA + "spcPts")
                        cur += int(spc.get("val")) / 100 / 72 if spc is not None else 0
                        nline, last_w = wrap_lines(runs, inner_w)
                        pal = str(p.alignment) if p.alignment is not None else None
                        for k in range(nline):
                            # Lines before the last line fill the line width
                            lw = max(0.05, min(inner_w, (inner_w if k < nline - 1 else last_w) + 0.1))
                            if pal == "RIGHT (3)": lx = inner_x + inner_w - lw
                            elif pal == "CENTER (2)": lx = inner_x + (inner_w - lw) / 2
                            else: lx = inner_x
                            lines_box.append((lx, cur, lx + lw, cur + lh))
                            cur += lh
                    ink_lines.append((lines_box or [(ix0, iy0, ix0 + iw, iy0 + ih)], sh.name, tf.text[:15]))
            elif sh.shape_type is not None and str(sh.shape_type).startswith("PICTURE") and not is_band:
                texts.append((r, sh.name, "[picture]"))
            elif sh.shape_type is not None and not is_band and 0.25 <= w <= 1.3 and 0.25 <= h <= 1.3 and 0.5 <= w / max(h, 0.01) <= 2.0 and has_fill(sh) and not is_white(sh):
                icons.append((r, sh.name))  # Icon shapes (small filled shapes close to square. Connectors and markers excluded)
            elif sh.shape_type is not None and not is_band and w > 0.6 and h > 0.4:
                # Charts and tables carry their own content, so they are excluded from the empty panel check
                if not (getattr(sh, "has_chart", False) or getattr(sh, "has_table", False)):
                    rects.append((r, sh.name))
        if accent > 1: fails.append(f"[{n}] Accent color in {accent} places (limit 1)")
        # Text box overlap
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i][0], texts[j][0]
                ix, iy = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
                inter = ix * iy
                small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                if small > 0 and inter / small > 0.2 and not contains(a, b) and not contains(b, a):
                    ratio = inter / small
                    pic = "[picture]" in (texts[i][2], texts[j][2])
                    # Check whether the actual glyph areas overlap (excludes boxes that overlap while their glyphs stay apart)
                    ia = next((x[0] for x in ink if x[1] == texts[i][1] and x[2] == texts[i][2]), None)
                    ib = next((x[0] for x in ink if x[1] == texts[j][1] and x[2] == texts[j][2]), None)
                    hard = False
                    if ia and ib:
                        jx = max(0, min(ia[2], ib[2]) - max(ia[0], ib[0]))
                        jy = max(0, min(ia[3], ib[3]) - max(ia[1], ib[1]))
                        sm = min((ia[2] - ia[0]) * (ia[3] - ia[1]), (ib[2] - ib[0]) * (ib[3] - ib[1]))
                        hard = sm > 0 and jx * jy / sm > 0.3
                    msg = f"[{n}] {'Picture and text' if pic else 'Text'} overlap {texts[i][2]} / {texts[j][2]} ({ratio:.0%})"
                    (fails if pic or hard else warns).append(msg)
        # A label box placed inside a content box overlaps by design, so judge only by glyph areas
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i][0], texts[j][0]
                if not (contains(a, b) or contains(b, a)): continue
                la = next((x[0] for x in ink_lines if x[1] == texts[i][1] and x[2] == texts[i][2]), None)
                lb = next((x[0] for x in ink_lines if x[1] == texts[j][1] and x[2] == texts[j][2]), None)
                if not la or not lb: continue
                worst = 0.0
                for ia in la:
                    for ib in lb:
                        jx = max(0, min(ia[2], ib[2]) - max(ia[0], ib[0]))
                        jy = max(0, min(ia[3], ib[3]) - max(ia[1], ib[1]))
                        sm = min((ia[2] - ia[0]) * (ia[3] - ia[1]), (ib[2] - ib[0]) * (ib[3] - ib[1]))
                        if sm > 0: worst = max(worst, jx * jy / sm)
                if worst > LABEL_INK_RATIO:
                    warns.append(f"[{n}] Glyph overlap inside a box {texts[i][2]} / {texts[j][2]} ({worst:.0%})")
        # Tables, charts, pictures and panel boxes overlapping each other (combinations the text box check misses)
        boxes = []
        for sh in slide.shapes:
            if sh.top is None or sh.width is None: continue
            x, y = sh.left / 914400, sh.top / 914400
            w, h = sh.width / 914400, sh.height / 914400
            if w < 0.3 or h < 0.2 or y < RULE_Y * sy + 0.35 or y > NOTE_Y * sy - 0.05: continue
            if sh.has_table: boxes.append(((x, y, x + w, y + h), "table"))
            elif sh.has_chart: boxes.append(((x, y, x + w, y + h), "chart"))
            elif sh.shape_type is not None and str(sh.shape_type).startswith("PICTURE"): boxes.append(((x, y, x + w, y + h), "picture"))
            elif sh.has_text_frame and sh.text_frame.text.strip() and has_fill(sh) and not is_white(sh) and not is_pointed(sh):
                boxes.append(((x, y, x + w, y + h), f"box '{sh.text_frame.text.strip()[:10]}'"))
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i][0], boxes[j][0]
                ix, iy = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
                inter = ix * iy
                small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                # Tables, charts and pictures are defects past 15%, filled boxes with each other past 25% (allows interlocking boxes of source slides)
                both_box = boxes[i][1].startswith("box") and boxes[j][1].startswith("box")
                lim = 0.25 if both_box else 0.15
                if small > 0 and inter / small > lim and not contains(a, b) and not contains(b, a):
                    fails.append(f"[{n}] Element overlap {boxes[i][1]} / {boxes[j][1]} ({inter / small:.0%})")

        # Estimated mid-word line breaks: a word wider than the inner box width is cut in the middle by every renderer (text boxes and table cells)
        # Estimated line breaks inside a word: LibreOffice splits a word caught at the line end like '60|분', '○|○억원', '가|정)', '3-|5개' (text_metrics.break_in_word)
        # Why: in the A4, 10.83 and 4:3 renders of the two sample decks, 128 such breaks separate a unit from its number or push the character before a closing bracket to the next line. Comparing word widths does not find them.
        #      This estimate finds 93 of the 96 text boxes and tables with a rendered break inside a word and warns 2 wrongly (no WARN in 16:9)
        for sh in (slide.shapes if word_break else []):
            if sh.width is None: continue
            y = sh.top / 914400 if sh.top else 0
            if y < RULE_Y * sy + 0.35: continue
            hit, splits = None, []
            if sh.has_table:
                colw = [c.width / 914400 for c in sh.table.columns]
                for r in sh.table.rows:
                    for j, c in enumerate(r.cells):
                        if c.is_spanned or not c.text.strip(): continue
                        inner = sum(colw[j:j + c.span_width]) - c.margin_left / 914400 - c.margin_right / 914400
                        hit = hit or too_wide_word(c.text_frame.paragraphs, inner)
                        splits += token_splits(c.text_frame.paragraphs, inner)
            elif sh.has_text_frame and sh.text_frame.text.strip():
                bp = sh.text_frame._txBody.find(NSA + "bodyPr")
                if bp is not None and bp.get("wrap") == "none": continue
                if bp is not None and bp.get("vert") not in (None, "horz"): continue  # Vertical text (matrix y-axis labels, etc.) does not wrap by horizontal width
                ins = lambda k: int(bp.get(k)) / 914400 if bp is not None and bp.get(k) else 0.1
                hit = too_wide_word(sh.text_frame.paragraphs, sh.width / 914400 - ins("lIns") - ins("rIns"))
                splits = token_splits(sh.text_frame.paragraphs, sh.width / 914400 - ins("lIns") - ins("rIns"))
            if hit:
                warns.append(f"[{n}] Estimated mid-word line break '{hit[0][:14]}' (word width {hit[1]:.2f}in > inner width {hit[2]:.2f}in)")
            if splits:
                more = f" and {len(splits) - 1} more" if len(splits) > 1 else ""
                warns.append(f"[{n}] Estimated line break inside a word '{splits[0][:16]}'{more} (the renderer splits a word caught at the line end) → shorten the text, widen the box, or rewrite so the word does not fall at the line end")

        # Bordered boxes with little content and a large empty area
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip(): continue
            if sh.top is None or sh.height is None: continue
            y, hh = sh.top / 914400, sh.height / 914400
            ww = sh.width / 914400 if sh.width else 0
            if hh < 1.2 or ww < 1.5 or y < RULE_Y * sy + 0.35 or y > NOTE_Y * sy: continue
            if has_fill(sh) and not is_white(sh): continue  # Label cells (filled boxes) are skipped
            # Borderless text boxes inside a bordered panel are checked too (panels that look empty inside)
            inside_panel = any(rr[0] <= x0 and rr[1] <= y and rr[2] >= x0 + ww and rr[3] >= y + hh and (rr[2] - rr[0]) * (rr[3] - rr[1]) > ww * hh
                               for rr, _ in rects) if (x0 := (sh.left / 914400 if sh.left is not None else 0)) is not None else False
            if not has_outline(sh) and not inside_panel: continue
            txt0 = sh.text_frame.text.strip()
            if len(txt0) < 8: continue
            if re.fullmatch(r"(시각자료|이미지|사진|산출물 화면|도식)", txt0): continue  # Placeholder boxes
            paras = [p for p in sh.text_frame.paragraphs if p.runs and "".join(r.text for r in p.runs).strip()]
            if len(paras) < 2 and hh < 1.5: continue  # One-line label boxes (connection structures, etc.) are skipped
            need, avail, _ = overflow_estimate(sh)
            if avail > 0 and need / avail < LIM.get("LIMIT", {}).get("boxFillMin", 0.45):
                warns.append(f"[{n}] Thin box content {need / avail:.0%} fill '{sh.text_frame.text.strip()[:12]}' (add items, replace with a diagram or shrink the box)")

        # Large empty area at the body bottom (content crowded upward). Cover, contents and dividers are top-aligned by design and skipped
        has_headline = any(sh.has_text_frame and sh.text_frame.text.strip() and sh.top is not None and sh.width is not None
                           and 0.85 <= sh.top / 914400 <= 1.45 and sh.width / 914400 >= W * 0.6 for sh in slide.shapes)
        # Match the body band to the typesetting reference (a check band wider than the real one flags centered layouts as crowded)
        has_marker = any(sh.has_text_frame and sh.text_frame.text.strip() and sh.top is not None
                         and RULE_Y * sy + 0.05 <= sh.top / 914400 <= RULE_Y * sy + 0.45 for sh in slide.shapes)
        has_note_row = any(sh.has_text_frame and sh.text_frame.text.strip() and sh.top is not None and sh.left is not None
                           and NOTE_Y * sy - 0.06 <= sh.top / 914400 <= NOTE_Y * sy + 0.3
                           and sh.left / 914400 < W * 0.5 for sh in slide.shapes)
        band_top = (CONTENT_Y if has_marker else CONTENT_Y_NO_MARKER) * sy + BODY_PAD * sy
        band_bottom = (NOTE_Y - 0.12 if has_note_row else CONTENT_BOTTOM) * sy - 0.05
        band_left, band_right = EDGE, W - EDGE
        top_c, bot_c, left_c, right_c = band_bottom, band_top, band_right, band_left
        has_body = False
        for sh in slide.shapes:
            if sh.top is None or sh.height is None or sh.left is None or sh.width is None: continue
            y, hh = sh.top / 914400, sh.height / 914400
            x, ww = sh.left / 914400, sh.width / 914400
            if y + hh < band_top + 0.08 or y > band_bottom: continue  # Marker band and divider lines are skipped
            if sh.has_text_frame and not sh.text_frame.text.strip() and not sh.has_table and not sh.has_chart: continue
            has_body = True
            top_c = min(top_c, max(y, band_top)); bot_c = max(bot_c, min(y + hh, band_bottom))
            left_c = min(left_c, max(x, band_left)); right_c = max(right_c, min(x + ww, band_right))
        band_h, band_w = band_bottom - band_top, band_right - band_left
        lim = LIM.get("LIMIT", {}).get("bandBottomGapMax", 0.3)
        if has_headline and has_body and band_h > 1.0:
            # Flag crowding only when one margin is large and the opposite one small (centered layouts are skipped)
            pairs = ((("bottom", (band_bottom - bot_c) / band_h), ("top", (top_c - band_top) / band_h)),
                     (("right", (band_right - right_c) / band_w), ("left", (left_c - band_left) / band_w)))
            for (n1, g1), (n2, g2) in pairs:
                big, small_gap = (n1, g1) if g1 >= g2 else (n2, g2), min(g1, g2)
                if big[1] > lim and small_gap < big[1] * 0.6:
                    warns.append(f"[{n}] Body {big[0]} margin {big[1]:.0%} (content crowded to one side)")
            # Boxes shrink to their content height, so even a centered layout lacks content when much body height remains
            cover = (bot_c - top_c) / band_h
            if cover < LIM.get("LIMIT", {}).get("bodyCoverMin", 0.7):
                warns.append(f"[{n}] Body vertical fill {cover:.0%} (add content or change the layout type)")

        # Collect headline fonts (for the deck-wide consistency check)
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip(): continue
            y = sh.top / 914400 if sh.top else 0
            w = sh.width / 914400 if sh.width else 0
            if 0.85 <= y <= 1.45 and w >= W * 0.6:
                pts = [r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs if r.font.size]
                if pts: headline_pts.append((n, max(pts)))
                break

        # Alignment consistency: tables per column, side-by-side boxes per tier
        for sh in slide.shapes:
            if not sh.has_table: continue
            cols_align = {}
            for r_i, row in enumerate(sh.table.rows):
                if r_i == 0: continue  # The header row is centered by default, so it is not compared
                for c_i, cell in enumerate(row.cells):
                    if not cell.text.strip(): continue
                    if any(r.font.bold for p in cell.text_frame.paragraphs for r in p.runs): continue  # Header and total rows are skipped
                    al = {p.alignment for p in cell.text_frame.paragraphs if p.alignment is not None}
                    if len(al) == 1: cols_align.setdefault(c_i, set()).add(next(iter(al)))
            odd = [c for c, a in cols_align.items() if len(a) > 1]
            if odd: warns.append(f"[{n}] Mixed table column alignment (columns {sorted(odd)})")

        rows_by_y = {}
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip() or sh.top is None: continue
            y = round(sh.top / 914400, 1); h = round(sh.height / 914400, 1)
            al = {p.alignment for p in sh.text_frame.paragraphs if p.alignment is not None}
            if len(al) == 1: rows_by_y.setdefault((y, h), []).append(next(iter(al)))
        for (y, h), als in rows_by_y.items():
            if len(als) >= 3 and len(set(als)) > 1 and h > 0.3:
                warns.append(f"[{n}] Mixed alignment in side-by-side boxes (y {y}in, {len(set(als))} kinds)")

        # Tables running off the bottom and fill colors outside the allowed set
        for sh in slide.shapes:
            if not sh.has_table: continue
            top = sh.top / 914400 if sh.top else 0
            bottom = top + (sh.height / 914400 if sh.height else 0)
            if bottom > H - 0.05:
                fails.append(f"[{n}] Table runs off the slide (bottom {bottom:.2f}in > limit {H - 0.05:.2f}in, {len(sh.table.rows)} rows)")
            elif bottom > H - EDGE + 0.05:
                warns.append(f"[{n}] Table enters the bottom margin (bottom {bottom:.2f}in > {H - EDGE:.2f}in)")
            for r in range(len(sh.table.rows)):
                for c in range(len(sh.table.columns)):
                    cell = sh.table.cell(r, c)
                    try:
                        if cell.fill.type != 1: continue
                        rgb = str(cell.fill.fore_color.rgb).upper()
                    except Exception:
                        continue
                    if rgb not in palette:
                        warns.append(f"[{n}] Table cell fill outside the palette #{rgb} (row {r + 1}, column {c + 1})")
                        break
                else:
                    continue
                break

        # Different font sizes among same-tier paragraphs in one box make one item stand out (note lines excluded)
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip(): continue
            y = sh.top / 914400 if sh.top else 0
            if y < RULE_Y * sy + 0.3: continue
            lv = {}
            for pa in sh.text_frame.paragraphs:  # Compare only bulleted paragraphs (title lines and notes excluded)
                txt = "".join(r.text for r in pa.runs).strip()
                if not txt or re.match(r"^\s*(※|\*|출처|자료|[Ss]ources?\s*[:：]|[Nn]otes?\s*[:：])", txt): continue
                xml = pa._p.xml
                if "buChar" not in xml and "buAutoNum" not in xml: continue
                sz = max((r.font.size.pt for r in pa.runs if r.font.size), default=None)
                if sz: lv.setdefault(pa.level, set()).add(sz)
            odd = [(l, sorted(v)) for l, v in lv.items() if len(v) > 1]
            if odd:
                warns.append(f"[{n}] Mixed font sizes in a box {odd[0][1]} '{sh.text_frame.text.strip()[:14]}' (same tier, same size)")

        # Empty cells in the table category column: empty without a merge, the table looks broken
        for sh in slide.shapes:
            if not sh.has_table: continue
            tbl = sh.table
            # Empty rows following a filled row in the category column (column 1) suggest a missing merge
            # Column 1 empty while other columns have values, without a merge, suggests a missing merge
            gap = 0
            for r in range(1, len(tbl.rows)):
                c0 = tbl.cell(r, 0)
                if c0.text.strip() or c0.is_spanned: continue
                # Rows with only the last column filled, as in sample tables, are skipped
                vals = [tbl.cell(r, c).text.strip() for c in range(1, len(tbl.columns))]
                if sum(1 for v in vals if v) >= 2:
                    gap += 1
            if gap >= 2:
                warns.append(f"[{n}] {gap} empty cells in table column 1 (missing merge suspected)")

        # Mixed vertical alignment in tables (mixed horizontal alignment is judged by the per-column check)
        for sh in slide.shapes:
            if not sh.has_table: continue
            tbl = sh.table
            valigns = {str(tbl.cell(r, c).vertical_anchor) for r in range(len(tbl.rows)) for c in range(len(tbl.columns))
                       if tbl.cell(r, c).text.strip() and tbl.cell(r, c).vertical_anchor is not None}
            if len(valigns) > 1:
                warns.append(f"[{n}] Mixed vertical alignment in table {sorted(valigns)}")

        # Icon and text overlap: an icon shape entering a text area
        for ir, iname in icons:
            for tr, tname, ttext in ink:
                # Text boxes placed on a shape (text fully inside the shape, like stage names on funnel bands) are intended and skipped
                if ir[0] - 0.01 <= tr[0] and ir[1] - 0.01 <= tr[1] and tr[2] <= ir[2] + 0.01 and tr[3] <= ir[3] + 0.01: continue
                ix = max(0, min(ir[2], tr[2]) - max(ir[0], tr[0]))
                iy = max(0, min(ir[3], tr[3]) - max(ir[1], tr[1]))
                area = (ir[2] - ir[0]) * (ir[3] - ir[1])
                if area > 0 and ix * iy / area > 0.25:
                    fails.append(f"[{n}] Icon and text overlap {iname} / '{ttext}' ({ix * iy / area:.0%})")
                    break

        # Empty panels: no text box inside a box without text
        for r, name in rects:
            if not any(contains(r, t[0]) or overlaps(r, t[0]) for t in texts):
                warns.append(f"[{n}] Empty panel {name} ({r[0]:.2f},{r[1]:.2f})")
    # Headline font consistency: report slides that differ from the most common size (tallied before output)
    if headline_pts:
        from collections import Counter
        mode_pt = Counter(pt for _, pt in headline_pts).most_common(1)[0][0]
        odd = [(n, pt) for n, pt in headline_pts if abs(pt - mode_pt) > 0.1]
        if odd and len(odd) <= len(headline_pts) / 2:
            warns.append(f"Headline font mismatch: base {mode_pt:g}pt, differing slides {[f'{n}({pt:g}pt)' for n, pt in odd[:8]]} → unless these are custom slide playback, set the headline size to 18pt")

    for f in fails: print("FAIL", f)
    for w in warns: print("WARN", w)
    print(f"check_layout: FAIL {len(fails)} WARN {len(warns)} slides {len(prs.slides)}")
    # Warnings also fail by default. To pass with a stated reason, add --allow-warn "reason"
    allow = sys.argv[sys.argv.index("--allow-warn") + 1] if "--allow-warn" in sys.argv else None
    if fails:
        sys.exit(1)
    if warns and not allow:
        print("check_layout: failing because WARNs remain. Fix them or pass with --allow-warn \"reason for keeping\"")
        sys.exit(1)
    if warns and allow:
        print(f"check_layout: {len(warns)} WARNs kept (reason: {allow})")
    sys.exit(0)


def has_outline(sh):
    """Whether the box has a visible border (False with no line)"""
    try:
        return sh.line.fill.type not in (5, None) or sh.line.width is not None
    except Exception:
        return False


def has_fill(sh):
    """True if the shape has a fill color (line-only boxes excluded)"""
    try:
        return sh.fill.type != 5  # 5 = MSO_FILL.BACKGROUND (no fill). None is the theme default fill
    except Exception:
        return False


def is_pointed(sh):
    """Chevrons and home plates are designed to interlock at their tips, so they are excluded from the overlap check"""
    try:
        return "CHEVRON" in str(sh.auto_shape_type) or "HOME_PLATE" in str(sh.auto_shape_type) or "PENTAGON" in str(sh.auto_shape_type)
    except Exception:
        return False


def is_white(sh):
    """White-filled shapes (donut hole covers, etc.) are excluded from icon detection"""
    try:
        return sh.fill.type == 1 and str(sh.fill.fore_color.rgb) == "FFFFFF"
    except Exception:
        return False


def contains(a, b):
    return a[0] <= b[0] + 0.02 and a[1] <= b[1] + 0.02 and a[2] >= b[2] - 0.02 and a[3] >= b[3] - 0.02


def overlaps(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]) > 0.05 and min(a[3], b[3]) - max(a[1], b[1]) > 0.05


if __name__ == "__main__":
    main()
