"""Converts other inputs (DOCX, XLSX, HWPX) into a level-convention Markdown manuscript. Changes only the structure without retyping the text."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import config as C
from config import msg

ROLE_MD = {"chapter": "# ", "section": "## ", "subsection": "### ", "ganada": "#### ", "square": "□ ",
           "circle": "- ", "dash": "    - ", "dot": "        - ", "note": "※ ", "source": "> ",
           "table_title": "<표> ", "fig_title": "[그림] "}
LEADING_MARK_RE = re.compile(r"^(제\s*\d+\s*장|\d+(?:\.\d+)*\.?|[가-힣]\.|[□■○❍◦ㅇ\-ㆍ·※*]|<표[^>]*>|\[그림[^\]]*\])\s*")
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"


def _pipe_table(rows: list[list[str]]) -> list[str]:
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    return ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width] + ["| " + " | ".join(r) + " |" for r in rows[1:]] + [""]


def guess_role(text: str) -> str | None:
    """Guesses the role of a paragraph whose role cannot be found from the style name (documents with symbols typed by hand)"""
    for pat, role in ((r"^제\s*\d+\s*장\b", "chapter"), (r"^\d+\.\d+\.\d+\s", "subsection"), (r"^\d+\.\d+\s", "section"),
                      (r"^[가-힣]\.\s", "ganada"), (r"^[□■]", "square"), (r"^[○❍◦ㅇ]", "circle"),
                      (r"^-\s", "dash"), (r"^[ㆍ·•]", "dot"), (r"^[※*]", "note"), (r"^(자료|출처)\s*[:：]", "source"),
                      (r"^<표", "table_title"), (r"^\[그림", "fig_title")):
        if re.match(pat, text):
            return role
    return None


def hwpx_to_md(src: str, out: str | None, profile_spec: str | None, image_dir: str | None):
    """Creates a manuscript from an existing HWPX: plain viewing (Markdown export with formatting) or level restoration (--profile).
    Level restoration maps style names back to roles and guesses the rest from symbols and numbering patterns. Figures, footnotes, and superscripts/subscripts are not restored."""
    from hwpx import HwpxDocument
    from hwpx_writer import load_profile
    doc = HwpxDocument.open(os.path.abspath(src))
    out = out or os.path.splitext(src)[0] + ".md"
    if not profile_spec:
        kw = {"image_dir": image_dir, "image_ref_prefix": os.path.basename(image_dir) + "/"} if image_dir else {}
        md = doc.text.markdown(rich=True, detect_headings=True, **kw)
        Path(out).write_text(md, encoding="utf-8")
        print(msg("export_ok", out=out, n=len(md), extra=""))
        return
    profile = load_profile(profile_spec)
    rev = {v: k for k, v in profile.items() if isinstance(v, str) and k in ROLE_MD}
    names = {sid: st.name for sid, st in doc.styles.items()}
    images = {it.item_id: it for it in doc.media.images}
    lines, img_n = [], 0
    if image_dir:
        os.makedirs(image_dir, exist_ok=True)
    for sec in doc.sections:
        for p in sec.paragraphs:
            pics = list(p.element.iter(f"{HP}pic"))
            if pics and image_dir:
                for pic in pics:
                    ref = next((x for x in pic.iter() if x.tag.endswith("}img")), None)
                    item = images.get(ref.get("binaryItemIDRef")) if ref is not None else None
                    if item is None:
                        continue
                    img_n += 1
                    fn = f"img{img_n:03d}.{item.format}"
                    Path(image_dir, fn).write_bytes(doc.package.read(item.href))
                    lines.append(f"![]({os.path.basename(image_dir)}/{fn})")
            if p.tables:
                for t in p.tables:
                    grid, seen = [], set()
                    for row in t.get_cell_map():   # merged cells: content only at the first position, the rest empty
                        line = []
                        for pos in row:
                            key = id(pos.cell.element)
                            line.append("" if key in seen else pos.cell.text.replace("\n", "<br>"))
                            seen.add(key)
                        grid.append(line)
                    cap = t.caption.text.strip() if getattr(t, "caption", None) else ""
                    if cap:
                        lines.append("<표> " + LEADING_MARK_RE.sub("", cap))
                    lines.extend(_pipe_table(grid))
                continue
            text = p.text.strip()
            if not text:
                continue
            role = rev.get(names.get(str(p.style_id_ref), ""), None) or guess_role(text)
            lines.append(ROLE_MD[role] + LEADING_MARK_RE.sub("", text) if role else text)
    md = "\n".join(lines) + "\n"
    Path(out).write_text(md, encoding="utf-8")
    print(msg("export_ok", out=out, n=len(md), extra=msg("export_hier")))


def _docx_para_key(p) -> str:
    """Level key of a paragraph: style name | left indent | autonumbered | leading symbol"""
    pf = p.paragraph_format
    indent = int((pf.left_indent or 0) / 12700 * 10) if pf.left_indent is not None else 0
    numbered = p._p.pPr is not None and p._p.pPr.numPr is not None
    lead = p.text.lstrip()[:1] if p.text.strip() else ""
    lead = lead if lead in "□■○◦❍ㅇ-ㆍ·※*" else ""
    return f"{p.style.name}|{indent}|{'num' if numbered else ''}|{lead}"


def docx_to_md(src: str, out: str | None, mapping: str | None):
    """Step 1 (no mapping): print counts and samples per paragraph type. Step 2: create the manuscript with the mapping JSON agreed with the user."""
    import docx
    d = docx.Document(src)
    if not mapping:
        keys: dict[str, list[str]] = {}
        for p in d.paragraphs:
            if p.text.strip():
                keys.setdefault(_docx_para_key(p), []).append(p.text.strip()[:40])
        print(msg("docx2md_keys"))
        for k, v in sorted(keys.items(), key=lambda kv: -len(kv[1])):
            print(msg("docx2md_key_line", key=k, n=len(v), sample=v[0]))
        print(msg("docx2md_roles"))
        return
    mp = json.loads(Path(mapping).read_text(encoding="utf-8"))
    lines = []
    pi, ti = 0, 0
    for child in d.element.body.iterchildren():
        tag = child.tag.split("}")[1]
        if tag == "p":
            p = d.paragraphs[pi]
            pi += 1
            if not p.text.strip():
                continue
            role = mp.get(_docx_para_key(p), "circle")
            if role == "skip":
                continue
            lines.append(ROLE_MD[role] + LEADING_MARK_RE.sub("", p.text.strip()))
        elif tag == "tbl":
            t = d.tables[ti]
            ti += 1
            lines.extend(_pipe_table([[c.text.strip().replace("\n", "<br>") for c in r.cells] for r in t.rows]))
    o = out or os.path.splitext(src)[0] + ".md"
    Path(o).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(msg("docx2md_ok", out=o, paras=pi, tables=ti))


def xlsx_to_md(src: str, out: str | None, allow_wide: bool):
    """Creates a <표> caption and a pipe table per sheet. When there are many columns, prints a notice to ask the user about transposing or splitting."""
    import openpyxl
    wb = openpyxl.load_workbook(src, data_only=True)
    lines = []
    for ws in wb.worksheets:
        rows = [[("" if v is None else (f"{v:,}" if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)).strip())
                 for v in r] for r in ws.iter_rows(values_only=True)]
        rows = [r for r in rows if any(r)]
        if not rows:
            continue
        ncol = max(len(r) for r in rows)
        if ncol > C.XLSX_WIDE_COLS and not allow_wide:
            print(msg("xlsx2md_wide", sheet=ws.title, n=ncol))
        lines.append(f"<표> {ws.title}")
        lines.extend(_pipe_table(rows))
    o = out or os.path.splitext(src)[0] + ".md"
    Path(o).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(msg("xlsx2md_ok", out=o, n=len(wb.worksheets)))
