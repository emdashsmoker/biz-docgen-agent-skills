"""Markdown 원고를 요소 목록으로 바꾸고, 형식과 무관한 조판 계산(표 열 폭, 정렬, 병합, 그림 크기)을 한다.
HWPX와 DOCX 조판기는 모두 이 모듈의 결과를 쓴다."""
from __future__ import annotations

import copy
import io
import math
import os
import re
import unicodedata
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import config as C
from config import msg


@dataclass
class Element:
    kind: str                # heading square circle dash dot note unit colwidth source table table_caption image pagebreak
    text: str = ""
    level: int = 0           # heading: 1-4
    data: dict = field(default_factory=dict)


HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
TABLE_SEP_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$")
COL_WIDTH_SEP_RE = re.compile(r"[,，\s]+")
FOOTNOTE_DEF_RE = re.compile(r"^\[\^([^\]]+)\]:\s*(.*)$")
INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|<sup>.*?</sup>|<sub>.*?</sub>|\^[^^\s]+\^|\[\^[^\]]+\])")
SQUARE_MARK = ("□", "■", "☐")
CIRCLE_MARK = ("○", "❍", "◦", "ㅇ")
NOTE_MARK = ("※", "* ")   # '*' 주석은 뒤에 공백이 있을 때만. '*기울임*'과 '**굵게**'로 시작하는 줄은 서술
MERGE_MARKS = ("^", "<")  # 병합 지시 셀. 내용이 없으므로 폭, 줄 수, 정렬 판정에서 제외
NUMERIC_CELL = re.compile(r"^[-+±(]?[\d,]+(?:\.\d+)?%?\)?$")
BULLET_PREFIXES = ("·", "•", "ㆍ", "∙", "○", "◦", "❍", "□", "■", "※", "- ", "▪")
CELL_BULLET_MARKS = ("◦", "○", "ㅇ", "·", "•", "ㆍ")   # 셀 ◦ 글머리 스타일로 바꾸는 줄 머리 기호
CELL_MARK_RE = re.compile(r"^\s*[◦○ㅇ·•ㆍ-]\s*")        # 셀 글머리 줄에서 지우는 머리 기호와 뒤 빈칸


def _alt(tokens) -> str:
    """원고 표기 토큰의 정규식 선택지. 토큰 안의 공백은 빈칸 유무와 관계없이 일치 ('열 폭'은 '열폭'과도 일치)"""
    return "|".join(r"\s*".join(re.escape(w) for w in t.split()) for t in tokens)


def _format_re(fmt: str, fields: dict[str, str]) -> str | None:
    """라벨 형식이 쓰는 번호의 정규식 ('Chapter {n}. ' → 'Chapter\\s*\\d+\\s*\\.'). 형식에 번호가 없으면 None"""
    parts = re.split(r"\{(\w+)\}", fmt)   # 글자, 자리표시, 글자, 자리표시, ...
    if not any(parts[1::2]):
        return None
    words = [p for i, part in enumerate(parts)
             for p in ([fields[part]] if i % 2 else [re.escape(w) for w in part.split()])]
    return r"\s*".join(words)


def compile_notation():
    """현재 라벨(기본 토큰과 라벨 파일이 추가한 토큰)로 원고 표기 정규식을 만듦.
    build는 라벨 파일을 읽은 뒤 다시 호출. 라벨 파일의 번호 형식으로 쓴 헤더 번호도 제N장, 가.와 같이 제거"""
    global CAPTION_RE, FIG_CAPTION_RE, UNIT_RE, COL_WIDTH_RE, SOURCE_RE, SOURCE_PAREN_RE, NUM_PREFIX_RE
    src = C.label("notation.source")
    paren = [t for t in src if t in C.SOURCE_PAREN_TOKENS or t not in C.LABEL_DEFAULTS["notation"]["source"]]
    CAPTION_RE = re.compile(rf"^[<＜]\s*(?:{_alt(C.label('notation.table'))})\s*[^>＞]*[>＞]\s*(.*)$")
    FIG_CAPTION_RE = re.compile(rf"^\[\s*(?:{_alt(C.label('notation.figure'))})\s*[^\]]*\]\s*(.*)$")
    UNIT_RE = re.compile(rf"^\(\s*(?:{_alt(C.label('notation.unit'))})\s*[:：].*\)$")
    COL_WIDTH_RE = re.compile(rf"^\(\s*(?:{_alt(C.label('notation.colwidth'))})\s*[:：]\s*(.*)\)$")
    SOURCE_RE = re.compile(rf"^(?:[(（]\s*(?:{_alt(paren)})\s*[)）]|(?:{_alt(src)})\s*[:：])")
    SOURCE_PAREN_RE = re.compile(rf"^[(（]\s*({_alt(paren)})\s*[)）]\s*")
    extra = [_format_re(C.label(f"formats.{lv}").split("{t}")[0], dict.fromkeys(("n", "c", "s", "ss"), r"\d+"))
             for lv in ("chapter", "section", "subsection") if C.label(f"formats.{lv}") is not None]
    if C.label("letters") != C.LABEL_DEFAULTS["letters"]:
        extra.append(_format_re(C.label("letters.format"), {"x": "[" + "".join(map(re.escape, C.label("letters.items"))) + "]"}))
    NUM_PREFIX_RE = re.compile(r"^(제\s*\d+\s*장|\d+(?:\.\d+)*\.?|[가-힣]\.%s)\s+" % "".join("|" + p for p in extra if p))


compile_notation()


def _strip_marker(text: str, marks: tuple) -> str | None:
    for m in marks:
        if text.startswith(m):
            return text[len(m):].lstrip()
    return None


def parse_markdown(path: str) -> tuple[list[Element], dict[str, str]]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    footnotes: dict[str, str] = {}
    # 불릿 계위는 들여쓰기 폭의 순위로 판정 (폭 값 자체는 원고마다 다름)
    indents = sorted({len(m.group(1).expandtabs(4)) for ln in lines if (m := BULLET_RE.match(ln))})
    elems: list[Element] = []
    i = 0
    blank = False   # 직전 줄이 빈 줄인지. 표·그림 뒤 ※ 줄은 빈 줄로 띄우면 블록에 붙지 않는다
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        i += 1
        if not stripped:
            blank = True
            continue
        gap, blank = blank, False
        if m := FOOTNOTE_DEF_RE.match(stripped):
            footnotes[m.group(1)] = m.group(2)
            continue
        if stripped == "---":
            elems.append(Element("pagebreak"))
            continue
        if m := HEADING_RE.match(stripped):
            elems.append(Element("heading", m.group(2).strip(), len(m.group(1))))
            continue
        if stripped.startswith("|"):
            rows = []
            j = i - 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(lines[j].strip())
                j += 1
            i = j
            tbl = _parse_table(rows, elems)
            k = i
            while i < len(lines) and not lines[i].strip():
                i += 1
            blank = i > k
            # 빈 줄 뒤 다음 표 캡션 바로 위에 쓴 단위 줄은 다음 표의 캡션 앞 단위 줄이므로 남겨 두어 다음 표가 흡수
            opens_next = blank and i + 1 < len(lines) and _opens_table(lines[i + 1])
            if i < len(lines) and UNIT_RE.match(lines[i].strip()) and not tbl.data.get("unit") and not opens_next:
                tbl.data["unit"] = lines[i].strip()   # 표 뒤에 쓴 단위 줄도 표 위 단위 행으로
                i += 1
                blank = False
            elems.append(tbl)
            continue
        if m := IMAGE_RE.match(stripped):
            elems.append(Element("image", m.group(1).strip(),
                                 data={"path": m.group(2).strip(), "base": os.path.dirname(os.path.abspath(path))}))
            continue
        if m := CAPTION_RE.match(stripped):
            elems.append(Element("table_caption", m.group(1).strip()))
            continue
        if m := FIG_CAPTION_RE.match(stripped):
            if elems and elems[-1].kind == "image":
                elems[-1].text = m.group(1).strip()
            continue
        if UNIT_RE.match(stripped):
            elems.append(Element("unit", stripped))
            continue
        if m := COL_WIDTH_RE.match(stripped):
            elems.append(Element("colwidth", m.group(1).strip()))
            continue
        if stripped.startswith(">"):   # 인용 줄은 내용으로 역할 판정 (출처 표기면 출처, 아니면 주석)
            body = stripped.lstrip("> ").strip()
            if SOURCE_RE.match(body):
                elems.append(Element("source", SOURCE_PAREN_RE.sub(r"\1: ", body), data={"gap": gap}))
            else:   # '> ※ 내용'도 '※ 내용'과 같게 기호를 떼어 저장 (본문 주석에서 기호 중복 방지)
                t = _strip_marker(body, NOTE_MARK)
                elems.append(Element("note", body if t is None else t,
                                     data={"gap": gap, "mark": "※" if t is None else body[0]}))
            continue
        if SOURCE_RE.match(stripped):
            elems.append(Element("source", SOURCE_PAREN_RE.sub(r"\1: ", stripped)))
            continue
        if (t := _strip_marker(stripped, SQUARE_MARK)) is not None:
            elems.append(Element("square", t))
            continue
        if (t := _strip_marker(stripped, NOTE_MARK)) is not None:
            elems.append(Element("note", t, data={"gap": gap, "mark": stripped[0]}))
            continue
        if m := BULLET_RE.match(raw):
            indent = len(m.group(1).expandtabs(4))
            rank = indents.index(indent) if indent in indents else len(indents)
            body = m.group(2).strip()
            if (t := _strip_marker(body, CIRCLE_MARK)) is not None:
                elems.append(Element("circle", t))
            elif (t := _strip_marker(body, SQUARE_MARK)) is not None:
                elems.append(Element("square", t))
            elif (t := _strip_marker(body, NOTE_MARK)) is not None:
                elems.append(Element("note", t, data={"gap": gap, "mark": body[0]}))
            else:
                elems.append(Element(("circle", "dash", "dot")[min(rank, 2)], body))
            continue
        if (t := _strip_marker(stripped, CIRCLE_MARK)) is not None:
            elems.append(Element("circle", t))
            continue
        elems.append(Element("circle", stripped))   # 기호 없는 일반 문단은 ○ 서술
    return elems, footnotes


def _opens_table(line: str) -> bool:
    """표 블록을 여는 줄 (캡션 줄, 열 폭 줄, 표 행)"""
    s = line.strip()
    return bool(CAPTION_RE.match(s) or COL_WIDTH_RE.match(s) or s.startswith("|"))


def _parse_table(rows: list[str], elems: list[Element]) -> Element:
    aligns: list[str | None] = []
    cells: list[list[str]] = []
    for r in rows:
        if TABLE_SEP_RE.match(r):
            for seg in r.strip("|").split("|"):
                s = seg.strip()
                aligns.append("LEFT" if s.startswith(":") and not s.endswith(":")
                              else "RIGHT" if s.endswith(":") and not s.startswith(":")
                              else "CENTER" if s.startswith(":") else None)
            continue
        cells.append([c.strip().replace("<br>", "\n") for c in r.strip().strip("|").split("|")])
    # 표 바로 앞 세 요소 안의 캡션, 단위 줄, 열 폭 줄을 순서와 무관하게 흡수
    found = {"table_caption": None, "unit": None, "colwidth": None}
    for k in range(len(elems) - 1, max(len(elems) - 1 - len(found), -1), -1):
        kind = elems[k].kind
        if kind in found and found[kind] is None:
            found[kind] = elems.pop(k).text
        else:
            break
    return Element("table", found["table_caption"] or "",
                   data={"rows": cells, "aligns": aligns, "unit": found["unit"], "colwidth": found["colwidth"]})


def attach_block_notes(elems: list[Element]) -> list[Element]:
    """표와 그림 바로 뒤의 ※, *, 출처 줄을 블록 하단 출처 행으로 붙이고 표 뒤 단위 줄을 단위 행으로 올린다.
    빈 줄을 두고 쓴 ※, * 줄은 블록에 붙이지 않고 본문 주석으로 둔다."""
    out: list[Element] = []
    skip = 0
    for idx, e in enumerate(elems):
        if skip:
            skip -= 1
            continue
        if e.kind in ("table", "image"):
            srcs, consumed = [], 0
            for nx in elems[idx + 1:]:
                if nx.kind == "note" and nx.data.get("gap"):
                    break
                if nx.kind == "note":   # 출처 행에서도 주석 기호를 남겨 출처 줄과 구별. '※ 출처:' 표기는 출처 줄 그대로
                    srcs.append(nx.text if SOURCE_RE.match(nx.text) else f"{nx.data.get('mark', '※')} {nx.text}")
                elif nx.kind == "source":
                    srcs.append(nx.text)
                elif nx.kind == "unit" and e.kind == "table" and not e.data.get("unit"):
                    e.data["unit"] = nx.text
                else:
                    break
                consumed += 1
            e.data["sources"] = srcs
            skip = consumed
        out.append(e)
    return out


# ── 원고 린트: 조판 전에 원고 결함을 알린다 (변환은 계속 진행) ─────────────────
GANADA_LEVEL = 4   # 가나다는 선택적 묶음이라 절이나 소절 바로 아래에 올 수 있음
BODY_KINDS = ("square", "circle", "dash", "dot", "note")   # 조판기가 각주 참조를 처리하는 본문 문단


def lint(elems: list[Element], footnotes: dict | None = None) -> list[str]:
    """원고를 고쳐야 해소되는 결함"""
    issues = []
    prev_level = 0
    for idx, e in enumerate(elems):
        if e.kind == "heading":
            skipped = e.level > prev_level + 1 and prev_level
            if skipped and not (e.level == GANADA_LEVEL and prev_level >= 2):
                issues.append(msg("lint_heading_skip", text=e.text[:30], prev=prev_level, cur=e.level))
            prev_level = e.level
        if e.kind == "square":
            nxt = elems[idx + 1].kind if idx + 1 < len(elems) else None
            if nxt not in ("circle", "dash", "dot", "note"):
                issues.append(msg("lint_square_alone", text=e.text[:30]))
        if e.kind == "table" and not e.text:
            issues.append(msg("lint_no_caption"))
        if e.kind == "colwidth":   # 표에 흡수되지 않은 열 폭 줄은 조판에 쓰이지 않음
            issues.append(msg("lint_colwidth_alone", text=e.text[:30]))
    return issues + _lint_attached(elems, footnotes or {})


def _lint_attached(elems: list[Element], footnotes: dict) -> list[str]:
    """표와 그림에 부착한 뒤의 요소 순서로 판정하는 결함 (각주 참조, 출처 줄 위치).
    attach_block_notes는 요소를 고치므로 사본에 적용하여 조판기가 받을 원고를 바꾸지 않음"""
    issues, refs, has_para = [], [], False
    for e in attach_block_notes(copy.deepcopy(elems)):
        if e.kind == "heading":   # 조판기는 제목에서 직전 문단 연결을 끊음
            has_para = False
        elif e.kind in BODY_KINDS:
            has_para = True
            refs += [seg for kind, seg in inline_segments(e.text) if kind == "footnote"]
        elif e.kind == "source" and not has_para:
            issues.append(msg("lint_source_no_para", text=e.text[:30]))
    issues += [msg("lint_footnote_undefined", key=k) for k in dict.fromkeys(refs) if k not in footnotes]
    issues += [msg("lint_footnote_unused", key=k) for k in footnotes if k not in refs]
    return issues


def hitl_notices(elems: list[Element], ask_page_break: bool = True, ask_long_table: bool = True) -> list[str]:
    """원고와 무관하게 유저가 고를 조판 선택지(쪽 나눔, 장표)를 알린다. 옵션으로 이미 고른 항목은 제외"""
    notices = []
    sec_sizes, cur, cur_level = [], None, 0
    for e in elems:
        if e.kind == "heading" and e.level <= 2:
            # 곧바로 하위 제목이 이어지는 장 제목과 문서 제목은 하위 절과 같은 쪽에 놓이므로 집계에서 제외
            if cur is not None and not (cur == 0 and e.level > cur_level):
                sec_sizes.append(cur)
            cur, cur_level = 0, e.level
        elif cur is not None:
            cur += 1
    if cur is not None:
        sec_sizes.append(cur)
    short = sum(1 for n in sec_sizes if n < C.SHORT_SECTION_ELEMS)
    if short and ask_page_break:
        notices.append(msg("hitl_page_break", total=len(sec_sizes), short=short, limit=C.SHORT_SECTION_ELEMS))
    for e in elems:
        if ask_long_table and e.kind == "table" and len(e.data["rows"]) > C.LONG_TABLE_ROWS:
            notices.append(msg("hitl_long_table", rows=len(e.data["rows"]), title=e.text or "-"))
    return notices


# ── 표 계산 (단위 HWPUNIT, DOCX 조판기는 변환하여 사용) ─────────────────────────
def shown_text(text: str) -> str:
    """인라인 서식 표기(굵게, 기울임, 첨자 기호)와 각주 참조를 뺀 출력 글자"""
    return "".join(seg for kind, seg in inline_segments(text) if kind != "footnote")


def is_numeric_cell(text: str) -> bool:
    """출력 글자 기준 숫자 셀 여부. `**5**`처럼 서식을 입힌 숫자도 숫자로 본다"""
    return bool(NUMERIC_CELL.match(shown_text(text).replace(" ", "")))


def char_units(ch: str, space_em: float, ratio: float, spacing: float) -> float:
    """글자 1자의 폭 (한글 반 자 = 1). 빈칸은 형식별 폭, 영문과 숫자와 기호는 나눔고딕 글자별 폭(GLYPH_EM)으로 센다.
    빈칸 폭은 한/글과 Word가 달라(HWPX 0.5em, DOCX 0.28em) 호출하는 형식이 넘긴다.
    장평(%)은 글자 폭에 곱하고 자간(%)은 글자마다 더하므로 좁은 영문 글자일수록 한글 반 자 대비 폭이 더 줄어든다"""
    if ch == " ":
        em = space_em
    elif ch in C.GLYPH_EM:
        em = C.GLYPH_EM[ch]
    elif unicodedata.east_asian_width(ch) in ("W", "F"):
        return C.WIDE_UNITS
    else:
        return C.OTHER_UNITS
    return (em * ratio + spacing) / ((C.CELL_HANGUL_EM * ratio + spacing) / 2)


NUMBERED_SQUARE_RE = re.compile(r"^(\d+)\.(\s+)")   # --numbered-square의 '1. 제목' 줄


def number_prefix_em(text: str, space_em: float) -> float:
    """'1. 제목' 줄의 번호, 마침표, 뒤 빈칸의 폭 (글자 크기 배수). 둘째 줄을 번호 뒤 글자에 맞추는 내어쓰기 폭"""
    m = NUMBERED_SQUARE_RE.match(text)
    if m is None:
        return 0.0
    return sum(C.GLYPH_EM[d] for d in m.group(1)) + C.GLYPH_EM["."] + len(m.group(2)) * space_em


def text_units(text: str, space_em: float = C.SPACE_EM_HWPX, ratio: float = 100, spacing: float = 0) -> float:
    """출력되는 글자 폭의 합 (한글 반 자 단위, 인라인 서식 표기는 제외)"""
    return sum(char_units(ch, space_em, ratio, spacing) for ch in shown_text(text))


def weighted_len(text: str, space_em: float = C.SPACE_EM_HWPX, ratio: float = 100, spacing: float = 0) -> int:
    """글자 폭 합의 올림값. 줄 수와 정렬 판정처럼 글자가 넘치면 안 되는 판정에 사용"""
    return math.ceil(round(text_units(text, space_em, ratio, spacing), 6))   # 소수 누적 오차로 1이 더 올라가지 않게 반올림


def pad_rows(rows: list[list[str]]) -> list[list[str]]:
    width = max(len(r) for r in rows)
    return [r + [""] * (width - len(r)) for r in rows]


def calc_col_widths(rows: list[list[str]], max_w: int, font: CellFont) -> list[int]:
    """열 필요폭을 표 내용 스타일의 실제 글자 폭으로 산정하고 상한과 하한 안에 맞춘다. 합계가 표의 실폭이다.
    글자 폭을 고정값으로 크게 잡으면 열마다 여유가 쌓여 정보가 적은 표도 상한까지 넓어지고 ○ 계위 밖으로 나감"""
    ncol = max(len(r) for r in rows)
    line_w = [0.0] * ncol   # 열에서 가장 긴 줄의 폭 (HWPUNIT). 올림하지 않아 빈칸 하나의 소수 초과분이 열을 넓히지 않음
    for r in rows:
        for c, cell in enumerate(r):
            if cell.strip() in MERGE_MARKS:
                continue
            span = h_span(r, c)   # '<'로 가로 병합한 셀의 글자는 병합한 열들이 나누어 담음
            for ln in cell.split("\n"):
                share = font.line_units(ln.strip()) * font.unit_w / span
                for k in range(c, c + span):
                    line_w[k] = max(line_w[k], share)
    # 1줄 보장 폭은 글자 크기와 관계없는 실제 폭. 이 폭 안의 이름과 짧은 문구는 접지 않고 넘는 열만 2줄로 접음
    eff = [w if w <= C.COL_ONE_LINE_W else max(C.COL_ONE_LINE_W, w * C.COL_WRAP_RATIO) for w in line_w]
    need = [max(round(w) + C.COL_PAD_W, C.COL_MIN_W) for w in eff]
    total = sum(need)
    floor_w = int(max_w * C.TABLE_MIN_RATIO)
    if total > max_w:
        # 균등 몫 이하인 짧은 라벨 열은 필요폭을 보장하고 나머지 열은 필요폭 비율로 줄임.
        # 비율로 줄이면 나머지 열의 접힘 비율이 비슷해져 행 높이가 고름. 몫을 반복해 다시 구하면 중간 열이 몫 안에 들어
        # 필요폭을 다 받고 가장 긴 열만 크게 줄어 그 열의 셀이 여러 줄로 접힘
        share = max_w / ncol
        short = [need[i] <= share for i in range(ncol)]
        remaining = max_w - sum(n for n, sh in zip(need, short) if sh)
        psum = sum(n for n, sh in zip(need, short) if not sh) or 1
        widths = [n if sh else max(int(remaining * n / psum), C.COL_MIN_W) for n, sh in zip(need, short)]
        widths[-1] += max_w - sum(widths)
    elif total < floor_w:
        extra, usum = floor_w - total, sum(eff) or 1
        widths = [need[c] + int(extra * eff[c] / usum) for c in range(ncol)]
        widths[-1] += floor_w - sum(widths)
    else:
        widths = need
    return widths


def fixed_col_widths(spec: str | None, ncol: int, max_w: int, title: str) -> list[int] | None:
    """원고의 열 폭 줄(열별 표 폭 상한 대비 %)을 열 폭으로 바꾼다. 값의 합계가 표 폭.
    자동 산정이 맞지 않는 표에 쓰는 수동 지정이므로 하한 보정 없이 지정값을 따름.
    지정이 없으면 None. 값이 맞지 않으면 WARN을 출력하고 None을 돌려 자동 산정으로 조판"""
    if not spec:
        return None
    try:
        values = [float(v) for v in COL_WIDTH_SEP_RE.split(spec.strip()) if v]
    except ValueError:
        values = []
    if not values or min(values) <= 0:
        print(msg("warn_colwidth_value", title=title or "-", spec=spec))
        return None
    if len(values) != ncol:
        print(msg("warn_colwidth_count", title=title or "-", n=len(values), ncol=ncol))
        return None
    total = sum(values)
    if total > C.COL_WIDTH_PCT_MAX + C.COL_WIDTH_PCT_TOL:
        print(msg("warn_colwidth_over", title=title or "-", total=f"{total:g}", limit=C.COL_WIDTH_PCT_MAX))
        return None
    widths = [int(max_w * v / C.COL_WIDTH_PCT_MAX) for v in values]
    widths[-1] += round(max_w * total / C.COL_WIDTH_PCT_MAX) - sum(widths)   # 반올림 잔차는 마지막 열에
    return widths


def h_span(row: list[str], c: int) -> int:
    """c열 셀이 오른쪽 '<' 셀과 가로 병합하는 열 수 (병합이 없으면 1)"""
    n = 1
    while c + n < len(row) and row[c + n].strip() == "<":
        n += 1
    return n


def bullet_head_hu(char: str, size_hu: float, offset_pct: float, adjust_hu: float) -> float:
    """글머리 기호 폭 + 기호 뒤 간격 + 폭 조정 (HWPUNIT). 반각 문자(하이픈 등)만 반각 폭으로 셈"""
    half = unicodedata.east_asian_width(char) in ("Na", "H")
    width = C.DOCX_HALFWIDTH_BULLET if half else C.DOCX_FULLWIDTH_BULLET
    return size_hu * width + size_hu * offset_pct / 100 + adjust_hu


@dataclass(frozen=True)
class LineStyle:
    """셀 안 문단 스타일의 글자 모양과 줄 앞 폭. 크기와 줄 앞 폭은 HWPUNIT, 장평과 자간은 %.
    줄 앞 폭은 문단의 좌우 여백과 글머리 기호가 차지하는 폭"""
    size_hu: float
    ratio: float
    spacing: float
    lead_hu: float = 0

    @property
    def unit_w(self) -> float:
        """셀 글자의 가중 1단위(한글 반 자) 폭. 한글 1자 폭은 글자 크기 x 글꼴 한글 폭 비율 x 장평에 자간을 더한 값"""
        return self.size_hu * (C.CELL_HANGUL_EM * self.ratio + self.spacing) / 100 / 2

    def text_hu(self, text: str, space_em: float) -> float:
        """이 스타일로 출력한 글자와 줄 앞 폭의 합 (HWPUNIT)"""
        return text_units(text, space_em, self.ratio, self.spacing) * self.unit_w + self.lead_hu


@dataclass(frozen=True)
class CellFont:
    """표 셀의 줄 스타일 (열 폭과 행 줄 수 산정용). 가중 1단위는 표 내용 스타일 기준. 빈칸 폭은 글자 크기 배수.
    일반 줄은 표 내용과 표 내용 왼쪽 스타일 중 넓은 쪽, 셀 글머리 스타일이 없는 양식은 글머리 줄을 일반 줄로 셈"""
    space_em: float
    plain: tuple[LineStyle, ...]
    bullet: LineStyle | None = None
    dash: LineStyle | None = None

    @property
    def unit_w(self) -> float:
        return self.plain[0].unit_w

    def line_units(self, line: str) -> float:
        """셀 한 줄이 차지하는 폭 (한글 반 자 단위). 글머리 줄은 머리 기호를 지운 글자에 기호 폭과 여백을 더함.
        글자만 세면 셀 글머리의 들여쓰기와 셀 안 문단 여백이 빠져 열이 좁게 잡히고 글자가 셀 경계에 닿음"""
        st = line.lstrip()
        if self.bullet is not None and st.startswith(CELL_BULLET_MARKS):
            hu = self.bullet.text_hu(CELL_MARK_RE.sub("", line), self.space_em)
        elif self.dash is not None and st.startswith("- "):
            hu = self.dash.text_hu(CELL_MARK_RE.sub("", line), self.space_em)
        else:
            hu = max(s.text_hu(line, self.space_em) for s in self.plain)
        return hu / self.unit_w


def cell_lines(row: list[str], ci: int, widths: list[int], font: CellFont) -> int:
    """셀의 예상 줄 수. 줄(개행)마다 셀 안 폭에 담기는 글자 수로 접힘을 센다.
    실제 줄 수보다 적게 세면 한/글과 Word가 행을 늘려 맞추고 많게 세면 빈 줄 높이가 남으므로 실제 글자 폭으로 센다."""
    inner = sum(widths[ci:ci + h_span(row, ci)]) - 2 * C.CELL_MARGIN_LR
    per_line = max(inner / font.unit_w, 1)
    return sum(max(1, math.ceil(round(font.line_units(ln.strip()), 6) / int(per_line))) for ln in row[ci].split("\n"))


def row_height(lines: int) -> int:
    """예상 줄 수에 맞는 행 최소 높이 (HWPUNIT)"""
    return C.ROW_BASE_H + C.ROW_LINE_H * (lines - 1)


def row_line_counts(rows: list[list[str]], widths: list[int], font: CellFont,
                    vspans: list[tuple[int, int, int]], hdr: int) -> list[int]:
    """행마다 예상 줄 수. 행의 줄 수는 세로 병합에 속하지 않은 셀 가운데 가장 많은 줄 수.
    세로 병합 셀은 병합 구간 행 높이의 합으로 담고 모자라는 줄만 구간 행에 번갈아 더한다.
    병합 셀의 줄을 첫 행에 모두 더하면 구간 행 높이가 필요 이상으로 커지고 고르지 않게 됨"""
    tops, covered = {}, set()
    for c, r0, r1 in vspans:   # 행 번호는 본문 기준이므로 머리글 행 수를 더해 절대 행으로 바꿈
        a, b = hdr + r0, hdr + r1
        tops[(a, c)] = b
        covered.update((r, c) for r in range(a + 1, b + 1))
    counts = [max((cell_lines(row, ci, widths, font) for ci, v in enumerate(row)
                   if v.strip() not in MERGE_MARKS and (ri, ci) not in tops and (ri, ci) not in covered), default=1)
              for ri, row in enumerate(rows)]
    for (a, c), b in tops.items():
        need = row_height(cell_lines(rows[a], c, widths, font))
        span = range(a, b + 1)
        k = 0
        while sum(row_height(counts[r]) for r in span) < need:
            counts[span[k % len(span)]] += 1
            k += 1
    return counts


def header_rows(rows: list[list[str]]) -> int:
    """머리글 행 수. 첫 행 다음에 '^'로 위 머리글과 병합하는 행이 이어지면 다단 머리글."""
    n = 1
    while n < len(rows) and any(v.strip() == "^" for v in rows[n]) and not any(
            is_numeric_cell(v) for v in rows[n] if v.strip() and v.strip() not in ("^", "<")):
        n += 1
    return n


def merge_spans(rows: list[list[str]], mode: str, hdr: int = 1) -> list[tuple[int, int, int]]:
    """세로 병합 구간 (col, start_row, end_row). 본문 행 기준이며 머리글 행은 음수 오프셋으로 표기.
    auto: 선행 라벨 열(첫 숫자 열 앞, 최대 MERGE_LABEL_COLS)의 연속 동일값 병합.
    라벨 열은 상위 라벨 열의 병합 구간 안에서만 병합한다. 셀 값 '^'는 모든 열에서 위 셀과 병합 지시."""
    body = rows[hdr:]
    ncol = len(rows[0])
    spans: list[tuple[int, int, int]] = []
    for c in range(ncol):
        k = 0
        while k + 1 < hdr and rows[k + 1][c].strip() == "^":
            k += 1
        if k:
            spans.append((c, -hdr, -hdr + k))
    if not body:
        return spans
    label_cols = []
    if mode == "auto":
        for c in range(min(ncol, C.MERGE_LABEL_COLS)):
            vals = [r[c].strip() for r in body if r[c].strip() and r[c].strip() not in ("^", "<")]
            if vals and all(is_numeric_cell(v) for v in vals):
                break
            label_cols.append(c)
    whole = [(0, len(body) - 1)]
    parent_bounds = whole
    for c in range(ncol):
        explicit = any(r[c].strip() == "^" for r in body)
        if c not in label_cols and not explicit:
            continue
        # 라벨 열은 상위 라벨 열의 구간 안에서만 병합. 라벨 열 밖의 '^'는 원고가 지시한 병합이므로 표 전체 범위에서 적용
        bounds = parent_bounds if c in label_cols else whole
        new_bounds = []
        for lo, hi in bounds:
            start = lo
            for i in range(lo + 1, hi + 2):
                same = i <= hi and (body[i][c].strip() == "^" or
                                    (c in label_cols and body[i][c].strip() == body[start][c].strip() and body[start][c].strip()))
                if not same:
                    if i - 1 > start:
                        spans.append((c, start, i - 1))
                    new_bounds.append((start, i - 1))
                    start = i
        if c in label_cols:
            parent_bounds = new_bounds
    return spans


def hmerge_spans(rows: list[list[str]]) -> list[tuple[int, int, int]]:
    """가로 병합 구간 (row, start_col, end_col). 셀 값 '<'는 왼쪽 셀과 병합 지시. 머리글 행 포함."""
    spans = []
    for ri, r in enumerate(rows):
        c = 0
        while c < len(r):
            if r[c].strip() == "<":
                c += 1
                continue
            end = c
            while end + 1 < len(r) and r[end + 1].strip() == "<":
                end += 1
            if end > c:
                spans.append((ri, c, end))
            c = end + 1
    return spans


def col_aligns(rows: list[list[str]], explicit: list, hdr: int = 1) -> list[str]:
    """정렬 결정 단위는 열. 명시 마커 > 글머리 포함 LEFT > CENTER.
    판정 대상은 머리글 행(hdr개)을 뺀 본문 셀이며 병합 지시 셀은 내용이 없으므로 제외.
    Why: 열 정렬은 표 안에서 열이 하는 역할로 정해짐. 셀 글자의 숫자 모양(연도 2005, 금액 2,005)과 글자 수로는 역할을 구분할 수 없음.
    수량 열의 RIGHT와 서술형 설명 열의 LEFT는 표 전체를 보는 원고 작성자가 마커로 지정"""
    ncol = max(len(r) for r in rows)
    out = []
    for c in range(ncol):
        body = [r[c] for r in rows[hdr:] if c < len(r) and r[c].strip() and r[c].strip() not in MERGE_MARKS]
        if c < len(explicit) and explicit[c]:
            out.append(explicit[c])
        elif any(v.lstrip().startswith(BULLET_PREFIXES) for v in body):
            out.append("LEFT")
        else:
            out.append("CENTER")
    return out


def table_plan(e: Element, merge_mode: str) -> dict:
    """표 하나의 조판 계획. HWPX와 DOCX가 같은 병합, 정렬, 머리글 판정을 쓰도록 한곳에서 계산."""
    rows = pad_rows(e.data["rows"])
    hdr = header_rows(rows)
    vspans = merge_spans(rows, merge_mode, hdr) if merge_mode != "none" else []
    vcells = {(r, c) for c, r0, r1 in vspans for r in range(r0, r1 + 1)}
    hspans, skipped = [], []
    if merge_mode != "none":
        for ri, c0, c1 in hmerge_spans(rows):
            if any((ri - hdr, c) in vcells for c in range(c0, c1 + 1)):
                skipped.append((ri, c0, c1))
            else:
                hspans.append((ri, c0, c1))
    return {"rows": rows, "hdr": hdr, "aligns": col_aligns(rows, e.data["aligns"], hdr),
            "vspans": vspans, "hspans": hspans, "skipped": skipped}


def split_long_table(e: Element) -> list[Element]:
    """장표를 제목행을 반복한 청크 표로 나눈다 (--long-table split)"""
    rows = pad_rows(e.data["rows"])
    step = C.LONG_TABLE_ROWS - 1
    chunks = [rows[i:i + step] for i in range(1, len(rows), step)]
    return [Element("table", f"{e.text} ({k})" if e.text else "",
                    data={**e.data, "rows": [rows[0]] + chunk, "split_done": True})
            for k, chunk in enumerate(chunks, 1)]


# ── 그림 ──────────────────────────────────────────────────────────────────────
def load_image(e: Element) -> tuple[bytes, str, tuple[float, float]] | None:
    """그림 원본을 읽는다. URL이면 내려받는다.
    반환: (바이트, 형식, 조판 크기 mm) 또는 None(파일 없음). 크기는 형식 변환 전 원본 기준"""
    path = e.data["path"]
    if path.startswith(("http://", "https://")):
        req = urllib.request.Request(path, headers={"User-Agent": C.HTTP_USER_AGENT})
        with urllib.request.urlopen(req, timeout=C.IMG_URL_TIMEOUT) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "").split(";")[0].strip()
        fmt = C.IMAGE_MIME_EXT.get(ctype) or os.path.splitext(path)[1].lstrip(".").lower() or "png"
    else:
        if not os.path.isabs(path):
            path = os.path.join(e.data["base"], path)
        if not os.path.exists(path):
            print(msg("warn_image_missing", path=path))
            return None
        data = Path(path).read_bytes()
        fmt = os.path.splitext(path)[1].lstrip(".").lower() or "png"
    if fmt == "jpeg":
        fmt = "jpg"
    size = image_size_mm(data)
    if fmt in C.IMAGE_CONVERT_TO_JPG:   # 한/글과 Word가 열지 못하는 형식은 JPG로 변환
        from PIL import Image
        buf = io.BytesIO()
        Image.open(io.BytesIO(data)).convert("RGB").save(buf, "JPEG", quality=C.JPEG_QUALITY)
        data, fmt = buf.getvalue(), "jpg"
    return data, fmt, size


def image_size_mm(data: bytes) -> tuple[float, float]:
    """그림 크기 규범: 가로형은 폭, 정사각형 근방은 폭, 세로형은 높이로 상한을 둔다"""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        px_w, px_h = im.size
        dpi = im.info.get("dpi", (C.IMG_DEFAULT_DPI, C.IMG_DEFAULT_DPI))[0] or C.IMG_DEFAULT_DPI
    except Exception:
        px_w, px_h, dpi = C.IMG_FALLBACK_PX[0], C.IMG_FALLBACK_PX[1], C.IMG_DEFAULT_DPI
    w_mm, h_mm = px_w / dpi * 25.4, px_h / dpi * 25.4
    ratio = w_mm / h_mm
    if ratio >= C.IMG_LANDSCAPE_RATIO:
        scale = C.IMG_LANDSCAPE_W_MM / w_mm
    elif ratio > C.IMG_PORTRAIT_RATIO:
        scale = C.IMG_SQUARE_W_MM / w_mm
    else:
        scale = C.IMG_PORTRAIT_H_MM / h_mm
    return round(w_mm * scale, 1), round(h_mm * scale, 1)


# ── 인라인 서식 ───────────────────────────────────────────────────────────────
def inline_segments(text: str) -> list[tuple[str, str]]:
    """인라인 서식을 (종류, 문자열) 목록으로 나눈다.
    종류: plain, bold, italic, code, sup, sub, footnote(각주 키)"""
    out = []
    for seg in INLINE_RE.split(text):
        if not seg:
            continue
        if seg.startswith("**"):
            out.append(("bold", seg[2:-2]))
        elif seg.startswith("*"):
            out.append(("italic", seg[1:-1]))
        elif seg.startswith("`"):
            out.append(("code", seg[1:-1]))
        elif seg.startswith("<sup>"):
            out.append(("sup", seg[5:-6]))
        elif seg.startswith("^"):
            out.append(("sup", seg[1:-1]))
        elif seg.startswith("<sub>"):
            out.append(("sub", seg[5:-6]))
        elif seg.startswith("[^"):
            out.append(("footnote", seg[2:-1]))
        else:
            out.append(("plain", seg))
    return out


def toc_entries(headings: list[tuple[int, str]], depth: int) -> list[tuple[int, str]]:
    """목차에 싣는 제목 (문서 순서). 목차 쪽번호는 이 목록의 순번으로 대응한다 (같은 문구의 제목이 여럿이어도 섞이지 않음)."""
    return [(lv, text) for lv, text in headings if lv <= depth]


def toc_first_lines(elems: list[Element], depth: int) -> list[str | None]:
    """목차 항목마다 뒤따르는 첫 본문 줄의 출력 글자 (toc_entries 순서). 한/글은 제목부터 첫 본문 줄까지를 한 쪽에 묶으므로
    사이의 하위 제목과 □는 건너뜀. 표와 그림은 캡션으로 찾고 찾을 글자가 없거나 쪽 나눔이 끼면 None"""
    out = []
    for i, e in enumerate(elems):
        if e.kind != "heading" or e.level > depth:
            continue
        first = None
        for nx in elems[i + 1:]:
            if nx.kind in ("heading", "square"):
                continue
            if nx.kind in BODY_KINDS or nx.kind == "source":
                first = shown_text(nx.text)
            elif nx.kind in ("table", "image"):
                first = nx.text or None
            break
        out.append(first)
    return out


def heading_label(profile: dict, counters: dict, level: int, text: str) -> str:
    """헤더 문구에 번호를 붙인다. 번호는 Numbering이 갱신한다."""
    manual = profile["numbering"] == "manual"
    ch = max(counters["chapter"], 1)
    if level == 1:
        return profile["chapter_format"].format(n=counters["chapter"], t=text)
    if level == 2:
        return profile["section_format"].format(c=ch, s=counters["section"], t=text) if manual else text
    if level == 3:
        return profile["subsection_format"].format(c=ch, s=max(counters["section"], 1),
                                                   ss=counters["subsection"], t=text) if manual else text
    letters = C.label("letters.items")
    return f"{C.label('letters.format').format(x=letters[(counters['ganada'] - 1) % len(letters)])} {text}"


class Numbering:
    """장, 절, 소절, 가나다 번호와 쪽 나눔 판정. HWPX와 DOCX가 같은 규칙을 쓴다."""

    def __init__(self, page_break: str):
        self.page_break = page_break   # chapter | section | none
        self.n = {"chapter": 0, "section": 0, "subsection": 0, "ganada": 0, "total_section": 0}

    def advance(self, level: int) -> bool:
        """번호를 올리고 이 헤더 앞에서 새 쪽을 시작할지 반환"""
        n = self.n
        brk = False
        if level == 1:
            n.update(chapter=n["chapter"] + 1, section=0, subsection=0, ganada=0)
            brk = self.page_break in ("chapter", "section") and n["chapter"] > 1
        elif level == 2:
            n.update(section=n["section"] + 1, subsection=0, ganada=0)
            # 절 단위 나눔: 장 직후 첫 절과 문서 첫 절은 이미 새 쪽이므로 제외
            brk = self.page_break == "section" and not (n["section"] == 1 and n["chapter"] > 0) and n["total_section"] > 0
            n["total_section"] += 1
        elif level == 3:
            n.update(subsection=n["subsection"] + 1, ganada=0)
        else:
            n["ganada"] += 1
        return brk
