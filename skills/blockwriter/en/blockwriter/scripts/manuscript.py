"""Turns a Markdown manuscript into a list of elements and does the format-independent typesetting calculations (table column widths, alignment, merging, figure size).
Both the HWPX and DOCX typesetters use the results of this module."""
from __future__ import annotations

import copy
import dataclasses
import io
import math
import os
import re
import sys
import unicodedata
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import config as C
from config import msg


@dataclass
class Element:
    kind: str                # heading square circle dash dot note unit colwidth source table table_caption image pagebreak fit
    text: str = ""
    level: int = 0           # heading: 1-4
    data: dict = field(default_factory=dict)


HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
TABLE_SEP_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$")
COL_WIDTH_SEP_RE = re.compile(r"[,，\s]+")
FOOTNOTE_DEF_RE = re.compile(r"^\[\^([^\]]+)\]:\s*(.*)$")
# Emphasis is recognized only when both inner ends are non-space characters and no asterisk follows on the outside
# Why: tells literal asterisks such as a significance legend ('*p<0.05, **p<0.01') apart from emphasis marks
EMPHASIS_RE = r"(?<!\*){mark}[^*\s](?:[^*]*[^*\s])?{mark}(?!\*)"
INLINE_RE = re.compile("(" + "|".join(EMPHASIS_RE.format(mark=m) for m in (r"\*{3}", r"\*\*", r"\*"))
                       + r"|`[^`]+`|<sup>.*?</sup>|<sub>.*?</sub>|\^[^^\s]+\^|\[\^[^\]]+\])")
SQUARE_MARK = ("□", "■", "☐")
CIRCLE_MARK = ("○", "❍", "◦", "ㅇ")
NOTE_MARK = ("※", "* ")   # a '*' note needs a space after it. Lines starting with '*italic*' or '**bold**' are statements
MERGE_MARKS = ("^", "<")  # merge directive cells. They hold no content, so width, line count, and alignment decisions skip them
NUMERIC_CELL = re.compile(r"^[-+±(]?[\d,]+(?:\.\d+)?%?\)?$")
BULLET_PREFIXES = ("·", "•", "ㆍ", "∙", "○", "◦", "❍", "□", "■", "※", "- ", "▪")
CELL_BULLET_MARKS = ("◦", "○", "ㅇ", "·", "•", "ㆍ")   # line-start marks that become the cell ◦ bullet style
CELL_MARK_RE = re.compile(r"^\s*[◦○ㅇ·•ㆍ-]\s*")        # leading mark and following spaces removed from cell bullet lines


def _alt(tokens) -> str:
    """Regex alternation of manuscript tokens. A space inside a token matches any spacing ('열 폭' also matches '열폭')"""
    return "|".join(r"\s*".join(re.escape(w) for w in t.split()) for t in tokens)


def _format_re(fmt: str, fields: dict[str, str]) -> str | None:
    """Pattern of the number written by a label format ('Chapter {n}. ' → 'Chapter\\s*\\d+\\s*\\.'). None when the format writes no number"""
    parts = re.split(r"\{(\w+)\}", fmt)   # literal, field, literal, field, ...
    if not any(parts[1::2]):
        return None
    words = [p for i, part in enumerate(parts)
             for p in ([fields[part]] if i % 2 else [re.escape(w) for w in part.split()])]
    return r"\s*".join(words)


def compile_notation():
    """Builds the manuscript notation patterns from the active labels (built-in tokens plus those added by a label file).
    build calls it again after reading a label file. Heading numbers written in a label file's number format are removed like 제N장 and 가."""
    global CAPTION_RE, FIG_CAPTION_RE, UNIT_RE, COL_WIDTH_RE, SOURCE_RE, SOURCE_PAREN_RE, NUM_PREFIX_RE, FIT_RE
    src = C.label("notation.source")
    paren = [t for t in src if t in C.SOURCE_PAREN_TOKENS or t not in C.LABEL_DEFAULTS["notation"]["source"]]
    CAPTION_RE = re.compile(rf"^[<＜]\s*(?:{_alt(C.label('notation.table'))})\s*[^>＞]*[>＞]\s*(.*)$")
    FIG_CAPTION_RE = re.compile(rf"^\[\s*(?:{_alt(C.label('notation.figure'))})\s*[^\]]*\]\s*(.*)$")
    UNIT_RE = re.compile(rf"^\(\s*(?:{_alt(C.label('notation.unit'))})\s*[:：].*\)$")
    COL_WIDTH_RE = re.compile(rf"^\(\s*(?:{_alt(C.label('notation.colwidth'))})\s*[:：]\s*(.*)\)$")
    FIT_RE = re.compile(rf"^\(\s*(?:{_alt(C.label('notation.fit'))})\s*({_alt(C.FIT_RANGE_WORDS)})?\s*(?:[:：]\s*(.*))?\)$")
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
    # bullet levels are ranked by indent width (the width values themselves differ between manuscripts)
    indents = sorted({len(m.group(1).expandtabs(4)) for ln in lines if (m := BULLET_RE.match(ln))})
    elems: list[Element] = []
    i = 0
    blank = False   # whether the previous line was blank. A ※ line after a table or figure is not attached to the block if separated by a blank line
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
        if m := FIT_RE.match(stripped):
            elems.append(Element("fit", stripped, data={"range": C.FIT_RANGE_WORDS.get(m.group(1)), "spec": m.group(2) or ""}))
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
            # a unit line written after a blank line, directly above the next table's caption, is that table's before-caption unit line, so it is left for the next table to absorb
            opens_next = blank and i + 1 < len(lines) and _opens_table(lines[i + 1])
            if i < len(lines) and UNIT_RE.match(lines[i].strip()) and not tbl.data.get("unit") and not opens_next:
                tbl.data["unit"] = lines[i].strip()   # a unit line written after the table also becomes the unit row above the table
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
        if stripped.startswith(">"):   # quote lines get their role from their content (source if it is a source notation, otherwise a note)
            body = stripped.lstrip("> ").strip()
            if SOURCE_RE.match(body):
                body, i = _read_source(lines, i, body)
                elems.append(Element("source", SOURCE_PAREN_RE.sub(r"\1: ", body), data={"gap": gap}))
            else:   # store '> ※ text' without the symbol, the same as '※ text' (avoids a doubled symbol in body notes)
                t = _strip_marker(body, NOTE_MARK)
                elems.append(Element("note", body if t is None else t,
                                     data={"gap": gap, "mark": "※" if t is None else body[0]}))
            continue
        if SOURCE_RE.match(stripped):
            stripped, i = _read_source(lines, i, stripped)
            elems.append(Element("source", SOURCE_PAREN_RE.sub(r"\1: ", stripped)))
            continue
        if (t := _strip_marker(stripped, SQUARE_MARK)) is not None:
            elems.append(Element("square", t))
            continue
        if (t := _strip_marker(stripped, NOTE_MARK)) is not None:
            if SOURCE_RE.match(t):
                t, i = _read_source(lines, i, t)
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
        elems.append(Element("circle", stripped))   # a plain paragraph without a symbol is a ○ statement
    return _apply_fit(elems), footnotes


def _read_source(lines: list[str], i: int, first: str) -> tuple[str, int]:
    """Reads the lines after a source line that ends with the source separator as lines of the same source row. Line boundaries stay as '\\n'"""
    parts = [first]
    while parts[-1].endswith(C.SOURCE_SEP) and i < len(lines) and _is_source_tail(lines[i]):
        parts.append(lines[i].strip().lstrip("> ").strip())
        i += 1
    return "\n".join(parts), i


def _is_source_tail(line: str) -> bool:
    """A line that can continue a source row. Blank lines and lines that start with another manuscript notation are excluded"""
    s = line.strip().lstrip("> ").strip()
    if not s or s == "---" or s.startswith(("|", "#", "!")) or BULLET_RE.match(line):
        return False
    if _strip_marker(s, SQUARE_MARK + CIRCLE_MARK + NOTE_MARK) is not None:
        return False
    return not any(rx.match(s) for rx in (SOURCE_RE, UNIT_RE, CAPTION_RE, FIG_CAPTION_RE, COL_WIDTH_RE, FIT_RE, FOOTNOTE_DEF_RE))


SOURCE_SPLIT_RE = re.compile(rf"(?<={re.escape(C.SOURCE_SEP)})\s+")   # spaces and line boundaries after the source separator


def source_lines(text: str, layout: str) -> list[str]:
    """Typeset lines of a source row. auto keeps the manuscript lines, break gives one line per source, inline joins them into one line"""
    if layout == "break":
        return SOURCE_SPLIT_RE.split(text)
    lines = text.split("\n")
    return lines if layout == "auto" else [" ".join(lines)]


def source_label(text: str) -> tuple[str, str]:
    """Splits a source row text into the source label ('자료:') and the text after it. Without a label, the label is an empty string"""
    m = SOURCE_RE.match(text)
    return (m.group(0), text[m.end():].lstrip(" ")) if m else ("", text)


FIT_ITEM_RE = re.compile(r"^(.+?)\s*([+-]?\d+(?:\.\d+)?)\s*(?:%p|%)?$")   # one item of an adjustment line ('장평 -3')


def parse_fit(spec: str) -> tuple[dict[str, float], list[str]]:
    """Reads the values of an adjustment line as {item: change}. Pieces it cannot read are returned separately"""
    vals: dict[str, float] = {}
    bad: list[str] = []
    for piece in filter(None, (s.strip() for s in re.split(r"[,，]", spec))):
        m = FIT_ITEM_RE.match(piece)
        key = C.FIT_KEYS.get(re.sub(r"\s+", "", m.group(1)).lower()) if m else None
        if key is None:
            bad.append(piece)
        else:
            vals[key] = float(m.group(2))
    return vals, bad


def _apply_fit(elems: list[Element]) -> list[Element]:
    """Moves adjustment lines into data['fit'] of their target elements and drops them from the element list. A single line targets the next element, a begin line targets the elements up to the end line.
    Unreadable values and unpaired begin or end lines are kept in data['fit_issues'] of the following element for lint to report"""
    out: list[Element] = []
    once = ranged = None
    issues: list[str] = []
    for e in elems:
        if e.kind != "fit":
            fit = {**(ranged or {}), **(once or {})}
            if fit:
                e.data["fit"] = fit
            if issues:
                e.data["fit_issues"], issues = issues, []
            once = None
            out.append(e)
            continue
        vals, bad = parse_fit(e.data["spec"])
        issues += [msg("lint_fit_value", text=e.text, piece=p) for p in bad]
        if e.data["range"] == "end":
            if ranged is None:
                issues.append(msg("lint_fit_no_begin", text=e.text))
            ranged = None
        elif e.data["range"] == "begin":
            ranged = vals
        else:
            once = vals
    if ranged is not None:
        issues.append(msg("lint_fit_no_end"))
    if issues and out:
        out[-1].data.setdefault("fit_issues", []).extend(issues)
    return out


def fit_value(key: str, base: float, fit: dict | None) -> float:
    """A style value plus the adjustment change (ratio, spacing, line spacing), limited to the range Hangul accepts"""
    low, high = C.FIT_BOUNDS[key]
    return min(high, max(low, base + (fit or {}).get(key, 0)))


def fit_line_scale(base: float | None, fit: dict | None) -> float:
    """Scale that a line spacing adjustment gives to the line height. Multiplied into the minimum table row height"""
    return fit_value("line", base, fit) / base if base and (fit or {}).get("line") else 1.0


def _opens_table(line: str) -> bool:
    """A line that opens a table block (caption line, column width line, table row)"""
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
    # absorb the caption, unit line, and column width line among the three elements right before the table, in any order
    found = {"table_caption": None, "unit": None, "colwidth": None}
    for k in range(len(elems) - 1, max(len(elems) - 1 - len(found), -1), -1):
        kind = elems[k].kind
        if kind in found and found[kind] is None:
            found[kind] = elems.pop(k).text
        else:
            break
    return Element("table", found["table_caption"] or "",
                   data={"rows": cells, "aligns": aligns, "unit": found["unit"], "colwidth": found["colwidth"]})


def attach_block_notes(elems: list[Element], source_layout: str = C.DEFAULT_SOURCE_LAYOUT) -> list[Element]:
    """Attaches ※, *, and source lines right after tables and figures as source rows at the bottom of the block, and moves a unit line after a table up to the unit row.
    ※ and * lines written after a blank line are not attached to the block and stay as body notes."""
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
                if nx.kind == "note":   # keep the note symbol in source rows so notes differ from source lines. A '※ 출처:' line stays a source line
                    srcs.append("\n".join(source_lines(nx.text, source_layout)) if SOURCE_RE.match(nx.text)
                                else f"{nx.data.get('mark', '※')} {nx.text}")
                elif nx.kind == "source":
                    srcs.append("\n".join(source_lines(nx.text, source_layout)))
                elif nx.kind == "unit" and e.kind == "table" and not e.data.get("unit"):
                    e.data["unit"] = nx.text
                else:
                    break
                consumed += 1
            e.data["sources"] = srcs
            skip = consumed
        elif e.kind == "source":   # a source line after body text moves into a footnote, so its lines are joined
            e.text = " ".join(e.text.split("\n"))
        out.append(e)
    return out


# ── Manuscript lint: reports manuscript defects before typesetting (conversion continues) ─────────────────
GANADA_LEVEL = 4   # 가나다 is optional grouping, so it may sit right under a section or a subsection
BODY_KINDS = ("square", "circle", "dash", "dot", "note")   # body paragraphs where the writers process footnote references


def lint(elems: list[Element], footnotes: dict | None = None) -> list[str]:
    """Defects that are resolved by fixing the manuscript"""
    issues = []
    prev_level = 0
    for idx, e in enumerate(elems):
        issues += e.data.get("fit_issues", [])
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
        if e.kind == "colwidth":   # a column width line not absorbed by a table is not used in typesetting
            issues.append(msg("lint_colwidth_alone", text=e.text[:30]))
    return issues + _lint_attached(elems, footnotes or {})


def _lint_attached(elems: list[Element], footnotes: dict) -> list[str]:
    """Defects judged on the element order after attaching notes to tables and figures (footnote references, source line position).
    attach_block_notes modifies elements, so it runs on a copy and the manuscript the writers receive stays unchanged"""
    issues, refs, has_para = [], [], False
    for e in attach_block_notes(copy.deepcopy(elems)):
        if e.kind == "heading":   # the writers cut the previous-paragraph link at headings
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
    """Reports typesetting choices for the user (page breaks, long tables) regardless of the manuscript. Items already chosen by option are left out"""
    notices = []
    sec_sizes, cur, cur_level = [], None, 0
    for e in elems:
        if e.kind == "heading" and e.level <= 2:
            # a chapter or document title followed directly by a lower heading shares the page with that section, so it is not counted
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


# ── Table calculations (HWPUNIT; the DOCX typesetter converts them) ─────────────────────────
def shown_text(text: str) -> str:
    """Displayed text without inline format markup (bold, italic, super/subscript marks) and footnote references"""
    return "".join(seg for kind, seg in inline_segments(text) if kind != "footnote")


def is_numeric_cell(text: str) -> bool:
    """Whether a cell is numeric, judged on its displayed text. A formatted number such as `**5**` counts as numeric"""
    return bool(NUMERIC_CELL.match(shown_text(text).replace(" ", "")))


def char_units(ch: str, space_em: float, ratio: float, spacing: float) -> float:
    """Width of one character (half a Hangul character = 1). Spaces use the width of the format; Latin letters, digits, and symbols use NanumGothic widths per character (GLYPH_EM).
    The space width differs between Hangul and Word (HWPX 0.5em, DOCX 0.28em), so the calling format passes it.
    The width ratio (%) multiplies the glyph width and letter spacing (%) is added per character, so narrow Latin letters shrink more relative to half a Hangul character"""
    if ch == " ":
        em = space_em
    elif ch in C.GLYPH_EM:
        em = C.GLYPH_EM[ch]
    elif unicodedata.east_asian_width(ch) in ("W", "F"):
        return C.WIDE_UNITS
    else:
        return C.OTHER_UNITS
    return (em * ratio + spacing) / ((C.CELL_HANGUL_EM * ratio + spacing) / 2)


NUMBERED_SQUARE_RE = re.compile(r"^(\d+)\.(\s+)")   # the '1. title' line of --numbered-square


def number_prefix_em(text: str, space_em: float) -> float:
    """Width of the number, period, and following spaces of a '1. title' line (multiple of the font size). The hanging indent width that aligns the second line with the text after the number"""
    m = NUMBERED_SQUARE_RE.match(text)
    if m is None:
        return 0.0
    return sum(C.GLYPH_EM[d] for d in m.group(1)) + C.GLYPH_EM["."] + len(m.group(2)) * space_em


def text_units(text: str, space_em: float = C.SPACE_EM_HWPX, ratio: float = 100, spacing: float = 0) -> float:
    """Sum of the printed character widths (in half-Hangul units, inline format markup excluded)"""
    return sum(char_units(ch, space_em, ratio, spacing) for ch in shown_text(text))


def weighted_len(text: str, space_em: float = C.SPACE_EM_HWPX, ratio: float = 100, spacing: float = 0) -> int:
    """Rounded-up sum of character widths. Used for checks where text must not overflow, such as line counts and alignment"""
    return math.ceil(round(text_units(text, space_em, ratio, spacing), 6))   # round first so accumulated decimal error does not push the result up by 1


def pad_rows(rows: list[list[str]]) -> list[list[str]]:
    width = max(len(r) for r in rows)
    return [r + [""] * (width - len(r)) for r in rows]


def col_line_widths(rows: list[list[str]], font: CellFont) -> list[float]:
    """Width of the longest line in each column (HWPUNIT). Computed in one place so automatic sizing and the no-wrap width use the same character widths"""
    ncol = max(len(r) for r in rows)
    line_w = [0.0] * ncol   # not rounded up, so a space's fractional excess does not widen a column
    for r in rows:
        for c, cell in enumerate(r):
            if cell.strip() in MERGE_MARKS:
                continue
            span = h_span(r, c)   # the text of a cell merged horizontally with '<' is shared by the merged columns
            for ln in cell.split("\n"):
                share = font.line_units(ln.strip()) * font.unit_w / span
                for k in range(c, c + span):
                    line_w[k] = max(line_w[k], share)
    return line_w


def col_need_widths(line_w: list[float]) -> list[int]:
    """Column need widths: line width plus column padding, with the minimum width guaranteed (HWPUNIT).
    Given the longest line widths as they are, the result is the no-wrap width, where every line of the column fits on one line"""
    return [max(round(w) + C.COL_PAD_W, C.COL_MIN_W) for w in line_w]


def calc_col_widths(rows: list[list[str]], max_w: int, font: CellFont) -> list[int]:
    """Compute column widths from the real character widths of the table body style and fit them between the cap and floor. The sum is the table width.
    A fixed, generous character width adds slack to every column, so even tables with little information widen to the cap and go past the ○ level"""
    ncol = max(len(r) for r in rows)
    line_w = col_line_widths(rows, font)
    # the one-line width is a physical width independent of font size. Names and short phrases within it do not wrap; only wider columns wrap to two lines
    eff = [w if w <= C.COL_ONE_LINE_W else max(C.COL_ONE_LINE_W, w * C.COL_WRAP_RATIO) for w in line_w]
    need = col_need_widths(eff)
    total = sum(need)
    floor_w = int(max_w * C.TABLE_MIN_RATIO)
    if total > max_w:
        # short label columns at or below the equal share keep their required width; the other columns shrink in proportion to their required widths.
        # Proportional shrinking gives those columns similar wrap ratios, so row heights stay even. Recomputing the share repeatedly lets middle columns fit within it
        # and keep their full width, while only the longest column shrinks sharply and its cells wrap to many lines
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


def fixed_col_widths(spec: str | None, ncol: int, max_w: int, title: str, nowrap_pct: float) -> list[int] | None:
    """Convert the manuscript column width line (each column as % of the table width cap) to column widths. The sum of the values is the table width.
    It is a manual setting for tables that automatic sizing does not suit, so the given values are used without the floor adjustment.
    Returns None when there is no setting. When the values do not fit, prints a WARN and returns None so the table uses automatic sizing.
    When the sum exceeds the no-wrap width (nowrap_pct, %) by the tolerance or more, prints a WARN only and uses the given values"""
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
    # width beyond the no-wrap width does not reduce line count and only widens the table. It may be a width the user asked for, so the given values stay
    if round(total - nowrap_pct, C.COL_WIDTH_PCT_DIGITS) >= C.COL_WIDTH_NOWRAP_TOL:
        print(msg("warn_colwidth_nowrap", title=title or "-", total=f"{total:g}",
                  nowrap=pct_text([nowrap_pct]), tol=C.COL_WIDTH_NOWRAP_TOL))
    widths = [int(max_w * v / C.COL_WIDTH_PCT_MAX) for v in values]
    widths[-1] += round(max_w * total / C.COL_WIDTH_PCT_MAX) - sum(widths)   # the rounding remainder goes to the last column
    return widths


def width_pct(w: float, max_w: int) -> float:
    """A width (HWPUNIT) in the unit of the column width line (% of the table width cap). Rounded to the printed digits so decisions follow the printed values"""
    return round(w * C.COL_WIDTH_PCT_MAX / max_w, C.COL_WIDTH_PCT_DIGITS)


def pct_text(values: list[float]) -> str:
    """A list of % values as text that can be copied into a column width line ('9.18, 12.98')"""
    return ", ".join(f"{v:.{C.COL_WIDTH_PCT_DIGITS}f}" for v in values)


def table_col_widths(rows: list[list[str]], spec: str | None, max_w: int, font: CellFont, title: str) -> list[int]:
    """Column widths of a table. The column width line when present, otherwise (or when it does not fit) automatic sizing.
    For tables whose cells wrap and tables with a column width line, prints the current width and the no-wrap width as INFO.
    Setting column width lines from these values instead of eyeballing the render PNG prevents tables widened more than needed"""
    nowrap = col_need_widths(col_line_widths(rows, font))   # width where the longest line of each column fits on one line
    nowrap_pct = width_pct(sum(nowrap), max_w)
    widths = (fixed_col_widths(spec, len(nowrap), max_w, title, nowrap_pct)
              or calc_col_widths(rows, max_w, font))
    if spec or any(w < n for w, n in zip(widths, nowrap)):
        print(msg("info_colwidth", title=title or "-",
                  cur=pct_text([width_pct(sum(widths), max_w)]), cur_cols=pct_text([width_pct(w, max_w) for w in widths]),
                  nowrap=pct_text([nowrap_pct]), nowrap_cols=pct_text([width_pct(w, max_w) for w in nowrap])))
    return widths


def h_span(row: list[str], c: int) -> int:
    """Number of columns the cell in column c spans through '<' cells to its right (1 if not merged)"""
    n = 1
    while c + n < len(row) and row[c + n].strip() == "<":
        n += 1
    return n


def bullet_head_hu(char: str, size_hu: float, offset_pct: float, adjust_hu: float) -> float:
    """Bullet symbol width + gap after the symbol + width adjustment (HWPUNIT). Only half-width characters (such as hyphens) count as half width"""
    half = unicodedata.east_asian_width(char) in ("Na", "H")
    width = C.DOCX_HALFWIDTH_BULLET if half else C.DOCX_FULLWIDTH_BULLET
    return size_hu * width + size_hu * offset_pct / 100 + adjust_hu


@dataclass(frozen=True)
class LineStyle:
    """Character shape and line lead of a paragraph style inside a cell. Size and lead in HWPUNIT, width ratio and letter spacing in %.
    The lead is the paragraph's left and right margins plus the width taken by the bullet symbol"""
    size_hu: float
    ratio: float
    spacing: float
    lead_hu: float = 0

    @property
    def unit_w(self) -> float:
        """Width of one weighted unit (half a Hangul character) of cell text. One Hangul character is the font size x the font's Hangul width ratio x the width ratio, plus the character spacing"""
        return self.size_hu * (C.CELL_HANGUL_EM * self.ratio + self.spacing) / 100 / 2

    def fitted(self, fit: dict | None) -> "LineStyle":
        """Line style with the ratio and spacing adjustment added (for column widths and line counts)"""
        if not fit:
            return self
        return dataclasses.replace(self, ratio=fit_value("ratio", self.ratio, fit), spacing=fit_value("spacing", self.spacing, fit))

    def label_hang_hu(self, label: str, space_em: float) -> int:
        """Hanging indent width: the source label width plus the gap after it (HWPUNIT). It aligns the second line of a source row with the start of the first source.
        A tab puts the first source at the same position, so the gap after the label absorbs glyph width differences between fonts"""
        return math.ceil(self.text_hu(label, space_em) - self.lead_hu + self.size_hu * C.SOURCE_LABEL_GAP_EM)

    def text_hu(self, text: str, space_em: float) -> float:
        """Width of text printed in this style plus the line lead (HWPUNIT)"""
        return text_units(text, space_em, self.ratio, self.spacing) * self.unit_w + self.lead_hu


@dataclass(frozen=True)
class CellFont:
    """Line styles of a table cell (for column widths and row line counts). The weighted unit follows the table body style. Space width as a multiple of the font size.
    Plain lines take the wider of the table body and table body left styles; in forms without cell bullet styles, bullet lines count as plain lines"""
    space_em: float
    plain: tuple[LineStyle, ...]
    bullet: LineStyle | None = None
    dash: LineStyle | None = None

    @property
    def unit_w(self) -> float:
        return self.plain[0].unit_w

    def line_units(self, line: str) -> float:
        """Width of one cell line (in half-Hangul units). A bullet line counts the text without its leading mark plus the symbol width and margins.
        Counting only the text leaves out cell bullet indents and in-cell paragraph margins, so columns come out too narrow and text reaches the cell border"""
        st = line.lstrip()
        if self.bullet is not None and st.startswith(CELL_BULLET_MARKS):
            hu = self.bullet.text_hu(CELL_MARK_RE.sub("", line), self.space_em)
        elif self.dash is not None and st.startswith("- "):
            hu = self.dash.text_hu(CELL_MARK_RE.sub("", line), self.space_em)
        else:
            hu = max(s.text_hu(line, self.space_em) for s in self.plain)
        return hu / self.unit_w


def cell_lines(row: list[str], ci: int, widths: list[int], font: CellFont) -> int:
    """Expected line count of a cell. Counts wrapping for each line (line break) by the number of characters that fit the cell's inner width.
    Counting fewer lines than actual makes Hangul and Word stretch the row, and counting more leaves empty line height, so the count uses actual character widths."""
    inner = sum(widths[ci:ci + h_span(row, ci)]) - 2 * C.CELL_MARGIN_LR
    per_line = max(inner / font.unit_w, 1)
    return sum(max(1, math.ceil(round(font.line_units(ln.strip()), 6) / int(per_line))) for ln in row[ci].split("\n"))


def row_height(lines: int, scale: float = 1.0) -> int:
    """Minimum row height for an expected line count (HWPUNIT)"""
    return round((C.ROW_BASE_H + C.ROW_LINE_H * (lines - 1)) * scale)


def source_row_height(lines: int, line_h: float) -> int:
    """Minimum height of a source or unit row (HWPUNIT). A broken source row grows by the style line height for each line after the first"""
    return round(C.ROW_BASE_H + line_h * (lines - 1))


def row_line_counts(rows: list[list[str]], widths: list[int], font: CellFont,
                    vspans: list[tuple[int, int, int]], hdr: int) -> list[int]:
    """Expected line count of each row. A row's line count is the most lines among its cells outside vertical merges.
    A vertically merged cell fits into the total height of the rows it spans, and only the missing lines are added to the spanned rows in turn.
    Adding all of a merged cell's lines to its first row makes the spanned rows taller than needed and uneven"""
    tops, covered = {}, set()
    for c, r0, r1 in vspans:   # row numbers are body-relative, so add the header row count to get absolute rows
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
    """Number of header rows. If rows after the first merge upward with '^', the header is multi-row."""
    n = 1
    while n < len(rows) and any(v.strip() == "^" for v in rows[n]) and not any(
            is_numeric_cell(v) for v in rows[n] if v.strip() and v.strip() not in ("^", "<")):
        n += 1
    return n


def merge_spans(rows: list[list[str]], mode: str, hdr: int = 1) -> list[tuple[int, int, int]]:
    """Vertical merge spans (col, start_row, end_row). Rows are body-relative; header rows use negative offsets.
    auto: merges consecutive equal values in leading label columns (before the first numeric column, at most MERGE_LABEL_COLS).
    A label column merges only within the merge spans of the label column above it. A cell value '^' means merge with the cell above in any column."""
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
        # a label column merges only within the spans of the label column above it. A '^' outside label columns is a merge the manuscript requested, so it applies across the whole table
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
    """Horizontal merge spans (row, start_col, end_col). A cell value '<' is a directive to merge with the cell on the left. Includes header rows."""
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
    """Alignment is decided per column. Explicit marker > LEFT if bullets > CENTER.
    Only body cells below the hdr header rows are judged, and merge directive cells are skipped because they hold no content.
    Why: column alignment follows the role the column plays in the table. Neither the number shape of cell text (year 2005, amount 2,005) nor its length tells roles apart.
    RIGHT for quantity columns and LEFT for descriptive text columns are set with markers by the manuscript author, who sees the whole table"""
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
    """Typesetting plan for one table. Computed in one place so HWPX and DOCX use the same merge, alignment, and header decisions."""
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
    """Splits a long table into chunk tables with the header row repeated (--long-table split)"""
    rows = pad_rows(e.data["rows"])
    step = C.LONG_TABLE_ROWS - 1
    chunks = [rows[i:i + step] for i in range(1, len(rows), step)]
    return [Element("table", f"{e.text} ({k})" if e.text else "",
                    data={**e.data, "rows": [rows[0]] + chunk, "split_done": True})
            for k, chunk in enumerate(chunks, 1)]


# ── Figures ──────────────────────────────────────────────────────────────────────
def load_image(e: Element) -> tuple[bytes, str, tuple[float, float]] | None:
    """Reads the source figure. Downloads it if it is a URL.
    Returns: (bytes, format, typeset size in mm) or None (file missing). The size is based on the original before format conversion"""
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
    if fmt in C.IMAGE_CONVERT_TO_JPG:   # convert formats that Hangul and Word cannot open to JPG
        from PIL import Image
        buf = io.BytesIO()
        Image.open(io.BytesIO(data)).convert("RGB").save(buf, "JPEG", quality=C.JPEG_QUALITY)
        data, fmt = buf.getvalue(), "jpg"
    return data, fmt, size


def image_size_mm(data: bytes) -> tuple[float, float]:
    """Figure size rule: caps landscape by width, near-square by width, and portrait by height"""
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


def fit_figure(w_hu: int, h_hu: int, body_w: int) -> tuple[int, int, int]:
    """Figure size and the width of the transparent table that holds it (HWPUNIT). Returns (figure width, figure height, table width)
    The line that holds the figure is as wide as the cell minus the left and right cell margins, so table width = figure width + those margins.
    Without the margins the right side of the figure is cut by that amount, and a wider table drifts from the figure in hand editing.
    A table wider than the body width leaves the page, so the figure is scaled down in proportion"""
    pad = 2 * C.CELL_MARGIN_LR
    max_w = body_w - pad
    if w_hu > max_w:
        w_hu, h_hu = max_w, round(h_hu * max_w / w_hu)
    return w_hu, h_hu, w_hu + pad


def table_pos_role(has_caption: bool, has_fig_pos: bool) -> str:
    """Role of the paragraph that holds a table. The table position style has no top margin because a caption sits above the table.
    A table without a caption touches the paragraph above, so it uses the figure position style, which has a top margin
    (the table position style when the form has no figure position style)"""
    return "table_pos" if has_caption or not has_fig_pos else "fig_pos"


# ── Source footnote merging ────────────────────────────────────────────────────────────
class NoteRegistry:
    """Scope decision and first-footnote record for source footnote merging. Format-agnostic so the HWPX and DOCX typesetters decide alike.
    When a footnote with the same text appears again inside the scope, the typesetter records a cross-reference to the first footnote number instead of a new footnote"""

    def __init__(self, scope: str | None):
        self.scope = scope            # None means no merging
        self.first: dict[str, object] = {}

    @staticmethod
    def _key(text: str) -> str:
        return " ".join(text.split())

    def enter(self, kind: str, level: int = 0):
        """Call before typesetting an element. Clears the first-footnote record when a scope boundary is crossed"""
        if self.scope == "square":
            edge = kind in ("heading", "square")
        else:
            edge = kind == "heading" and level <= C.NOTE_SCOPE_HEADING_LEVEL.get(self.scope, 0)
        if edge:
            self.first.clear()

    def lookup(self, text: str):
        """Record of the earlier footnote with the same text in the same scope, or None"""
        return self.first.get(self._key(text)) if self.scope else None

    def remember(self, text: str, handle):
        if self.scope and self._key(text):
            self.first[self._key(text)] = handle
# ── Inline formatting ───────────────────────────────────────────────────────────────
def inline_segments(text: str) -> list[tuple[str, str]]:
    """Splits inline formatting into a list of (kind, text).
    kind: plain, bold, italic, code, sup, sub, footnote (footnote key)"""
    out = []
    for i, seg in enumerate(INLINE_RE.split(text)):
        if not seg:
            continue
        if i % 2 == 0:   # even items of the split are text outside the marks. They stay literal even when they start with a mark character
            out.append(("plain", seg))
        elif seg.startswith("***"):   # bold italic marks are written as bold
            out.append(("bold", seg[3:-3]))
        elif seg.startswith("**"):
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
        else:   # [^key]
            out.append(("footnote", seg[2:-1]))
    return out


def parse_toc_kinds(spec: str, allowed: tuple[str, ...], option: str) -> tuple[str, ...]:
    """Validates a comma-separated list of item kinds and returns it. option is the option name used in the error message"""
    kinds = tuple(k.strip() for k in spec.split(",") if k.strip())
    unknown = [k for k in kinds if k not in allowed]
    if unknown or not kinds:
        sys.exit(msg("err_toc_scope", option=option, items=unknown, allowed=", ".join(allowed)))
    return kinds


def toc_bookmark_name(text: str) -> str:
    """HWPX bookmark name. Removes only the separator characters of the page reference path from the TOC entry text"""
    return "".join(ch for ch in text if ch not in C.BOOKMARK_DROP_CHARS).strip()


def docx_bookmark_name(n: int, text: str) -> str:
    """Word bookmark name (starts with a letter; letters, digits and underscores; length limit). The sequence number keeps names unique"""
    slug = re.sub(r"[^0-9A-Za-z가-힣]+", "_", text).strip("_")
    return C.DOCX_TOC_BOOKMARK.format(n=n, slug=slug)[:C.DOCX_BOOKMARK_MAX].rstrip("_")


class BookmarkNames:
    """Issues HWPX bookmark names. Hangul does not register two bookmarks with the same name, so a repeated text gets a sequence number starting at (2)"""

    def __init__(self):
        self.used: set[str] = set()

    def issue(self, text: str) -> str:
        base = toc_bookmark_name(text)
        name, n = base, 1
        while name in self.used:
            n += 1
            name = f"{base}({n})"
        self.used.add(name)
        return name


class TocMarks:
    """Registers the items listed in the TOC. The HWPX and DOCX builders both inherit this and implement only the bookmark writing (add_bookmark).
    toc_items: list of (kind, TOC text, bookmark name) in document order. A TOC without page numbers has None as the bookmark name"""

    def toc_mark(self, kind: str, text: str, host):
        """Registers an item that is in the TOC scope and attaches the bookmark that the page reference targets to the host paragraph.
        Why the page-number condition: bookmarks serve only as page reference targets, so a TOC without page numbers gets none"""
        if not self.toc or kind not in self.toc_scope:
            return
        name = self.add_bookmark(host, text) if self.page_number else None
        self.toc_items.append((kind, text, name))


def toc_layout(toc_items: list[tuple[str, str, str | None]]) -> list[dict]:
    """Order of TOC paragraphs (TOC, list of tables, list of figures). Builders only write this list in order.
    kind: title(text, first), entry(item, text, name, indent). first tells whether it is the first TOC title; other titles start on a new page"""
    out = [{"kind": "title", "text": C.label("toc.title"), "first": True}]
    out += [{"kind": "entry", "item": kind, "text": text, "name": name, "indent": C.TOC_INDENT[kind]}
            for kind, text, name in toc_items if kind not in C.TOC_LIST_KINDS]
    for list_kind, title_key in C.TOC_LIST_KINDS.items():
        entries = [(text, name) for kind, text, name in toc_items if kind == list_kind]
        if entries:
            out.append({"kind": "title", "text": C.label(title_key), "first": False})
            out += [{"kind": "entry", "item": list_kind, "text": text, "name": name, "indent": C.TOC_LIST_INDENT}
                    for text, name in entries]
    return out


def heading_label(profile: dict, counters: dict, level: int, text: str) -> str:
    """Adds the number to a heading text. Numbering updates the numbers."""
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
    """Chapter, section, subsection, and 가나다 numbering and page-break decisions. HWPX and DOCX use the same rules."""

    def __init__(self, page_break: str):
        self.page_break = page_break   # chapter | section | none
        self.n = {"chapter": 0, "section": 0, "subsection": 0, "ganada": 0, "total_section": 0}

    def advance(self, level: int) -> bool:
        """Increments the number and returns whether a new page starts before this heading"""
        n = self.n
        brk = False
        if level == 1:
            n.update(chapter=n["chapter"] + 1, section=0, subsection=0, ganada=0)
            brk = self.page_break in ("chapter", "section") and n["chapter"] > 1
        elif level == 2:
            n.update(section=n["section"] + 1, subsection=0, ganada=0)
            # section-level break: the first section right after a chapter and the first section of the document already start a new page, so they are excluded
            brk = self.page_break == "section" and not (n["section"] == 1 and n["chapter"] > 0) and n["total_section"] > 0
            n["total_section"] += 1
        elif level == 3:
            n.update(subsection=n["subsection"] + 1, ganada=0)
        else:
            n["ganada"] += 1
        return brk
