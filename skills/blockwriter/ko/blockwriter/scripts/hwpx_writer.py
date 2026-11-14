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
import uuid
import zipfile
from pathlib import Path

import lxml.etree as ET

import config as C
import manuscript as M
import toc_refs
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
    else:
        prof = {**C.PROFILE_DEFAULTS, **json.loads(Path(spec).read_text(encoding="utf-8"))}
    for level in ("chapter", "section", "subsection"):   # 라벨 파일의 번호 형식이 현재 프로파일의 형식을 덮어씀
        if C.label(f"formats.{level}") is not None:
            prof[f"{level}_format"] = C.label(f"formats.{level}")
    return prof


def builtin_skeleton(form_name: str, workdir: str) -> str:
    path = os.path.join(workdir, f"_skeleton_{form_name}.hwpx")
    return write_skeleton(FORMS[form_name], path)


class Builder(M.TocMarks):
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
        self.toc_items: list[tuple[str, str, str | None]] = []   # 목차 수록 항목 (M.TocMarks)
        self.bookmark_names = M.BookmarkNames()
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
        self.pending_caption = None   # 목차 등록을 기다리는 캡션 (종류, 목차 문구, 개체)
        # 조판 옵션 (cmd_build에서 지정)
        self.numbered_square = False
        self.toc = False
        self.toc_scope = C.TOC_SCOPE_DEFAULT
        self.cover = None
        self.page_number = False
        self.header_spec = None
        self.merge_mode = "auto"
        self.long_table_mode = "engine"
        self.notes = M.NoteRegistry(None)   # 출처 각주 통합 (build --footnote-merge)

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

    def para(self, role: str, text: str, footnotes: dict | None = None, no_heading: bool = False,
             adjust: dict | None = None, **attrs):
        """스타일, 문단 모양, 글자 모양 참조 3종을 함께 지정해야 서식이 붙는다.
        adjust는 원고 조정 표기의 값 (장평, 자간, 줄 간격을 스타일 값에서 더하는 %p)"""
        r = self.refs(role)
        if role == "square" and self.numbered_square and M.NUMBERED_SQUARE_RE.match(text):   # 1. 2. 3. 숫자 헤더
            r["para_pr_id_ref"] = self._numbered_pp(str(r["para_pr_id_ref"]), str(r["char_pr_id_ref"]), text)
        elif no_heading:   # 번호를 본문에 기입하므로 스타일의 자동 개요 번호를 끈다
            r["para_pr_id_ref"] = self._no_bullet_pp(str(r["para_pr_id_ref"]))
        else:
            text = self.manual_symbol.get(role, "") + text
        if adjust:
            r["para_pr_id_ref"] = self._line_pp(str(r["para_pr_id_ref"]), adjust.get("line", 0))
            r["char_pr_id_ref"] = self._adjusted_cp(str(r["char_pr_id_ref"]), adjust)
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

    def _adjusted_cp(self, base_cp: str, adjust: dict) -> str:
        """장평과 자간에 조정값(%p)을 더한 글자 모양. 일곱 글꼴 슬롯에 같은 값을 더한다"""
        deltas = {"ratio": adjust.get("ratio", 0), "spacing": adjust.get("spacing", 0)}
        if not any(deltas.values()):
            return base_cp
        key = (base_cp, "ADJUST", deltas["ratio"], deltas["spacing"])
        if key in self._cp_cache:
            return self._cp_cache[key]
        base = self.header.element.find(f".//{HH}charPr[@id='{base_cp}']")

        def shift(e):
            for tag, delta in deltas.items():
                node = e.find(f"{HH}{tag}")
                if node is not None and delta:
                    for lang, value in node.attrib.items():
                        node.set(lang, str(int(value) + delta))

        def signature(e):
            return (tuple(sorted((k, v) for k, v in e.attrib.items() if k != "id")), tuple(ET.tostring(c) for c in e))

        want = copy.deepcopy(base)
        shift(want)
        want_sig = signature(want)
        el = self.header.ensure_char_property(predicate=lambda e: signature(e) == want_sig, modifier=shift,
                                              base_char_pr_id=base_cp)
        self._cp_cache[key] = el.get("id")
        return self._cp_cache[key]

    def _line_pct(self, pp_id: str) -> int | None:
        """문단 모양의 줄 간격(%). 글자 크기 대비 비율이 아닌 줄 간격은 None"""
        pp = self.header.element.find(f".//{HH}paraPr[@id='{pp_id}']")
        node = next(pp.iter(f"{HH}lineSpacing"), None) if pp is not None else None
        return int(node.get("value")) if node is not None and node.get("type") == "PERCENT" else None

    def _line_pp(self, base_pp: str, delta: int) -> str:
        """줄 간격에 조정값(%p)을 더한 문단 모양. 줄 간격이 비율이 아닌 문단 모양은 그대로 돌려준다"""
        base_pct = self._line_pct(base_pp)
        if not delta or base_pct is None:
            return base_pp
        key = (str(base_pp), "LINE", delta)
        if key not in self._pp_cache:
            self._pp_cache[key] = self.header.ensure_paragraph_format(base_para_pr_id=base_pp,
                                                                      line_spacing_percent=base_pct + delta)
        return self._pp_cache[key]

    def _margin_pp(self, base_pp: str, **margins: int) -> str:
        """여백(intent, left, prev 등)을 바꾼 문단 모양. 구형 한/글용 저장값(hp:default)은 새 값의 2배로 기록 (양식 생성 규칙과 동일)"""
        key = (str(base_pp), "MARGIN") + tuple(sorted(margins.items()))
        if key not in self._pp_cache:
            pp = self.header.ensure_paragraph_format(base_para_pr_id=base_pp, margins=margins)
            for name, value in margins.items():
                legacy = self.header.element.find(f".//{HH}paraPr[@id='{pp}']//{HP}default/{HH}margin/{HC}{name}")
                if legacy is not None:
                    legacy.set("value", str(2 * value))
            self._pp_cache[key] = pp
        return self._pp_cache[key]

    def _pp_margin(self, pp_id: str, name: str) -> int:
        """문단 모양의 여백 값 (HWPUNIT). 새 한/글 값(hp:case), 없으면 구형 값(hp:default)의 절반"""
        pp = self.header.element.find(f".//{HH}paraPr[@id='{pp_id}']")
        case = pp.find(f".//{HP}case/{HH}margin/{HC}{name}")
        if case is not None:
            return int(case.get("value"))
        legacy = pp.find(f".//{HP}default/{HH}margin/{HC}{name}")
        return int(legacy.get("value")) // 2 if legacy is not None else 0

    def add_bookmark(self, p, text: str) -> str:
        """책갈피를 문단 첫 run의 첫 컨트롤로 기록하고 이름을 돌려준다. 표를 담은 문단에서는 표보다 앞에 놓인다.
        p는 문단 객체 또는 문단 요소 (캡션 문단은 요소로 받음)"""
        pe = getattr(p, "element", p)
        name = self.bookmark_names.issue(text)
        run = pe.find(f"{HP}run")
        if run is None:   # 글자가 없는 문단. 줄 배치 저장값보다 앞에 run을 둔다
            run = ET.Element(f"{HP}run", charPrIDRef=str(self.refs("body")["char_pr_id_ref"]))
            pe.insert(0, run)
        ctrl = ET.Element(f"{HP}ctrl")
        ET.SubElement(ctrl, f"{HP}bookmark", name=name)
        run.insert(0, ctrl)
        return name

    def _add_footnote(self, p, text: str, body_cp: str):
        """각주 참조를 문단 기본 글자 모양의 run에 두고 각주 본문에도 본문과 같은 인라인 서식을 적용한다.
        라이브러리는 참조를 문단의 마지막 run(첨자, 굵게 등)에 두고 각주 본문을 run 하나의 글자 모양으로만 만든다.
        출처 각주 통합 범위 안에서 문구가 같은 각주는 첫 각주 번호의 상호참조로 대체한다"""
        first = self.notes.lookup(text)
        if first is not None:
            self._note_crossref(p, str(body_cp), *first)
            return
        note = p.add_footnote("", run_attributes={"charPrIDRef": str(body_cp)})
        if not note.element.get("instId"):   # 상호참조가 가리킬 id. 구버전 라이브러리는 기록하지 않음
            note.element.set("instId", new_object_id())
        self.notes.remember(text, (note.element.get("instId"), note.element.get("number"),
                                   chr(int(note.element.get("suffixChar", str(ord(")")))))))
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

    def _note_crossref(self, p, base_cp: str, inst_id: str, number: str, suffix: str):
        """각주 번호 상호참조. 한/글이 저장하는 구조(필드 시작 run, 위 첨자 run 안의 번호와 필드 끝과 번호 뒤 문자)와 같게 기록한다.
        번호는 저장값이며 한/글이 상호참조를 갱신할 때 다시 매긴다"""
        pe = p.element
        runs = pe.findall(f"{HP}run")
        at = list(pe).index(runs[-1]) + 1 if runs else len(pe)   # 줄 배치 저장값보다 앞, 마지막 run 뒤
        field_id = new_object_id()
        begin_run = ET.Element(f"{HP}run", charPrIDRef=base_cp)
        begin_run.append(crossref_begin(field_id, f"?#{inst_id};3;1;0;0;", f"?#{inst_id};", "TARGET_FOOTNOTE", "OBJECT_TYPE_NUMBER"))
        sup_run = ET.Element(f"{HP}run", charPrIDRef=self._run_style(base_cp, script="sup"))
        ET.SubElement(sup_run, f"{HP}t").text = number
        ET.SubElement(ET.SubElement(sup_run, f"{HP}ctrl"), f"{HP}fieldEnd", beginIDRef=field_id,
                      fieldid=C.HWPX_CROSSREF_FIELD_ID)
        ET.SubElement(sup_run, f"{HP}t").text = suffix
        pe.insert(at, begin_run)
        pe.insert(at + 1, sup_run)
        pe.set("paraPrIDRef", self._bullet_shape_pp(pe.get("paraPrIDRef"), base_cp))
        p.section.mark_dirty()

    def _bullet_shape_pp(self, base_pp: str, cp: str) -> str:
        """글머리표의 글자 모양을 cp로 지정한 문단 모양. 글머리표 없는 문단 모양은 그대로 돌려준다.
        글머리표 글자 모양이 '본문 따름'이면 한/글이 문단 안 위 첨자 run을 따라 글머리표까지 줄여 그린다"""
        key = (str(base_pp), "BULLETSHAPE", str(cp))
        if key in self._pp_cache:
            return self._pp_cache[key]
        root = self.header.element
        pp = root.find(f".//{HH}paraPr[@id='{base_pp}']")
        hd = pp.find(f"{HH}heading") if pp is not None else None
        src = root.find(f".//{HH}bullet[@id='{hd.get('idRef')}']") if hd is not None and hd.get("type") == "BULLET" else None
        head = src.find(f"{HH}paraHead") if src is not None else None
        if head is None or head.get("charPrIDRef") == str(cp):
            self._pp_cache[key] = str(base_pp)
            return self._pp_cache[key]
        bullets = src.getparent()
        fixed = copy.deepcopy(src)
        fixed.set("id", str(max(int(b.get("id")) for b in bullets) + 1))
        fixed.find(f"{HH}paraHead").set("charPrIDRef", str(cp))
        bullets.append(fixed)
        bullets.set("itemCnt", str(len(bullets)))
        self._pp_cache[key] = self.header.ensure_paragraph_format(
            base_para_pr_id=base_pp, heading={"type": "BULLET", "idRef": fixed.get("id"), "level": hd.get("level", "0")})
        return self._pp_cache[key]

    def _flush_pp(self, base_pp: str) -> str:
        """좌우 여백과 첫 줄 들여쓰기가 0인 문단 모양. 그림을 담는 셀 문단용.
        유저 양식의 그림 위치 스타일에 여백이 있으면 그 폭만큼 줄이 좁아져 그림이 잘린다"""
        key = (str(base_pp), "FLUSH")
        if key not in self._pp_cache:
            self._pp_cache[key] = self.header.ensure_paragraph_format(
                base_para_pr_id=base_pp, margins={"left": 0, "right": 0, "intent": 0})
        return self._pp_cache[key]

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
            ch = self.refs("chapter")
            indent_pp: dict[int, str] = {}   # 왼쪽 여백 → 목차 절 스타일에서 파생한 문단 모양
            for it in M.toc_layout(self.toc_items):
                if it["kind"] == "title":
                    front(it["text"], str(ch["char_pr_id_ref"]), self._aligned_pp(str(ch["para_pr_id_ref"]), "CENTER"),
                          pageBreak="1" if cover or not it["first"] else "0")
                    continue
                item, text, left = it["item"], it["text"], it["indent"]
                r = self.refs("toc_chapter" if item == "chapter" else "toc_section")
                pp, cp = str(r["para_pr_id_ref"]), str(r["char_pr_id_ref"])
                if item not in ("chapter", "section"):   # 장과 절은 스타일의 여백 그대로
                    if left not in indent_pp:
                        indent_pp[left] = self.header.ensure_paragraph_format(base_para_pr_id=pp, margins={"left": left})
                    pp = indent_pp[left]
                p = front(text, cp, pp)
                p.element.set("styleIDRef", str(r["style_id_ref"]))
                if it["name"]:   # 항목 문구, 오른쪽 점선 탭, 쪽 참조 순서
                    tnode = [t for t in p.element.iter(f"{HP}t") if t.text][-1]
                    unit = C.TOC_UNIT_W.get(item, C.TOC_UNIT_W_DEFAULT)
                    width = max(C.TOC_TAB_POS - left - M.weighted_len(text) * unit - len(toc_refs.PLACEHOLDER) * unit, 1000)
                    ET.SubElement(tnode, f"{HP}tab", width=str(width), leader="3", type="2")
                    ref_run = ET.Element(f"{HP}run", charPrIDRef=cp)
                    p.element.findall(f"{HP}run")[-1].addnext(ref_run)
                    toc_page_ref(ref_run, it["name"], toc_refs.PLACEHOLDER)
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
            # 한/글 저작 순서(구역 정의 secPr, 단 정의 colPr, 쪽번호)를 따라 colPr 컨트롤 뒤에 둔다.
            # secPr 바로 뒤(colPr 앞)에 두면 생성 직후에는 한 run에 모여 있어 한/글이 읽지만, 한/글이
            # 재저장하면 secPr가 단독 run으로 분리되고 colPr가 다음 run으로 밀려 재오픈 시 구역 설정 대신
            # 기본 편집 용지(좌우 30mm, 위 20mm, 머리말 15mm)가 적용되어 본문 폭이 170mm에서 150mm로 줄었다.
            # 양식이 newNum(쪽번호 새로 시작)을 colPr 뒤에 두므로 그 뒤까지 지나 삽입한다. colPr가 없을 때만 secPr 기준.
            # 한/글이 저장한 유저 양식(스켈레톤)은 secPr와 colPr가 서로 다른 run에 있으므로 첫 run이 아닌 첫 문단 전체에서 찾는다.
            anchor = next((c for c in reversed(first.findall(f"{HP}run/{HP}ctrl"))
                           if c.find(f"{HP}colPr") is not None or c.find(f"{HP}newNum") is not None), None)
            if anchor is None:
                anchor = run.find(f"{HP}secPr")
            host = anchor.getparent() if anchor is not None else run
            host.insert(list(host).index(anchor) + 1 if anchor is not None else 0, ctrl)

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

    def _transparent_row(self, t, ri: int, ncol: int, text: str, role: str, align: str) -> int:
        """표 안의 투명 병합 행 (단위, 출처). 손으로 편집할 때 표와 함께 이동하도록 표 내부에 둔다. 반환: 행 높이
        출처 행은 줄 나눔 표기(<br>)마다 문단을 나누고 라벨('출처: ') 폭만큼 내어써서 둘째 줄부터 첫 출처 시작 위치에 맞춘다"""
        no_border = self._border_fill([])
        u = self.refs(role)
        lines = M.source_lines(text) if role == "source" else [text]
        t.set_cell_text(ri, 0, "\n".join(lines), split_paragraphs=True)
        pp = self._aligned_pp(str(u["para_pr_id_ref"]), align)
        hang = round(self._line_style(role).glyph_hu(M.source_label(lines[0]), C.SPACE_EM_HWPX)) if role == "source" else 0
        left = self._pp_margin(pp, "left")
        for li, pe in enumerate(t.cell(ri, 0).element.iter(f"{HP}p")):
            # 한/글 내어쓰기는 첫 줄을 왼쪽 여백에 두고 둘째 줄부터 들여 시작 (음수 intent).
            # 이어지는 문단은 왼쪽 여백으로 같은 위치에 두고 문단 위 여백을 없애 한 출처 행의 줄 사이를 고르게 둠
            line_pp = pp if li == 0 else self._margin_pp(pp, left=left, prev=0)
            if hang:
                line_pp = self._margin_pp(pp, intent=-hang) if li == 0 else self._margin_pp(pp, left=left + hang, intent=0, prev=0)
            pe.set("paraPrIDRef", line_pp)
            pe.set("styleIDRef", str(u["style_id_ref"]))
            for run in pe.iter(f"{HP}run"):
                run.set("charPrIDRef", str(u["char_pr_id_ref"]))
        line_pct = self._line_pct(pp)
        height = M.source_row_height(len(lines), self._line_style(role).size_hu * line_pct / 100 if line_pct else C.ROW_LINE_H)
        for ci in range(ncol):
            t.cell(ri, ci).element.set("borderFillIDRef", str(no_border))
            t.cell(ri, ci).set_size(height=height)
        if ncol > 1:
            t.merge_cells(ri, 0, ri, ncol - 1)
        return height

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
        open_b, close_b = C.caption_marks(kind)
        prefix = self.p.get("caption_prefix", "").format(c=max(self.numbering.n["chapter"], 1))
        run = cp.add_run(open_b + prefix, char_pr_id_ref=r["char_pr_id_ref"])
        # 필드에 저장하는 번호. 한/글은 열 때 다시 매기며 저장값을 그대로 그리는 렌더러도 올바른 번호를 보이게 함
        self.caption_counts[kind] += 1
        an = ET.SubElement(ET.SubElement(run.element, f"{HP}ctrl"), f"{HP}autoNum",
                           num=str(self.caption_counts[kind]), numType=kind)
        ET.SubElement(an, f"{HP}autoNumFormat", type="DIGIT", userChar="", prefixChar="", suffixChar="", supscript="0")
        cp.add_run(close_b + text, char_pr_id_ref=r["char_pr_id_ref"])
        # 목차 등록은 개체 기록이 끝난 뒤 (_mark_pending_caption)
        self.pending_caption = (C.CAPTION_KINDS[kind], f"{open_b}{prefix}{self.caption_counts[kind]}{close_b}{text}", holder)

    def _mark_pending_caption(self):
        """캡션이 붙은 표나 그림을 목차에 등록하고 책갈피를 개체 안에 둔다. 개체가 표이면 첫 셀의 첫 문단, 그 밖은 개체를 담은 문단.
        Why 첫 셀: 책갈피가 표 개체 안에 있어 표를 옮기면 함께 이동. 캡션 문단 안에 두면 rhwp가 캡션을 표와 겹쳐 그림.
        Why 개체 기록 뒤: 셀 글자를 기록할 때 run을 다시 만들므로 그 전에 넣은 책갈피는 지워짐"""
        if not self.pending_caption:
            return
        kind, text, holder = self.pending_caption
        self.pending_caption = None
        cell = next(holder.element.iter(f"{HP}tc"), None)
        host = next(cell.iter(f"{HP}p")) if cell is not None else next(
            a for a in holder.element.iterancestors() if a.tag == f"{HP}p")
        self.toc_mark(kind, text, host)

    # ── 헤더 계위 ───────────────────────────────────────────────────────
    def heading(self, level: int, text: str, adjust: dict | None = None):
        text = M.NUM_PREFIX_RE.sub("", text).strip()
        role = ("chapter", "section", "subsection", "ganada")[level - 1]
        if self.numbering.advance(level):
            self.pending_break = True
        label = M.heading_label(self.p, self.numbering.n, level, text)
        manual = self.p["numbering"] == "manual"
        p = self.para(role, label, no_heading=manual and level in (2, 3), adjust=adjust)
        self.toc_mark(role, label, p)
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
        widths = M.table_col_widths(rows, e.data.get("colwidth"), self.table_max_w, font, e.text)
        table_w = sum(widths)
        self.gap()
        r = self._centered_refs(M.table_pos_role(bool(e.text), bool(self.p.get("fig_pos"))))
        unit = e.data.get("unit")
        sources = e.data.get("sources", [])
        head = 1 if unit else 0   # 단위 행: 머리글 위 투명 병합 셀 (표 우측 끝 정렬)
        engine_long = nrow > C.LONG_TABLE_ROWS and not e.data.get("split_done")   # 장표: 글자처럼 취급 해제 대상
        break_attrs = self._take_break()   # 쪽 나눔은 표를 담은 문단에 적용 (앞의 빈 문단은 앞 쪽 끝에 남음)
        if engine_long:
            self._long_table_gap()
        t = self.doc.add_table(nrow + head + len(sources), ncol, width=table_w, **r, **break_attrs)
        if e.text:
            self.attach_caption(t, "TABLE", e.text, "TOP", table_w)
        t.set_column_widths(widths)
        cell_ref = self.refs("table_cell")
        left_ref = self.refs("table_cell_left")
        left_pp = str(left_ref["para_pr_id_ref"])
        if self._pp_align(left_pp) not in ("LEFT", "JUSTIFY"):   # 왼쪽 정렬 스타일이 없는 양식은 표 내용 스타일을 왼쪽으로 파생
            left_pp = self._aligned_pp(left_pp, "LEFT")
        extra_h = self._transparent_row(t, 0, ncol, unit, "unit", "RIGHT") if unit else 0   # 단위 행과 출처 행 높이의 합
        for k, src in enumerate(sources):   # 출처 행: 표 아래 투명 병합 셀, 왼쪽 정렬
            extra_h += self._transparent_row(t, head + nrow + k, ncol, src, "source", "LEFT")
        total_h = 0
        line_counts = M.row_line_counts(rows, widths, font, plan["vspans"], hdr)
        line_delta = e.data.get("adjust", {}).get("line", 0)   # 원고 조정 표기의 줄 간격 조정값 (%p)
        scale = M.line_scale(self._line_pct(str(cell_ref["para_pr_id_ref"])), e.data.get("adjust"))
        for ri, row in enumerate(rows):
            row_h = M.row_height(line_counts[ri], scale)
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
                    pe.set("paraPrIDRef", self._line_pp(str(bref["para_pr_id_ref"]) if bref else pp, line_delta))
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
            sz.set("height", str(total_h + extra_h))
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
        if engine_long:   # 장표: 한/글이 쪽 경계에서 행 단위로 나누고 제목행 반복
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
        self._mark_pending_caption()
        t.mark_dirty()
        if engine_long:
            self._long_table_gap()

    def _long_table_gap(self):
        """글자처럼 취급을 해제한 장표의 앞뒤에 두는 바탕글 빈 문단"""
        for _ in range(C.LONG_TABLE_GAP_LINES):
            self.doc.add_paragraph("", **self.refs("body"))

    # ── 그림 ────────────────────────────────────────────────────────────
    def image(self, e: M.Element):
        loaded = M.load_image(e)
        if loaded is None:
            return
        data, fmt, (w_mm, h_mm) = loaded
        self.gap()
        r = self._centered_refs("fig_pos")
        w_hu, h_hu, table_w = M.fit_figure(round(w_mm * 7200 / 25.4), round(h_mm * 7200 / 25.4), self.body_w)
        sources = e.data.get("sources", [])
        if not C.FIGURE_IN_TABLE:
            pic = self.doc.add_picture(data, fmt, width_mm=w_hu * 25.4 / 7200, height_mm=h_hu * 25.4 / 7200,
                                       **r, **self._take_break())
            if e.text:
                self.attach_caption(pic, "PICTURE", e.text, "BOTTOM", w_hu)
            self._mark_pending_caption()
            for src in sources:
                self.para("source", M.source_inline(src))
            return
        # 투명 1열 표에 그림을 넣고 표를 그림 번호 유형으로 지정. 내부 그림은 번호 집계에서 제외
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
            pe.set("paraPrIDRef", self._flush_pp(str(r["para_pr_id_ref"])))
            pe.set("styleIDRef", str(r["style_id_ref"]))
        cell.element.set("borderFillIDRef", self._border_fill([]))
        # 표 폭 산정에 쓴 좌우 여백을 셀에 직접 기록. 라이브러리의 표 기본 여백이 바뀌어도 그림 폭과 셀 안 폭이 같음
        cell.element.set("hasMargin", "1")
        cm = cell.element.find(f"{HP}cellMargin")
        if cm is not None:
            cm.set("left", str(C.CELL_MARGIN_LR))
            cm.set("right", str(C.CELL_MARGIN_LR))
        cell.set_size(height=h_hu + 2 * C.ROW_LINE_H)
        source_h = sum(self._transparent_row(t, 1 + k, 1, src, "source", "LEFT") for k, src in enumerate(sources))
        t.element.set("numberingType", "PICTURE")
        pos = t.element.find(f"{HP}pos")
        if pos is not None:
            pos.set("horzAlign", "CENTER")
        sz = t.element.find(f"{HP}sz")
        if sz is not None:
            sz.set("height", str(h_hu + 2 * C.ROW_LINE_H + source_h))
        if e.text:
            self.attach_caption(t, "PICTURE", e.text, "BOTTOM", table_w)
        self._mark_pending_caption()
        t.mark_dirty()

    # ── 실행 ────────────────────────────────────────────────────────────
    def build(self, elems: list[M.Element], footnotes: dict, out: str):
        # 목차 스타일이 없는 양식은 목차를 생략. 본문 기록 전에 판정하여 쓰이지 않을 책갈피를 붙이지 않음
        if self.toc and not (self.p.get("toc_chapter") and self.p.get("toc_section")):
            print(msg("warn_no_toc_style"))
            self.toc = False
        for e in M.attach_block_notes(elems):
            self.notes.enter(e.kind, e.level)
            if e.kind == "heading":
                self.heading(e.level, e.text, e.data.get("adjust"))
                self.last_para = None   # 제목 뒤 출처 줄이 앞 절 문단의 각주로 붙지 않게 연결을 끊음
            elif e.kind in ("square", "circle", "dash", "dot", "note"):
                self.last_para = self.para(e.kind, e.text, footnotes, adjust=e.data.get("adjust"))
                self.last_cp = str(self.refs(e.kind)["char_pr_id_ref"])
            elif e.kind == "unit":
                self.para("unit", e.text)
            elif e.kind == "source":   # 표·그림에 붙지 않은 출처 줄은 직전 문단의 각주로 이동
                if self.last_para is not None:
                    self._add_footnote(self.last_para, M.source_inline(e.text), self.last_cp)
                else:
                    self.para("note", M.source_inline(e.text), footnotes)
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


def crossref_begin(field_id: str, command: str, ref_path: str, ref_type: str, content_type: str):
    """상호참조 필드 시작 컨트롤(hp:ctrl). 한/글이 저장하는 구조와 같게 기록한다.
    매개변수 이름과 값은 한/글 저장 파일 그대로 ("Fiexde" 철자 포함). Command의 뒤 숫자는 참조 내용을 뜻하는 저장값"""
    ctrl = ET.Element(f"{HP}ctrl")
    begin = ET.SubElement(ctrl, f"{HP}fieldBegin", id=field_id, type="CROSSREF",
                          name="", editable="0", dirty="0", zorder="-1", fieldid=C.HWPX_CROSSREF_FIELD_ID)
    params = (("booleanParam", "Fiexde", "1"), ("integerParam", "Prop", "0"),
              ("stringParam", "Command", command), ("stringParam", "RefPath", ref_path),
              ("stringParam", "RefType", ref_type), ("stringParam", "RefContentType", content_type),
              ("booleanParam", "RefHyperLink", "false"), ("stringParam", "RefOpenType", "HWPHYPERLINK_JUMP_CURRENTTAB"))
    holder = ET.SubElement(begin, f"{HP}parameters", cnt=str(len(params)), name="")
    for tag, name, value in params:
        ET.SubElement(holder, f"{HP}{tag}", name=name).text = value
    return ctrl


def toc_page_ref(run, name: str, value: str):
    """책갈피 쪽 번호 상호참조를 run에 기록한다 (필드 시작, 저장값 글자, 필드 끝 순서).
    저장값은 한/글이 문서를 불러올 때 책갈피 위치의 쪽번호로 다시 계산한다"""
    field_id = new_object_id()
    run.append(crossref_begin(field_id, f"?{name};6;0;0;0;", f"?{name};", "TARGET_BOOKMARK", "OBJECT_TYPE_PAGE"))
    ET.SubElement(run, f"{HP}t").text = value
    ET.SubElement(ET.SubElement(run, f"{HP}ctrl"), f"{HP}fieldEnd", beginIDRef=field_id, fieldid=C.HWPX_CROSSREF_FIELD_ID)


def new_object_id() -> str:
    """개체와 필드의 인스턴스 id (python-hwpx가 표와 각주에 쓰는 범위와 같은 31비트 난수)"""
    return str(uuid.uuid4().int & 0x7FFFFFFF)


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
    """build 명령의 HWPX 경로"""
    workdir = tempfile.mkdtemp(prefix="blockwriter_")   # 내장 양식 스켈레톤 보관. 조판이 끝나면 삭제
    try:
        _build_hwpx(a, elems, footnotes, out, workdir)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _build_hwpx(a, elems, footnotes, out: str, workdir: str):
    profile = load_profile(a.profile)
    skeleton = a.skeleton or (builtin_skeleton(a.profile, workdir) if a.profile in FORMS else None)
    if not skeleton or not os.path.exists(skeleton):
        sys.exit(msg("err_no_skeleton", path=skeleton))
    b = Builder(skeleton, profile, page_break=a.page_break)
    b.numbered_square = a.numbered_square
    b.toc, b.toc_scope = a.toc, a.toc_scope
    b.page_number = a.page_number
    b.cover = parse_cover(a.cover)
    b.header_spec = a.header
    b.merge_mode = a.merge
    b.long_table_mode = a.long_table
    b.notes = M.NoteRegistry(a.footnote_merge)
    b.build(elems, footnotes, out)
    fixed = repair_manifest(out)
    if fixed:
        print(msg("manifest_fixed", n=fixed))
    refs = sum(1 for _, _, name in b.toc_items if name)
    if refs:   # 한/글은 문서를 불러올 때 쪽 참조를 다시 계산하므로 저장값은 자리 표시 값으로 둔다
        print(msg("toc_hwpx", n=len(b.toc_items), refs=refs, mark=toc_refs.PLACEHOLDER))
    elif b.toc_items:
        print(msg("toc_no_numbers", n=len(b.toc_items), fmt="hwpx"))


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
