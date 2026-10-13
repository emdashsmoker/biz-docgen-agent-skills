"""HWPX 조판기: 원고 요소를 python-hwpx로 스켈레톤 위에 배치한다.
스켈레톤은 내장 양식(form.py)에서 생성하거나 유저 양식에서 추출한다."""
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
# 인라인 서식 종류별 글자 모양 변경값 (_run_style 인자)
INLINE_STYLE = {"bold": {"bold": True}, "italic": {"italic": True}, "sup": {"script": "sup"}, "sub": {"script": "sub"}}
MANUAL_SYMBOLS = {"square": "□ ", "circle": "○ ", "dash": "- ", "dot": "ㆍ ", "note": "※ "}
ROLE_KEYS = ("body", "chapter", "section", "subsection", "ganada", "square", "circle", "dash", "dot", "note",
             "table_pos", "table_cell", "table_cell_left", "table_title", "unit", "source", "fig_pos", "fig_title",
             "toc_chapter", "toc_section", "table_cell_bullet", "table_cell_dash")
FORMAT_FLAGS = ("bold", "italic", "supscript", "subscript")


def load_profile(spec: str) -> dict:
    """내장 양식 이름이면 form.py의 스타일 이름과 번호 체계로, JSON 경로면 그 내용으로 프로파일을 만든다."""
    if spec in FORMS:
        names = {st.role: st.name for st in FORMS[spec].styles}
        prof = dict(C.PROFILE_FORMATS[spec])
        for role in ROLE_KEYS:
            if role in names:
                prof[role] = names[role]
        prof.setdefault("table_cell_left", names["table_cell"])   # 왼쪽 정렬 표 내용 스타일이 없는 양식
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
        self.toc_numbers: dict[int, int] = {}   # 목차 항목 순번 → 쪽번호
        self.header = self.doc.parts.headers[0]
        self.body_w = self._body_width()
        self.table_max_w = self.body_w - C.TABLE_INDENT_MARGIN
        self._pp_cache: dict = {}
        self._cp_cache: dict = {}
        self.pending_break = False
        self.manual_symbol = self._manual_symbols()
        self._warned: set[str] = set()
        self.last_para = None
        self.last_cp = None   # 직전 문단의 기본 글자 모양 (출처 줄을 옮긴 각주의 참조 run에 사용)
        self.caption_counts = {"TABLE": 0, "PICTURE": 0}   # 캡션 번호 필드에 저장할 번호
        # 조판 옵션 (cmd_build에서 지정)
        self.numbered_square = False
        self.toc = False
        self.toc_depth = 2
        self.cover = None
        self.page_number = False
        self.header_spec = None
        self.merge_mode = "auto"
        self.long_table_mode = "engine"

    def _manual_symbols(self) -> dict[str, str]:
        """스타일의 heading이 BULLET이면 한/글이 기호를 그리고, 아니면 본문에 기호를 넣는다."""
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

    # ── 기본 요소 ───────────────────────────────────────────────────────
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
        """기준 글자 모양을 복제하고 굵게·기울임·첨자만 더한다.
        기존 글자 모양을 재사용할 때는 서식 표시 외 모든 속성이 기준과 같은지 확인한다.
        일부 속성만 비교하면 자간이나 장평이 다른 글자 모양이 재사용된다."""
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
        """스타일, 문단 모양, 글자 모양 참조 3종을 함께 지정해야 서식이 붙는다."""
        r = self.refs(role)
        if role == "square" and self.numbered_square and M.NUMBERED_SQUARE_RE.match(text):   # 1. 2. 3. 숫자 헤더
            r["para_pr_id_ref"] = self._numbered_pp(str(r["para_pr_id_ref"]), str(r["char_pr_id_ref"]), text)
        elif no_heading:   # 번호를 본문에 기입하므로 스타일의 자동 개요 번호를 끈다
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
        """각주 참조를 문단 기본 글자 모양의 run에 두고 각주 본문에도 본문과 같은 인라인 서식을 적용한다.
        라이브러리는 참조를 문단의 마지막 run(첨자, 굵게 등)에 두고 각주 본문을 run 하나의 글자 모양으로만 만든다"""
        note = p.add_footnote("", run_attributes={"charPrIDRef": str(body_cp)})
        run = note.element.find(f".//{HP}subList/{HP}p/{HP}run")   # 각주 번호가 든 run
        base_cp = run.get("charPrIDRef")
        empty_t = run.find(f"{HP}t")
        if empty_t is not None:
            run.remove(empty_t)
        for kind, seg in M.inline_segments(text):
            if kind == "footnote":   # 각주 안의 각주 참조는 쓰지 않음
                continue
            cp = self._run_style(base_cp, **INLINE_STYLE[kind]) if kind in INLINE_STYLE else base_cp
            new_run = ET.SubElement(run.getparent(), f"{HP}run", charPrIDRef=str(cp))
            ET.SubElement(new_run, f"{HP}t").text = seg

    def _inline_runs(self, pe, base_cp: str):
        """셀 문단의 인라인 서식 표기(굵게, 기울임, 첨자)를 글자 모양이 다른 run으로 나눈다.
        셀 안의 각주 참조는 지원하지 않아 표기 그대로 둔다"""
        runs = pe.findall(f"{HP}run")
        if not runs:
            return
        text = "".join(t.text or "" for r in runs for t in r.findall(f"{HP}t"))
        segs = M.inline_segments(text)
        if all(kind == "plain" for kind, _ in segs):
            return
        idx = list(pe).index(runs[0])   # 원래 run이 있던 위치에 다시 배치 (문단 안 다른 요소보다 앞)
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
        """'---' 쪽 나눔을 다음 문단 또는 표·그림을 담은 문단에 적용"""
        attrs = dict(attrs or {})
        if self.pending_break:
            attrs["pageBreak"] = "1"
            self.pending_break = False
        return attrs

    def _centered_refs(self, role: str) -> dict:
        """표·그림 문단은 스타일 정렬과 무관하게 가운데. 유저 양식의 표 위치 스타일이 왼쪽이어도 표가 왼쪽에 붙지 않음."""
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
        """숫자 헤더 문단 모양. 글머리를 끄고 번호 폭만큼 내어써서 둘째 줄을 번호 뒤 글자에 맞춘다.
        양쪽 정렬은 접힌 첫 줄의 빈칸을 늘려 번호 뒤 글자 위치를 옮기므로 왼쪽 정렬"""
        height = int(self.header.element.find(f".//{HH}charPr[@id='{cp}']").get("height"))
        hang = round(height * M.number_prefix_em(text, C.SPACE_EM_HWPX))
        key = (base_pp, "NUMBERED", hang)
        if key not in self._pp_cache:
            # 한/글 내어쓰기는 첫 줄을 왼쪽 여백에 두고 둘째 줄부터 내어쓰기 폭만큼 들여 시작 (음수 intent)
            pp = self.header.ensure_paragraph_format(base_para_pr_id=self._no_bullet_pp(base_pp), alignment="LEFT",
                                                     margins={"intent": -hang})
            # 구형 한/글용 저장값(hp:default)은 새 값의 2배로 기록 (양식 생성 규칙과 동일)
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
        """표지와 목차를 앞부분 구역에 두고 본문을 새 구역으로 옮긴다. 본문 쪽번호는 1부터 시작."""
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
            s0.element.append(p.element)   # add_paragraph는 마지막 구역에 붙이므로 앞부분 구역으로 이동
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
                        unit = 700 if lv == 1 else 600   # 장 14pt, 절 12pt 글자 1자 폭 추정 (HWPUNIT)
                        width = max(C.TOC_TAB_POS - left - M.weighted_len(text) * unit - len(str(num)) * unit, 1000)
                        ET.SubElement(tnode, f"{HP}tab", width=str(width), leader="3", type="2").tail = str(num)
        for sec in (s0, s1):
            sec.mark_dirty() if hasattr(sec, "mark_dirty") else None

    def set_header(self, spec: str | None):
        """머리말 (기본 OFF). "텍스트;align=LEFT|CENTER|RIGHT". 본문 구역에만 적용.
        python-hwpx가 머리말을 secPr 안과 ctrl 두 곳에 쓰므로 secPr 안 사본을 제거하고 ctrl 사본의 문단 정렬을 지정."""
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
        """꼬리말 쪽번호. 기본 OFF (취합 시 번호 충돌 방지). ON이면 가운데 아래 '- N -'."""
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
        """셀 안의 ○, - 줄에 양식의 셀 글머리 스타일을 대응 (프로파일에 있을 때만)."""
        st = line.lstrip()
        if st.startswith(M.CELL_BULLET_MARKS) and self.p.get("table_cell_bullet"):
            return "table_cell_bullet"
        if st.startswith("- ") and self.p.get("table_cell_dash"):
            return "table_cell_dash"
        return None

    def _border_fill(self, sides: list[str], fill: str | None = None) -> str:
        """테두리 정의를 만들고 4변 상태를 요소에서 직접 확인·강제한다.
        라이브러리 버전에 따라 active_borders 해석이 달라 투명 행에 선이 남는 사례가 있었다."""
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
        """표 안의 투명 병합 행 (단위, 출처). 손으로 편집할 때 표와 함께 이동하도록 표 내부에 둔다."""
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
        """표 셀 줄 스타일 (열 폭과 행 줄 수 산정용)"""
        bullet = self._line_style("table_cell_bullet") if self.p.get("table_cell_bullet") else None
        dash = self._line_style("table_cell_dash") if self.p.get("table_cell_dash") else None
        return M.CellFont(C.SPACE_EM_HWPX, (self._line_style("table_cell"), self._line_style("table_cell_left")),
                          bullet, dash)

    def _line_style(self, role: str) -> M.LineStyle:
        """역할 스타일의 글자 크기, 장평, 자간과 셀 안 줄 앞 폭"""
        r = self.refs(role)
        cp = self.header.element.find(f".//{HH}charPr[@id='{r['char_pr_id_ref']}']")
        ratio, spacing = cp.find(f"{HH}ratio"), cp.find(f"{HH}spacing")
        size = int(cp.get("height"))
        return M.LineStyle(size, int(ratio.get("hangul")) if ratio is not None else 100,
                           int(spacing.get("hangul")) if spacing is not None else 0,
                           self._cell_lead(str(r["para_pr_id_ref"]), size))

    def _cell_lead(self, pp_id: str, size: int) -> float:
        """셀 안 문단의 좌우 여백과 글머리 폭 (HWPUNIT). 여백은 새 한/글 값(hp:case), 없으면 구형 값(hp:default)의 절반"""
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
        """개체 부착 캡션(한/글 캡션 기능). 번호는 자동 번호 필드이며 장 시작 시 재시작."""
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
        # 필드에 저장하는 번호. 한/글은 열 때 다시 매기며 저장값을 그대로 그리는 렌더러도 올바른 번호를 보이게 함
        self.caption_counts[kind] += 1
        an = ET.SubElement(ET.SubElement(run.element, f"{HP}ctrl"), f"{HP}autoNum",
                           num=str(self.caption_counts[kind]), numType=kind)
        ET.SubElement(an, f"{HP}autoNumFormat", type="DIGIT", userChar="", prefixChar="", suffixChar="", supscript="0")
        cp.add_run(close_b + text, char_pr_id_ref=r["char_pr_id_ref"])

    # ── 헤더 계위 ───────────────────────────────────────────────────────
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
        if level == 1 and self.p.get("caption_prefix"):   # 장별 <표 N-1>부터 재시작
            p.add_new_num(kind="TABLE", number=1)
            p.add_new_num(kind="PICTURE", number=1)
            self.caption_counts = {"TABLE": 0, "PICTURE": 0}

    # ── 표 ──────────────────────────────────────────────────────────────
    def table(self, e: M.Element):
        if len(e.data["rows"]) > C.LONG_TABLE_ROWS and self.long_table_mode == "split" and not e.data.get("split_done"):
            for sub in M.split_long_table(e):   # 물리 분할: 청크마다 제목행 재부착
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
        head = 1 if unit else 0   # 단위 행: 머리글 위 투명 병합 셀 (표 우측 끝 정렬)
        t = self.doc.add_table(nrow + head + len(sources), ncol, width=table_w, **r, **self._take_break())
        if e.text:
            self.attach_caption(t, "TABLE", e.text, "TOP", table_w)
        t.set_column_widths(widths)
        cell_ref = self.refs("table_cell")
        left_ref = self.refs("table_cell_left")
        left_pp = str(left_ref["para_pr_id_ref"])
        if self._pp_align(left_pp) not in ("LEFT", "JUSTIFY"):   # 왼쪽 정렬 스타일이 없는 양식은 표 내용 스타일을 왼쪽으로 파생
            left_pp = self._aligned_pp(left_pp, "LEFT")
        if unit:
            self._transparent_row(t, 0, ncol, unit, "unit", "RIGHT")
        for k, src in enumerate(sources):   # 출처 행: 표 아래 투명 병합 셀, 왼쪽 정렬
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
                cell.element.set("hasMargin", "1")   # cellMargin 값이 적용되려면 필요
                if is_head:
                    cell.element.set("header", "1")
        sz = t.element.find(f"{HP}sz")
        if sz is not None:   # 표 높이가 행 높이 합보다 크면 렌더러가 마지막 행을 늘여 그린다
            sz.set("height", str(total_h + C.ROW_BASE_H * (head + len(sources))))
        pos = t.element.find(f"{HP}pos")
        if pos is not None:   # 글자처럼 취급하는 표는 문단 정렬을 따르므로 pos 정렬도 가운데로 맞춰 해석 충돌 제거
            pos.set("horzAlign", "CENTER")
        for c, r0, r1 in plan["vspans"]:   # 연속 동일 라벨 세로 병합. 음수는 머리글 행
            a, b = head + hdr + r0, head + hdr + r1
            for rr in range(a + 1, b + 1):
                t.set_cell_text(rr, c, "")
            t.merge_cells(a, c, b, c)
        for ri, c0, c1 in plan["skipped"]:
            print(msg("warn_hmerge_overlap", row=ri, c0=c0, c1=c1))
        for ri, c0, c1 in plan["hspans"]:   # '<' 지시 가로 병합
            for cc in range(c0 + 1, c1 + 1):
                t.set_cell_text(head + ri, cc, "")
            t.merge_cells(head + ri, c0, head + ri, c1)
        # 병합 뒤 실제 스팬 기준으로 선을 지정 (병합 셀이 표 끝까지 닿으면 그쪽 바깥선을 비운다)
        for tc in t.element.iter(f"{HP}tc"):
            addr, span = tc.find(f"{HP}cellAddr"), tc.find(f"{HP}cellSpan")
            if addr is None or span is None:
                continue
            c0, r0 = int(addr.get("colAddr")), int(addr.get("rowAddr"))
            c1 = c0 + int(span.get("colSpan")) - 1
            if r0 < head or r0 >= head + nrow:
                continue   # 단위 행과 출처 행은 투명
            sides = cell_sides(c0, c1, ncol)
            tc.set("borderFillIDRef", self._border_fill(sides, C.HEADER_FILL if r0 < head + hdr else None))
        if nrow > C.LONG_TABLE_ROWS and not e.data.get("split_done"):   # 장표: 한/글이 쪽 경계에서 행 단위로 나누고 제목행 반복
            t.element.set("repeatHeader", "1")
            t.element.set("pageBreak", "CELL")
            if head:   # 한/글은 표 맨 위부터 이어진 제목 셀 행만 반복하므로 단위 행도 제목 셀로 지정
                for tc in t.element.iter(f"{HP}tc"):
                    addr = tc.find(f"{HP}cellAddr")
                    if addr is not None and addr.get("rowAddr") == "0":
                        tc.set("header", "1")
            if pos is not None:
                pos.set("treatAsChar", "0")
                pos.set("flowWithText", "1")
        t.mark_dirty()

    # ── 그림 ────────────────────────────────────────────────────────────
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
        # 투명 1열 표에 그림을 넣고 표를 그림 번호 유형으로 지정. 내부 그림은 번호 집계에서 제외
        table_w = w_hu + 2 * C.CELL_MARGIN_LR   # 셀 좌우 여백을 더해야 그림이 셀 안 폭에 들어감
        t = self.doc.add_table(1 + len(sources), 1, width=table_w, **r, **self._take_break())
        item = self.doc.media.add_image(data, fmt)
        item_id = getattr(item, "item_id", item)   # 라이브러리 버전에 따라 객체 또는 문자열
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

    # ── 실행 ────────────────────────────────────────────────────────────
    def build(self, elems: list[M.Element], footnotes: dict, out: str):
        for e in M.attach_block_notes(elems):
            if e.kind == "heading":
                self.heading(e.level, e.text)
                self.last_para = None   # 제목 뒤 출처 줄이 앞 절 문단의 각주로 붙지 않게 연결을 끊음
            elif e.kind in ("square", "circle", "dash", "dot", "note"):
                self.last_para = self.para(e.kind, e.text, footnotes)
                self.last_cp = str(self.refs(e.kind)["char_pr_id_ref"])
            elif e.kind == "unit":
                self.para("unit", e.text)
            elif e.kind == "source":   # 표·그림에 붙지 않은 출처 줄은 직전 문단의 각주로 이동
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
        # 머리말은 여백 확정 뒤에 생성. python-hwpx가 머리말 영역 폭을 생성 시점의 여백으로 한 번만 계산함
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
    """라이브러리는 임시 파일(권한 0600)을 옮겨 저장하므로 저장 뒤 일반 파일과 같은 권한으로 되돌린다"""
    doc.save_to_path(os.path.abspath(path))
    umask = os.umask(0)
    os.umask(umask)
    os.chmod(path, 0o666 & ~umask)


def cell_sides(c0: int, c1: int, ncol: int) -> list[str]:
    """셀 4변 중 선을 그을 변. 표 좌우 끝에 닿는 변은 비운다."""
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
    """content.hpf의 opf:item을 header.xml의 binItem 및 BinData 파일과 대조하고 누락분을 등록한다.
    python-hwpx 6.5.0은 목차나 표지를 넣은 문서에서 이미지 여러 개 중 첫 항목만 매니페스트에 등록하며,
    이 경우 한/글이 나머지 그림을 열지 못한다. 정합하면 파일을 건드리지 않는다."""
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
    """build 명령의 HWPX 경로. 목차와 쪽번호를 함께 켜면 렌더링으로 제목 쪽을 찾아 2회 조판한다."""
    workdir = tempfile.mkdtemp(prefix="blockwriter_")   # 내장 양식 스켈레톤 보관. 조판이 끝나면 삭제
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
    if a.toc and a.page_number and b.headings and has_toc:   # 2회 조판: 렌더링으로 제목의 쪽 위치를 찾아 목차에 기입 (근사값)
        def remake(numbers):
            make(numbers)
            repair_manifest(out)
        render.fill_toc_numbers(remake, out, [t for _, t in M.toc_entries(b.headings, a.toc_depth)], a.rhwp,
                                M.toc_first_lines(elems, a.toc_depth))   # rhwp는 제목 고립 방지 설정을 반영하지 않음


# ── 유저 양식에서 스켈레톤 추출 ────────────────────────────────────────────────
# 역할별 후보 스타일 이름. 내장 양식 이름을 먼저 두고 보고서 양식에 흔한 짧은 이름을 뒤에 둔다
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
    """유저 양식에서 header.xml과 본문 구역의 쪽 설정만 남긴 빈 양식과 프로파일 초안을 만든다."""
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
                 r"\1\3", hpf)   # 작성자와 일시 메타데이터 제거
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for it in src.infolist():
            n = it.filename
            if n.startswith("BinData/") or re.match(r"Contents/section[1-9]", n) or n == "Preview/PrvImage.png":
                continue
            data = src.read(n)
            if n == "Contents/section0.xml":
                data = (first + "</hs:sec>").encode("utf-8")
            elif n == "Preview/PrvText.txt":
                data = b""   # 원본 미리보기 텍스트 제거
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
    if spec.get("cells"):   # "라벨 > right" 경로로 표 셀 채우기
        res = doc.tables.fill_by_path(spec["cells"])
        print(msg("fill_cells", ok=res["applied_count"], fail=res["failed_count"]))
        for f in res.get("failed", []):   # 실패 사유 예: 라벨이 문서에 여러 번 나옴(ambiguous label)
            print(msg("fill_cell_failed", path=f.get("path"), reason=f.get("reason")))
    save_hwpx(doc, out or src)
    print(msg("fill_ok", n=total, out=out or src))


def check(path: str, expect: str) -> int:
    """스키마 검증, 이미지 매니페스트 정합, rhwp 기대 조건 대조. 기대 조건 불일치를 포함한 이슈 수를 반환."""
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
