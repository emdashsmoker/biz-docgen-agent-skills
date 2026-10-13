"""HWPX typesetter: places manuscript elements on the skeleton with python-hwpx.
The skeleton is generated from a built-in form (form.py) or extracted from a user form."""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import lxml.etree as ET

import config as C
import manuscript as M
from config import msg
from form import FORMS
from hwpx_form import write_skeleton

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
HC = "{http://www.hancom.co.kr/hwpml/2011/core}"
# character shape changes per inline format kind (_run_style arguments)
INLINE_STYLE = {"bold": {"bold": True}, "italic": {"italic": True}, "sup": {"script": "sup"}, "sub": {"script": "sub"}}
MANUAL_SYMBOLS = {"square": "□ ", "circle": "○ ", "dash": "- ", "dot": "ㆍ ", "note": "※ "}
ROLE_KEYS = ("body", "chapter", "section", "subsection", "ganada", "square", "circle", "dash", "dot", "note",
             "table_pos", "table_cell", "table_cell_left", "table_title", "unit", "source", "fig_pos", "fig_title",
             "toc_chapter", "toc_section", "table_cell_bullet", "table_cell_dash")
FORMAT_FLAGS = ("bold", "italic", "supscript", "subscript")


def load_profile(spec: str) -> dict:
    """Builds a profile: for a built-in form name, from the form.py style names and numbering; for a JSON path, from its content."""
    if spec in FORMS:
        names = {st.role: st.name for st in FORMS[spec].styles}
        prof = dict(C.PROFILE_FORMATS[spec])
        for role in ROLE_KEYS:
            if role in names:
                prof[role] = names[role]
        prof.setdefault("table_cell_left", names["table_cell"])   # forms without a left-aligned table content style
        return prof
    return {**C.PROFILE_DEFAULTS, **json.loads(Path(spec).read_text(encoding="utf-8"))}


def builtin_skeleton(form_name: str, workdir: str) -> str:
    path = os.path.join(workdir, f"_skeleton_{form_name}.hwpx")
    return write_skeleton(FORMS[form_name], path)


class Builder:
    def __init__(self, skeleton: str, profile: dict, page_break: str = "chapter"):
        try:
            from hwpx import HwpxDocument
        except ImportError:
            sys.exit(msg("err_no_hwpx"))
        try:
            with zipfile.ZipFile(skeleton) as z:
                bad = z.testzip()
            if bad:
                sys.exit(msg("err_skeleton_zip", item=bad))
            self.doc = HwpxDocument.open(os.path.abspath(skeleton))
        except SystemExit:
            raise
        except Exception as ex:
            sys.exit(msg("err_skeleton_load", err=f"{type(ex).__name__}: {ex}"))
        self.p = profile
        self.numbering = M.Numbering(page_break)
        self.styles = {s.name: (sid, s) for sid, s in self.doc.styles.items()}
        missing = [v for k, v in profile.items() if k not in C.NON_ROLE_KEYS and v is not None and v not in self.styles]
        if missing:
            sys.exit(msg("err_missing_styles", names=missing))
        self.headings: list[tuple[int, str]] = []
        self.toc_numbers: dict[int, int] = {}   # TOC entry index → page number
        self.header = self.doc.parts.headers[0]
        self.body_w = self._body_width()
        self.table_max_w = self.body_w - C.TABLE_INDENT_MARGIN
        self._pp_cache: dict = {}
        self._cp_cache: dict = {}
        self.pending_break = False
        self.manual_symbol = self._manual_symbols()
        self._warned: set[str] = set()
        self.last_para = None
        self.last_cp = None   # base character shape of the previous paragraph (used for the reference run of a footnote made from a source line)
        self.caption_counts = {"TABLE": 0, "PICTURE": 0}   # numbers stored in the caption number fields
        # typesetting options (set in cmd_build)
        self.numbered_square = False
        self.toc = False
        self.toc_depth = 2
        self.cover = None
        self.page_number = False
        self.header_spec = None
        self.merge_mode = "auto"
        self.long_table_mode = "engine"

    def _manual_symbols(self) -> dict[str, str]:
        """If the style's heading is BULLET, Hangul draws the symbol; otherwise the symbol is written into the text."""
        out = {}
        for role, sym in MANUAL_SYMBOLS.items():
            if self.p.get(role) is None:
                continue
            pp_id = str(self.styles[self.p[role]][1].para_pr_id_ref)
            el = self.header.element.find(f".//{HH}paraPr[@id='{pp_id}']")
            hd = el.find(f"{HH}heading") if el is not None else None
            if (hd.get("type") if hd is not None else "NONE").upper() != "BULLET":
                out[role] = sym
        return out

    # ── Basic elements ─────────────────────────────────────────────────────
    def _body_width(self) -> int:
        sp = self.doc.sections[0].properties
        return sp.page_size.width - sp.page_margins.left - sp.page_margins.right

    def refs(self, role: str) -> dict:
        if self.p.get(role) is None and role not in self._warned:
            self._warned.add(role)
            print(msg("warn_no_style", role=role))
        sid, s = self.styles[self.p.get(role) or self.p["body"]]
        return {"style_id_ref": sid, "para_pr_id_ref": s.para_pr_id_ref, "char_pr_id_ref": s.char_pr_id_ref}

    def _run_style(self, base_cp: str, **fmt) -> str:
        """Clones the base character shape and adds only bold, italic, or super/subscript.
        When reusing an existing character shape, checks that every attribute except these format flags equals the base.
        Comparing only some attributes would reuse a character shape with different spacing or width ratio."""
        key = (base_cp,) + tuple(sorted(fmt.items()))
        if key in self._cp_cache:
            return self._cp_cache[key]
        base = self.header.element.find(f".//{HH}charPr[@id='{base_cp}']")
        wanted = [t for t, on in (("bold", fmt.get("bold")), ("italic", fmt.get("italic")),
                                  ({"sup": "supscript", "sub": "subscript"}.get(fmt.get("script")), True)) if on and t]

        def signature(e):
            attrs = tuple(sorted((k, v) for k, v in e.attrib.items() if k != "id"))
            kids = tuple(ET.tostring(c) for c in e if c.tag.split("}")[1] not in FORMAT_FLAGS)
            return attrs, kids

        def flags(e):
            return {c.tag.split("}")[1] for c in e} & set(FORMAT_FLAGS)

        base_sig = signature(base)

        def same(e):
            return signature(e) == base_sig and flags(e) == set(wanted) | flags(base)

        def add(e):
            anchor = e.find(f"{HH}offset")
            idx = list(e).index(anchor) + 1 if anchor is not None else len(e)
            for t in wanted:
                if e.find(f"{HH}{t}") is None:
                    e.insert(idx, ET.Element(f"{HH}{t}"))
                    idx += 1

        el = self.header.ensure_char_property(predicate=same, modifier=add, base_char_pr_id=base_cp)
        self._cp_cache[key] = el.get("id")
        return self._cp_cache[key]

    def para(self, role: str, text: str, footnotes: dict | None = None, no_heading: bool = False, **attrs):
        """Formatting applies only when all three references (style, paragraph shape, character shape) are set together."""
        r = self.refs(role)
        if role == "square" and self.numbered_square and M.NUMBERED_SQUARE_RE.match(text):   # 1. 2. 3. numbered headers
            r["para_pr_id_ref"] = self._numbered_pp(str(r["para_pr_id_ref"]), str(r["char_pr_id_ref"]), text)
        elif no_heading:   # numbers are written into the text, so the style's automatic outline number is turned off
            r["para_pr_id_ref"] = self._no_bullet_pp(str(r["para_pr_id_ref"]))
        else:
            text = self.manual_symbol.get(role, "") + text
        p = self.doc.add_paragraph("", **r, **self._take_break(attrs))
        cp = str(r["char_pr_id_ref"])
        for kind, seg in M.inline_segments(text):
            if kind == "bold":
                p.add_run(seg, char_pr_id_ref=self._run_style(cp, bold=True))
            elif kind == "italic":
                p.add_run(seg, char_pr_id_ref=self._run_style(cp, italic=True))
            elif kind in ("sup", "sub"):
                p.add_run(seg, char_pr_id_ref=self._run_style(cp, script=kind))
            elif kind == "footnote":
                if footnotes is not None:
                    self._add_footnote(p, footnotes.get(seg, ""), cp)
            else:
                p.add_run(seg, char_pr_id_ref=cp)
        return p

    def _add_footnote(self, p, text: str, body_cp: str):
        """Places the footnote reference in a run with the paragraph's base character shape and applies the same inline formatting as body text to the footnote text.
        The library puts the reference in the paragraph's last run (subscript, bold, etc.) and builds the footnote text with a single character shape"""
        note = p.add_footnote("", run_attributes={"charPrIDRef": str(body_cp)})
        run = note.element.find(f".//{HP}subList/{HP}p/{HP}run")   # the run holding the footnote number
        base_cp = run.get("charPrIDRef")
        empty_t = run.find(f"{HP}t")
        if empty_t is not None:
            run.remove(empty_t)
        for kind, seg in M.inline_segments(text):
            if kind == "footnote":   # footnote references inside a footnote are not used
                continue
            cp = self._run_style(base_cp, **INLINE_STYLE[kind]) if kind in INLINE_STYLE else base_cp
            new_run = ET.SubElement(run.getparent(), f"{HP}run", charPrIDRef=str(cp))
            ET.SubElement(new_run, f"{HP}t").text = seg

    def _inline_runs(self, pe, base_cp: str):
        """Splits inline format markup (bold, italic, super/subscript) in a cell paragraph into runs with different character shapes.
        Footnote references in cells are not supported, so their markup stays as written"""
        runs = pe.findall(f"{HP}run")
        if not runs:
            return
        text = "".join(t.text or "" for r in runs for t in r.findall(f"{HP}t"))
        segs = M.inline_segments(text)
        if all(kind == "plain" for kind, _ in segs):
            return
        idx = list(pe).index(runs[0])   # put back at the original run position (before other elements in the paragraph)
        for r in runs:
            pe.remove(r)
        for kind, seg in segs:
            if kind == "footnote":
                kind, seg = "plain", f"[^{seg}]"
            cp = self._run_style(base_cp, **INLINE_STYLE[kind]) if kind in INLINE_STYLE else base_cp
            new_run = ET.Element(f"{HP}run", charPrIDRef=str(cp))
            ET.SubElement(new_run, f"{HP}t").text = seg
            pe.insert(idx, new_run)
            idx += 1

    def _take_break(self, attrs: dict | None = None) -> dict:
        """Applies a '---' page break to the next paragraph or to the paragraph holding a table or figure"""
        attrs = dict(attrs or {})
        if self.pending_break:
            attrs["pageBreak"] = "1"
            self.pending_break = False
        return attrs

    def _centered_refs(self, role: str) -> dict:
        """Table and figure paragraphs are centered regardless of style alignment, so a table does not stick to the left even if a user form's table position style is left-aligned."""
        r = self.refs(role)
        if self._pp_align(r["para_pr_id_ref"]) != "CENTER":
            r["para_pr_id_ref"] = self._aligned_pp(str(r["para_pr_id_ref"]), "CENTER")
        return r

    def _pp_align(self, pp_id) -> str | None:
        el = self.header.element.find(f".//{HH}paraPr[@id='{pp_id}']")
        al = el.find(f"{HH}align") if el is not None else None
        return al.get("horizontal") if al is not None else None

    def _aligned_pp(self, base_pp: str, align: str) -> str:
        key = (str(base_pp), align)
        if key not in self._pp_cache:
            self._pp_cache[key] = self.header.ensure_paragraph_format(base_para_pr_id=base_pp, alignment=align)
        return self._pp_cache[key]

    def _no_bullet_pp(self, base_pp: str) -> str:
        key = (base_pp, "NOBULLET")
        if key not in self._pp_cache:
            self._pp_cache[key] = self.header.ensure_paragraph_format(
                base_para_pr_id=base_pp, heading={"type": "NONE", "idRef": "0", "level": "0"})
        return self._pp_cache[key]

    def _numbered_pp(self, base_pp: str, cp: str, text: str) -> str:
        """Paragraph shape for numbered headings. Turns off the bullet and hangs by the number width so the second line aligns with the text after the number.
        Justified alignment stretches the spaces of a wrapped first line and shifts the text after the number, so the alignment is left"""
        height = int(self.header.element.find(f".//{HH}charPr[@id='{cp}']").get("height"))
        hang = round(height * M.number_prefix_em(text, C.SPACE_EM_HWPX))
        key = (base_pp, "NUMBERED", hang)
        if key not in self._pp_cache:
            # Hangul hanging indent keeps the first line at the left margin and starts later lines indented by the hanging width (negative intent)
            pp = self.header.ensure_paragraph_format(base_para_pr_id=self._no_bullet_pp(base_pp), alignment="LEFT",
                                                     margins={"intent": -hang})
            # the stored value for older Hangul versions (hp:default) is written as twice the new value (same rule as form generation)
            legacy = self.header.element.find(f".//{HH}paraPr[@id='{pp}']//{HP}default/{HH}margin/{HC}intent")
            if legacy is not None:
                legacy.set("value", str(-2 * hang))
            self._pp_cache[key] = pp
        return self._pp_cache[key]

    def gap(self):
        for _ in range(C.BLOCK_GAP_LINES):
            self.doc.add_paragraph("", **self.refs("body"))

    def _cover_char(self, size_pt: float, bold: bool) -> str:
        base = str(self.refs("chapter")["char_pr_id_ref"])
        height = str(round(size_pt * 100))

        def mod(e):
            e.set("height", height)
            b = e.find(f"{HH}bold")
            if bold and b is None:
                anchor = e.find(f"{HH}offset")
                e.insert(list(e).index(anchor) + 1, ET.Element(f"{HH}bold"))
            if not bold and b is not None:
                e.remove(b)
        font = self.header.element.find(f".//{HH}charPr[@id='{base}']").find(f"{HH}fontRef").get("hangul")
        return self.header.ensure_char_property(
            predicate=lambda e: e.get("height") == height and e.find(f"{HH}fontRef").get("hangul") == font
            and (e.find(f"{HH}bold") is not None) == bold, modifier=mod, base_char_pr_id=base).get("id")

    def _front_matter(self, cover: dict | None):
        """Places the cover and TOC in the front section and moves the body to a new section. Body page numbers start at 1."""
        s0 = self.doc.sections[0]
        s1 = self.doc.add_section(after=0)
        old = s1.paragraphs[0].element
        old.getparent().replace(old, copy.deepcopy(s0.paragraphs[0].element))
        for p in list(s0.element)[1:]:
            s0.element.remove(p)
            s1.element.append(p)
        sn = s1.paragraphs[0].element.find(f".//{HP}startNum")
        if sn is not None:
            sn.set("page", "1")
        body_ref = self.refs("body")
        center = self._aligned_pp(str(body_ref["para_pr_id_ref"]), "CENTER")

        def front(text="", cp=None, pp=center, **attrs):
            p = self.doc.add_paragraph("", **body_ref, **attrs)
            p.element.set("paraPrIDRef", pp)
            if text:
                p.add_run(text, char_pr_id_ref=cp or str(body_ref["char_pr_id_ref"]))
            s0.element.append(p.element)   # add_paragraph appends to the last section, so move to the front section
            return p
        if cover:
            for _ in range(C.COVER_TOP_LINES):
                front()
            front(cover.get("title", ""), self._cover_char(C.COVER_TITLE_PT, True))
            if cover.get("subtitle"):
                front()
                front(cover["subtitle"], self._cover_char(C.COVER_SUB_PT, False))
            front()
            front()
            if cover.get("date"):
                front(cover["date"], self._cover_char(C.COVER_DATE_PT, False))
            for _ in range(C.COVER_GAP_LINES):
                front()
            if cover.get("org"):
                front(cover["org"], self._cover_char(C.COVER_ORG_PT, True))
        if self.toc:
            if not (self.p.get("toc_chapter") and self.p.get("toc_section")):
                print(msg("warn_no_toc_style"))
            else:
                ch = self.refs("chapter")
                front(C.TOC_TITLE, str(ch["char_pr_id_ref"]), self._aligned_pp(str(ch["para_pr_id_ref"]), "CENTER"),
                      pageBreak="1" if cover else "0")
                sub_pp = None
                for idx, (lv, text) in enumerate(M.toc_entries(self.headings, self.toc_depth)):
                    r = self.refs("toc_chapter" if lv == 1 else "toc_section")
                    pp = str(r["para_pr_id_ref"])
                    if lv >= 3:
                        if sub_pp is None:
                            sub_pp = self.header.ensure_paragraph_format(base_para_pr_id=pp, margins={"left": C.TOC_SUB_INDENT})
                        pp = sub_pp
                    p = front(text, str(r["char_pr_id_ref"]), pp)
                    p.element.set("styleIDRef", str(r["style_id_ref"]))
                    num = self.toc_numbers.get(idx)
                    if num:
                        tnode = [t for t in p.element.iter(f"{HP}t") if t.text][-1]
                        left = C.TOC_SUB_INDENT if lv >= 3 else (0 if lv == 1 else C.TOC_SECTION_INDENT)
                        unit = 700 if lv == 1 else 600   # estimated width of one character at 14pt (chapter) and 12pt (section) (HWPUNIT)
                        width = max(C.TOC_TAB_POS - left - M.weighted_len(text) * unit - len(str(num)) * unit, 1000)
                        ET.SubElement(tnode, f"{HP}tab", width=str(width), leader="3", type="2").tail = str(num)
        for sec in (s0, s1):
            sec.mark_dirty() if hasattr(sec, "mark_dirty") else None

    def set_header(self, spec: str | None):
        """Header (default OFF). "text;align=LEFT|CENTER|RIGHT". Applies only to the body section.
        python-hwpx writes the header in two places, inside secPr and as a ctrl, so the copy inside secPr is removed and the ctrl copy gets the paragraph alignment."""
        if not spec:
            return
        text, align = parse_header_spec(spec)
        sec = self.doc.sections[-1]
        self.doc.page.set_header(text=text, section=sec)
        pp = self._aligned_pp(str(self.refs("body")["para_pr_id_ref"]), align)
        first = sec.paragraphs[0].element
        sec_pr = first.find(f".//{HP}secPr")
        if sec_pr is not None:
            for h in list(sec_pr.iter(f"{HP}header")):
                h.getparent().remove(h)
        for h in first.iter(f"{HP}header"):
            for pe in h.iter(f"{HP}p"):
                pe.set("paraPrIDRef", pp)

    def set_page_number(self, on: bool):
        """Footer page number. Default OFF (avoids number clashes when documents are combined). When ON, '- N -' at bottom center."""
        for sec in self.doc.sections:
            fp = sec.paragraphs[0].element
            for ctrl in list(fp.iter(f"{HP}ctrl")):
                if ctrl.find(f"{HP}pageNum") is not None:
                    ctrl.getparent().remove(ctrl)
        if on:
            first = self.doc.sections[-1].paragraphs[0].element
            run = first.find(f"{HP}run")
            ctrl = ET.Element(f"{HP}ctrl")
            ET.SubElement(ctrl, f"{HP}pageNum", pos="BOTTOM_CENTER", formatType="DIGIT", sideChar="-")
            sec_pr = run.find(f"{HP}secPr")
            run.insert(list(run).index(sec_pr) + 1 if sec_pr is not None else 0, ctrl)

    def _cell_line_role(self, line: str) -> str | None:
        """Maps ○ and - lines inside cells to the form's cell bullet styles (only when the profile has them)."""
        st = line.lstrip()
        if st.startswith(M.CELL_BULLET_MARKS) and self.p.get("table_cell_bullet"):
            return "table_cell_bullet"
        if st.startswith("- ") and self.p.get("table_cell_dash"):
            return "table_cell_dash"
        return None

    def _border_fill(self, sides: list[str], fill: str | None = None) -> str:
        """Creates a border definition and checks/forces the state of all 4 sides directly on the element.
        Depending on the library version, active_borders was interpreted differently and lines remained on transparent rows."""
        bid = self.header.ensure_border_fill(border_color=C.BORDER_COLOR, border_width=C.BORDER_WIDTH,
                                             active_borders=sides, fill_color=fill)
        el = self.header.element.find(f".//{HH}borderFill[@id='{bid}']")
        if el is not None:
            for side in ("left", "right", "top", "bottom"):
                b = el.find(f"{HH}{side}Border")
                if b is not None:
                    b.set("type", "SOLID" if side in sides else "NONE")
        return str(bid)

    def _transparent_row(self, t, ri: int, ncol: int, text: str, role: str, align: str):
        """Transparent merged row inside a table (unit, source). Kept inside the table so it moves with the table during manual editing."""
        no_border = self._border_fill([])
        u = self.refs(role)
        t.set_cell_text(ri, 0, text)
        for pe in t.cell(ri, 0).element.iter(f"{HP}p"):
            pe.set("paraPrIDRef", self._aligned_pp(str(u["para_pr_id_ref"]), align))
            pe.set("styleIDRef", str(u["style_id_ref"]))
            for run in pe.iter(f"{HP}run"):
                run.set("charPrIDRef", str(u["char_pr_id_ref"]))
        for ci in range(ncol):
            t.cell(ri, ci).element.set("borderFillIDRef", str(no_border))
            t.cell(ri, ci).set_size(height=C.ROW_BASE_H)
        if ncol > 1:
            t.merge_cells(ri, 0, ri, ncol - 1)

    def _cell_font(self) -> M.CellFont:
        """Line styles of table cells (for column widths and row line counts)"""
        bullet = self._line_style("table_cell_bullet") if self.p.get("table_cell_bullet") else None
        dash = self._line_style("table_cell_dash") if self.p.get("table_cell_dash") else None
        return M.CellFont(C.SPACE_EM_HWPX, (self._line_style("table_cell"), self._line_style("table_cell_left")),
                          bullet, dash)

    def _line_style(self, role: str) -> M.LineStyle:
        """Font size, width ratio, letter spacing, and in-cell line lead of a role style"""
        r = self.refs(role)
        cp = self.header.element.find(f".//{HH}charPr[@id='{r['char_pr_id_ref']}']")
        ratio, spacing = cp.find(f"{HH}ratio"), cp.find(f"{HH}spacing")
        size = int(cp.get("height"))
        return M.LineStyle(size, int(ratio.get("hangul")) if ratio is not None else 100,
                           int(spacing.get("hangul")) if spacing is not None else 0,
                           self._cell_lead(str(r["para_pr_id_ref"]), size))

    def _cell_lead(self, pp_id: str, size: int) -> float:
        """Left and right margins and bullet width of a paragraph inside a cell (HWPUNIT). Margins use the new Hangul value (hp:case), or half the legacy value (hp:default) when it is missing"""
        pp = self.header.element.find(f".//{HH}paraPr[@id='{pp_id}']")
        case = pp.find(f".//{HP}case/{HH}margin")
        margin, scale = (case, 1) if case is not None else (pp.find(f".//{HP}default/{HH}margin"), 0.5)
        side = sum(int(margin.find(f"{HC}{k}").get("value")) * scale for k in ("left", "right")) if margin is not None else 0
        head = pp.find(f"{HH}heading")
        if head is None or head.get("type") != "BULLET":
            return side
        b = self.header.element.find(f".//{HH}bullet[@id='{head.get('idRef')}']")
        ph = b.find(f"{HH}paraHead") if b is not None else None
        if ph is None:
            return side
        offset = int(ph.get("textOffset", "0"))
        offset_pct = offset if ph.get("textOffsetType", "PERCENT") == "PERCENT" else offset * 100 / size
        return side + M.bullet_head_hu(b.get("char", "-"), size, offset_pct, int(ph.get("widthAdjust", "0")))

    def attach_caption(self, holder, kind: str, text: str, side: str, width: int):
        """Attached caption object (Hangul caption feature). The number is an automatic number field and restarts at each chapter."""
        r = self.refs("table_title" if kind == "TABLE" else "fig_title")
        cap = holder.set_caption("", side=side, width=width, char_pr_id_ref=r["char_pr_id_ref"])
        cp = cap.paragraphs[0]
        cp.element.set("paraPrIDRef", str(r["para_pr_id_ref"]))
        cp.element.set("styleIDRef", str(r["style_id_ref"]))
        for run in [c for c in cp.element if c.tag == f"{HP}run"]:
            cp.element.remove(run)
        open_b, close_b = C.CAPTION_MARKS[kind]
        prefix = self.p.get("caption_prefix", "").format(c=max(self.numbering.n["chapter"], 1))
        run = cp.add_run(open_b + prefix, char_pr_id_ref=r["char_pr_id_ref"])
        # number stored in the field. Hangul renumbers on open, and renderers that draw the stored value also show the right number
        self.caption_counts[kind] += 1
        an = ET.SubElement(ET.SubElement(run.element, f"{HP}ctrl"), f"{HP}autoNum",
                           num=str(self.caption_counts[kind]), numType=kind)
        ET.SubElement(an, f"{HP}autoNumFormat", type="DIGIT", userChar="", prefixChar="", suffixChar="", supscript="0")
        cp.add_run(close_b + text, char_pr_id_ref=r["char_pr_id_ref"])

    # ── Heading levels ─────────────────────────────────────────────────────
    def heading(self, level: int, text: str):
        text = M.NUM_PREFIX_RE.sub("", text).strip()
        role = ("chapter", "section", "subsection", "ganada")[level - 1]
        if self.numbering.advance(level):
            self.pending_break = True
        label = M.heading_label(self.p, self.numbering.n, level, text)
        manual = self.p["numbering"] == "manual"
        p = self.para(role, label, no_heading=manual and level in (2, 3))
        if level <= 3:
            self.headings.append((level, label))
        if level == 1 and self.p.get("caption_prefix"):   # restart from <표 N-1> in each chapter
            p.add_new_num(kind="TABLE", number=1)
            p.add_new_num(kind="PICTURE", number=1)
            self.caption_counts = {"TABLE": 0, "PICTURE": 0}

    # ── Tables ─────────────────────────────────────────────────────────────
    def table(self, e: M.Element):
        if len(e.data["rows"]) > C.LONG_TABLE_ROWS and self.long_table_mode == "split" and not e.data.get("split_done"):
            for sub in M.split_long_table(e):   # physical split: reattach the header row to each chunk
                self.table(sub)
            return
        plan = M.table_plan(e, self.merge_mode)
        rows, hdr, aligns = plan["rows"], plan["hdr"], plan["aligns"]
        nrow, ncol = len(rows), len(rows[0])
        font = self._cell_font()
        widths = (M.fixed_col_widths(e.data.get("colwidth"), ncol, self.table_max_w, e.text)
                  or M.calc_col_widths(rows, self.table_max_w, font))
        table_w = sum(widths)
        self.gap()
        r = self._centered_refs("table_pos")
        unit = e.data.get("unit")
        sources = e.data.get("sources", [])
        head = 1 if unit else 0   # unit row: transparent merged cell above the header (right-aligned at the table's right edge)
        t = self.doc.add_table(nrow + head + len(sources), ncol, width=table_w, **r, **self._take_break())
        if e.text:
            self.attach_caption(t, "TABLE", e.text, "TOP", table_w)
        t.set_column_widths(widths)
        cell_ref = self.refs("table_cell")
        left_ref = self.refs("table_cell_left")
        left_pp = str(left_ref["para_pr_id_ref"])
        if self._pp_align(left_pp) not in ("LEFT", "JUSTIFY"):   # forms without a left-aligned style derive a left-aligned version of the table content style
            left_pp = self._aligned_pp(left_pp, "LEFT")
        if unit:
            self._transparent_row(t, 0, ncol, unit, "unit", "RIGHT")
        for k, src in enumerate(sources):   # source row: transparent merged cell below the table, left-aligned
            self._transparent_row(t, head + nrow + k, ncol, src, "source", "LEFT")
        total_h = 0
        line_counts = M.row_line_counts(rows, widths, font, plan["vspans"], hdr)
        for ri, row in enumerate(rows):
            row_h = M.row_height(line_counts[ri])
            total_h += row_h
            for ci, val in enumerate(row):
                lines_txt = val.split("\n")
                bullet_roles = [self._cell_line_role(ln) for ln in lines_txt]
                if any(bullet_roles):
                    val = "\n".join(M.CELL_MARK_RE.sub("", ln) if br else ln
                                    for ln, br in zip(lines_txt, bullet_roles))
                t.set_cell_text(ri + head, ci, "" if val.strip() in ("^", "<") else val, split_paragraphs=True)
                cell = t.cell(ri + head, ci)
                cell.set_size(height=row_h)
                is_head = ri < hdr
                is_left = aligns[ci] == "LEFT" and not is_head
                ref = left_ref if is_left else cell_ref
                pp = left_pp if is_left else str(ref["para_pr_id_ref"])
                if not is_head and aligns[ci] == "RIGHT":
                    pp = self._aligned_pp(pp, "RIGHT")
                cp = self._run_style(str(cell_ref["char_pr_id_ref"]), bold=True) if is_head else str(ref["char_pr_id_ref"])
                for li, pe in enumerate(cell.element.iter(f"{HP}p")):
                    br = bullet_roles[li] if li < len(bullet_roles) and not is_head else None
                    bref = self.refs(br) if br else None
                    pe.set("paraPrIDRef", str(bref["para_pr_id_ref"]) if bref else pp)
                    pe.set("styleIDRef", str(bref["style_id_ref"] if bref else ref["style_id_ref"]))
                    line_cp = str(bref["char_pr_id_ref"]) if bref else cp
                    for run in pe.iter(f"{HP}run"):
                        run.set("charPrIDRef", line_cp)
                    self._inline_runs(pe, line_cp)
                cell.element.set("hasMargin", "1")   # needed for cellMargin values to apply
                if is_head:
                    cell.element.set("header", "1")
        sz = t.element.find(f"{HP}sz")
        if sz is not None:   # if the table height exceeds the sum of row heights, renderers stretch the last row
            sz.set("height", str(total_h + C.ROW_BASE_H * (head + len(sources))))
        pos = t.element.find(f"{HP}pos")
        if pos is not None:   # a table treated as a character follows paragraph alignment, so pos alignment is also centered to remove conflicting interpretations
            pos.set("horzAlign", "CENTER")
        for c, r0, r1 in plan["vspans"]:   # vertical merge of consecutive identical labels. Negative values are header rows
            a, b = head + hdr + r0, head + hdr + r1
            for rr in range(a + 1, b + 1):
                t.set_cell_text(rr, c, "")
            t.merge_cells(a, c, b, c)
        for ri, c0, c1 in plan["skipped"]:
            print(msg("warn_hmerge_overlap", row=ri, c0=c0, c1=c1))
        for ri, c0, c1 in plan["hspans"]:   # horizontal merge by '<' directive
            for cc in range(c0 + 1, c1 + 1):
                t.set_cell_text(head + ri, cc, "")
            t.merge_cells(head + ri, c0, head + ri, c1)
        # set borders from the actual span after merging (if a merged cell reaches the table edge, that outer border stays open)
        for tc in t.element.iter(f"{HP}tc"):
            addr, span = tc.find(f"{HP}cellAddr"), tc.find(f"{HP}cellSpan")
            if addr is None or span is None:
                continue
            c0, r0 = int(addr.get("colAddr")), int(addr.get("rowAddr"))
            c1 = c0 + int(span.get("colSpan")) - 1
            if r0 < head or r0 >= head + nrow:
                continue   # unit and source rows are transparent
            sides = cell_sides(c0, c1, ncol)
            tc.set("borderFillIDRef", self._border_fill(sides, C.HEADER_FILL if r0 < head + hdr else None))
        if nrow > C.LONG_TABLE_ROWS and not e.data.get("split_done"):   # long table: Hangul splits it by row at page boundaries and repeats the header row
            t.element.set("repeatHeader", "1")
            t.element.set("pageBreak", "CELL")
            if head:   # Hangul repeats only title-cell rows that run contiguously from the top of the table, so the unit row is marked as title cells too
                for tc in t.element.iter(f"{HP}tc"):
                    addr = tc.find(f"{HP}cellAddr")
                    if addr is not None and addr.get("rowAddr") == "0":
                        tc.set("header", "1")
            if pos is not None:
                pos.set("treatAsChar", "0")
                pos.set("flowWithText", "1")
        t.mark_dirty()

    # ── Figures ────────────────────────────────────────────────────────────
    def image(self, e: M.Element):
        loaded = M.load_image(e)
        if loaded is None:
            return
        data, fmt, (w_mm, h_mm) = loaded
        self.gap()
        r = self._centered_refs("fig_pos")
        w_hu, h_hu = round(w_mm * 7200 / 25.4), round(h_mm * 7200 / 25.4)
        sources = e.data.get("sources", [])
        if not C.FIGURE_IN_TABLE:
            pic = self.doc.add_picture(data, fmt, width_mm=w_mm, height_mm=h_mm, **r, **self._take_break())
            if e.text:
                self.attach_caption(pic, "PICTURE", e.text, "BOTTOM", w_hu)
            for src in sources:
                self.para("source", src)
            return
        # put the figure in a transparent one-column table and set the table's numbering type to figure. The inner picture is excluded from numbering
        table_w = w_hu + 2 * C.CELL_MARGIN_LR   # add the left and right cell margins so the picture fits the cell's inner width
        t = self.doc.add_table(1 + len(sources), 1, width=table_w, **r, **self._take_break())
        item = self.doc.media.add_image(data, fmt)
        item_id = getattr(item, "item_id", item)   # object or string depending on the library version
        cell = t.cell(0, 0)
        pic = cell.paragraphs[0].add_picture(str(item_id), width=w_hu, height=h_hu, char_pr_id_ref=r["char_pr_id_ref"])
        img = next((el for el in pic.element.iter() if el.tag.endswith("}img")), None)
        if img is None or not img.get("binaryItemIDRef"):
            sys.exit(msg("err_image_ref", path=e.data["path"]))
        pic.element.set("numberingType", "NONE")
        for pe in cell.element.iter(f"{HP}p"):
            pe.set("paraPrIDRef", str(r["para_pr_id_ref"]))
            pe.set("styleIDRef", str(r["style_id_ref"]))
        cell.element.set("borderFillIDRef", self._border_fill([]))
        cell.set_size(height=h_hu + 2 * C.ROW_LINE_H)
        for k, src in enumerate(sources):
            self._transparent_row(t, 1 + k, 1, src, "source", "LEFT")
        t.element.set("numberingType", "PICTURE")
        pos = t.element.find(f"{HP}pos")
        if pos is not None:
            pos.set("horzAlign", "CENTER")
        sz = t.element.find(f"{HP}sz")
        if sz is not None:
            sz.set("height", str(h_hu + 2 * C.ROW_LINE_H + C.ROW_BASE_H * len(sources)))
        if e.text:
            self.attach_caption(t, "PICTURE", e.text, "BOTTOM", table_w)
        t.mark_dirty()

    # ── Run ────────────────────────────────────────────────────────────────
    def build(self, elems: list[M.Element], footnotes: dict, out: str):
        for e in M.attach_block_notes(elems):
            if e.kind == "heading":
                self.heading(e.level, e.text)
                self.last_para = None   # cut the link so a source line after a heading does not become a footnote of the previous section's paragraph
            elif e.kind in ("square", "circle", "dash", "dot", "note"):
                self.last_para = self.para(e.kind, e.text, footnotes)
                self.last_cp = str(self.refs(e.kind)["char_pr_id_ref"])
            elif e.kind == "unit":
                self.para("unit", e.text)
            elif e.kind == "source":   # a source line not attached to a table or figure becomes a footnote of the previous paragraph
                if self.last_para is not None:
                    self._add_footnote(self.last_para, e.text, self.last_cp)
                else:
                    self.para("note", e.text, footnotes)
            elif e.kind == "table":
                self.table(e)
            elif e.kind == "image":
                self.image(e)
            elif e.kind == "pagebreak":
                self.pending_break = True
        if self.toc or self.cover:
            self._front_matter(self.cover)
        self.set_page_number(self.page_number)
        # create the page header after the margins are final. python-hwpx computes the header area width only once, from the margins at creation time
        self.set_header(self.header_spec)
        report = self.doc.validate()
        issues = getattr(report, "issues", [])
        if issues:
            print(msg("warn_schema", n=len(issues)))
            for it in list(issues)[:5]:
                print("   ", it)
        save_hwpx(self.doc, out)
        self.doc.close()


def save_hwpx(doc, path: str):
    """The library saves by moving a temporary file (mode 0600), so restore normal file permissions after saving"""
    doc.save_to_path(os.path.abspath(path))
    umask = os.umask(0)
    os.umask(umask)
    os.chmod(path, 0o666 & ~umask)


def cell_sides(c0: int, c1: int, ncol: int) -> list[str]:
    """Sides of the 4 cell sides to draw. Sides touching the table's left or right edge stay open."""
    sides = ["top", "bottom", "left", "right"]
    if C.EDGE_OPEN_SIDES and c0 == 0:
        sides.remove("left")
    if C.EDGE_OPEN_SIDES and c1 == ncol - 1:
        sides.remove("right")
    return sides


def parse_header_spec(spec: str) -> tuple[str, str]:
    parts = spec.split(";")
    align = next((kv.split("=", 1)[1].strip().upper() for kv in parts[1:] if kv.strip().lower().startswith("align=")), "RIGHT")
    return parts[0].strip(), align


def parse_cover(spec: str | None) -> dict | None:
    return dict(kv.split("=", 1) for kv in spec.split(";") if "=" in kv) if spec else None


def repair_manifest(path: str) -> int:
    """Check content.hpf opf:item entries against header.xml binItem entries and BinData files and register the missing ones.
    python-hwpx 6.5.0 registers only the first of several images in the manifest when a document has a TOC or cover,
    and Hangul then cannot open the other pictures. The file is left untouched when everything matches."""
    media = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif",
             "bmp": "image/bmp", "tif": "image/tiff", "tiff": "image/tiff", "svg": "image/svg+xml"}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}
    hpf = data["Contents/content.hpf"].decode("utf-8")
    header = data.get("Contents/header.xml", b"").decode("utf-8")
    have = set(re.findall(r'<opf:item[^>]*href="BinData/([^"]+)"', hpf))
    wanted: list[str] = []
    for f in re.findall(r'<hh:binItem[^>]*BinData="([^"]+)"', header):
        if f not in wanted:
            wanted.append(f)
    for n in names:
        if n.startswith("BinData/") and n.split("/", 1)[1] not in wanted:
            wanted.append(n.split("/", 1)[1])
    missing = [f for f in wanted if f not in have and f"BinData/{f}" in names]
    if not missing:
        return 0
    items = "".join(
        f'<opf:item id="{os.path.splitext(f)[0]}" href="BinData/{f}" '
        f'media-type="{media.get(os.path.splitext(f)[1].lstrip(".").lower(), "application/octet-stream")}" '
        f'isEmbeded="1"/>' for f in missing)
    data["Contents/content.hpf"] = hpf.replace("</opf:manifest>", items + "</opf:manifest>", 1).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(zipfile.ZipInfo("mimetype"), data["mimetype"], compress_type=zipfile.ZIP_STORED)
        for n in names:
            if n != "mimetype":
                z.writestr(n, data[n])
    return len(missing)


def build_hwpx(a, elems, footnotes, out: str):
    """HWPX path of the build command. With TOC and page numbers both on, finds heading pages by rendering and typesets twice."""
    workdir = tempfile.mkdtemp(prefix="blockwriter_")   # holds the built-in form skeleton; deleted when typesetting ends
    try:
        _build_hwpx(a, elems, footnotes, out, workdir)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _build_hwpx(a, elems, footnotes, out: str, workdir: str):
    import render
    profile = load_profile(a.profile)
    skeleton = a.skeleton or (builtin_skeleton(a.profile, workdir) if a.profile in FORMS else None)
    if not skeleton or not os.path.exists(skeleton):
        sys.exit(msg("err_no_skeleton", path=skeleton))

    def make(numbers=None):
        b = Builder(skeleton, profile, page_break=a.page_break)
        b.numbered_square = a.numbered_square
        b.toc, b.toc_depth = a.toc, a.toc_depth
        b.page_number = a.page_number
        b.cover = parse_cover(a.cover)
        b.header_spec = a.header
        b.merge_mode = a.merge
        b.long_table_mode = a.long_table
        b.toc_numbers = numbers or {}
        b.build(elems, footnotes, out)
        return b
    b = make()
    fixed = repair_manifest(out)
    if fixed:
        print(msg("manifest_fixed", n=fixed))
    has_toc = bool(profile.get("toc_chapter") and profile.get("toc_section"))
    if a.toc and a.page_number and b.headings and has_toc:   # two-pass typesetting: find heading page positions by rendering and write them into the TOC (approximate)
        def remake(numbers):
            make(numbers)
            repair_manifest(out)
        render.fill_toc_numbers(remake, out, [t for _, t in M.toc_entries(b.headings, a.toc_depth)], a.rhwp,
                                M.toc_first_lines(elems, a.toc_depth))   # rhwp does not apply the keep-with-next setting that prevents stranded headings


# ── Skeleton extraction from a user form ────────────────────────────────────────
# candidate style names per role. Built-in form names come first, then short names common in report forms
SKELETON_GUESS = {
    "chapter": ("장 제목", "문서 제목", "장"), "section": ("절 제목", "1.1", "절"), "subsection": ("소절 제목", "1.1.1"),
    "ganada": ("가나다 제목", "가.", "가. 제목"), "square": ("□ 내용", "□"),
    "circle": ("○ 내용", "○"), "dash": ("- 내용", "-"),
    "dot": ("ㆍ 내용", "ㆍ"), "note": ("※ 내용", "※"),
    "table_pos": ("표 위치", "표위치"), "table_cell": ("표 내용", "표내용"),
    "table_cell_left": ("표 내용 왼쪽", "표 내용", "표내용"), "table_title": ("표 제목",),
    "unit": ("단위",), "source": ("출처",),
    "fig_pos": ("그림 위치", "그림위치"), "fig_title": ("그림 제목",), "body": ("바탕글",),
}


def skeleton_from_template(src_path: str, out_path: str, section: int | None):
    """Creates an empty form that keeps only header.xml and the body section page settings of a user form, plus a draft profile."""
    src = zipfile.ZipFile(src_path)
    secs = sorted(n for n in src.namelist() if re.match(r"Contents/section\d+\.xml", n))
    sec_name = f"Contents/section{section}.xml" if section is not None else secs[-1]
    s = src.read(sec_name).decode("utf-8")
    first = s[: s.find("</hp:p>") + 7]
    first = re.sub(r"<hp:t\b[^>]*>.*?</hp:t>", "<hp:t/>", first, flags=re.S)
    first = re.sub(r"<hp:t\b[^>]*/>", "<hp:t/>", first)
    first = re.sub(r'(<hp:p\b[^>]*?)paraPrIDRef="\d+"', r'\1paraPrIDRef="0"', first, count=1)
    first = re.sub(r'(<hp:p\b[^>]*?)pageBreak="1"', r'\1pageBreak="0"', first, count=1)
    hpf = src.read("Contents/content.hpf").decode("utf-8")
    hpf = re.sub(r'<opf:item id="section[1-9]\d*"[^>]*/>', "", hpf)
    hpf = re.sub(r'<opf:itemref idref="section[1-9]\d*"[^>]*/>', "", hpf)
    hpf = re.sub(r'<opf:item [^>]*href="BinData/[^"]*"[^>]*/>', "", hpf)
    hpf = re.sub(r'(<opf:meta name="(creator|lastsaveby|date|CreatedDate|ModifiedDate)"[^>]*>)[^<]*(</opf:meta>)',
                 r"\1\3", hpf)   # remove author and date metadata
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for it in src.infolist():
            n = it.filename
            if n.startswith("BinData/") or re.match(r"Contents/section[1-9]", n) or n == "Preview/PrvImage.png":
                continue
            data = src.read(n)
            if n == "Contents/section0.xml":
                data = (first + "</hs:sec>").encode("utf-8")
            elif n == "Preview/PrvText.txt":
                data = b""   # remove the original preview text
            elif n == "Contents/content.hpf":
                data = hpf.encode("utf-8")
            elif n == "Contents/header.xml":
                data = re.sub(rb'secCnt="\d+"', b'secCnt="1"', data)
            if n == "mimetype":
                z.writestr(zipfile.ZipInfo("mimetype"), data, compress_type=zipfile.ZIP_STORED)
            else:
                z.writestr(it, data)
    from hwpx import HwpxDocument
    doc = HwpxDocument.open(os.path.abspath(out_path))
    names = [st.name for st in doc.styles.values()]
    bullets = {bid: b.char for bid, b in doc.styles.bullets.items()} if hasattr(doc.styles, "bullets") else {}
    doc.close()
    profile = {"numbering": "manual", "chapter_format": C.PROFILE_DEFAULTS["chapter_format"]}
    for role, cands in SKELETON_GUESS.items():
        profile[role] = next((c for c in cands if c in names), None)
    prof_path = os.path.splitext(out_path)[0] + ".profile.json"
    Path(prof_path).write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(msg("skeleton_ok", out=out_path, size=os.path.getsize(out_path), sec=sec_name))
    print(msg("skeleton_styles", names=names))
    print(msg("skeleton_bullets", bullets=bullets))
    print(msg("skeleton_profile", path=prof_path))


def fill(src: str, mapping: str, out: str | None):
    from hwpx import HwpxDocument
    spec = json.loads(Path(mapping).read_text(encoding="utf-8"))
    doc = HwpxDocument.open(os.path.abspath(src))
    total = 0
    for old, new in spec.get("replace", {}).items():
        total += doc.text.replace(old, new) or 0
    if spec.get("cells"):   # fill table cells by "label > right" paths
        res = doc.tables.fill_by_path(spec["cells"])
        print(msg("fill_cells", ok=res["applied_count"], fail=res["failed_count"]))
        for f in res.get("failed", []):   # example failure reason: the label appears more than once in the document (ambiguous label)
            print(msg("fill_cell_failed", path=f.get("path"), reason=f.get("reason")))
    save_hwpx(doc, out or src)
    print(msg("fill_ok", n=total, out=out or src))


def check(path: str, expect: str) -> int:
    """Schema validation, image manifest consistency, rhwp expectation check. Returns the issue count, including failed expectations."""
    import render
    from hwpx import HwpxDocument
    doc = HwpxDocument.open(os.path.abspath(path))
    report = doc.validate()
    issues = list(getattr(report, "issues", []))
    with zipfile.ZipFile(path) as z:
        hpf = z.read("Contents/content.hpf").decode("utf-8")
        have = set(re.findall(r'<opf:item[^>]*href="BinData/([^"]+)"', hpf))
        binitems = set(re.findall(r'<hh:binItem[^>]*BinData="([^"]+)"', z.read("Contents/header.xml").decode("utf-8")))
        files = {n.split("/", 1)[1] for n in z.namelist() if n.startswith("BinData/")}
        sec = "".join(z.read(n).decode("utf-8") for n in z.namelist() if n.startswith("Contents/section"))
    refs = set(re.findall(r'binaryItemIDRef="([^"]+)"', sec))
    stems = {os.path.splitext(f)[0] for f in files}
    if files - have:
        issues.append(msg("check_manifest_missing", items=sorted(files - have)))
    if binitems - files:
        issues.append(msg("check_bin_missing", items=sorted(binitems - files)))
    if refs - stems:
        issues.append(msg("check_ref_missing", items=sorted(refs - stems)))
    print(msg("check_images", files=len(files), items=len(binitems), manifest=len(have), refs=len(refs)))
    print(msg("check_schema", n=len(issues)))
    for it in issues[:10]:
        print("   ", it)
    doc.close()
    verified = render.rhwp_verify(path, expect)
    return len(issues) + (verified is False)
