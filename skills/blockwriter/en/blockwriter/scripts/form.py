"""Report form definitions

Both the HWPX skeleton and the DOCX styles are built from the definitions in this file.
To change form values, edit only this file.

Units
- Length: HWPUNIT (1pt = 100, 1mm = 7200 / 25.4)
- Font size: pt
- Line spacing, character width ratio, character spacing: %
"""
from __future__ import annotations

from dataclasses import dataclass

# Hangul's 7 font slots. A character shape has its own font, width ratio, and spacing per slot
LANGS = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")

# Form fonts. All are Nanum fonts distributed by NAVER under the SIL Open Font License 1.1; the names are the Korean names used by Hangul and Word
# For reports with many Hanja, only fonts (NAVER release) with outlines for all 4,620 KS X 1001 Hanja are used
# NanumMyeongjo has no Hanja, and NanumSquare maps Hanja codes to empty glyphs, so Hanja print as blanks
GOTHIC = "나눔고딕"        # every style except the flat headings
BARUN = "나눔바른고딕"     # flat headings. A different typeface from the chapter headings (NanumGothic)

# font classification info (hh:typeInfo). Hangul uses it to choose a substitute when a font is missing
# value order: familyType, weight, proportion, contrast, strokeVariation, armStyle, letterform, midline, xHeight
# familyType is the sans-serif/serif class; the rest are the OS/2 PANOSE values (bWeight through bXHeight) of the font files distributed by NAVER
FONT_CATALOG = {   # font name → (format, classification info)
    GOTHIC: ("TTF", ("FCAT_GOTHIC", 6, 4, 0, 0, 0, 0, 0, 0)),
    BARUN: ("TTF", ("FCAT_GOTHIC", 6, 3, 2, 1, 1, 2, 1, 1)),
}

# Level marks. The special symbols (□, ○, -, ㆍ) of Article 2(1) of the Enforcement Rule of the Regulation on the Operation and Innovation of Administrative Affairs plus the note mark ※; both forms use the same marks
# Characters with outlines in every weight of NanumGothic (NAVER and Google releases) and NanumBarunGothic. □, ○, ㆍ, and ※ share one width within each font, so the text start line after the bullet stays aligned
MARK_SQUARE, MARK_CIRCLE, MARK_DASH, MARK_DOT, MARK_NOTE = "□", "○", "-", "ㆍ", "※"
MARK_CELL_CIRCLE = "◦"   # table cell bullet. A circle smaller than ○ to suit 10pt cell text (diameter 0.53 of the font size; ○ is 0.75)

# border/background definitions for paragraphs and characters (hh:borderFill). All have no lines and differ only in background brush
BORDER_FILLS = {
    "plain": None,            # no background brush. The page border refers to id 1, so this is always written first
    "brush_ff": "#FF000000",  # no background, transparent pattern color
    "brush": "#000000",       # no background, black pattern color
}

TOC_TAB_POS = 48100   # TOC page-number right dotted tab position (HWPUNIT)

# tab definitions (hh:tabPr). toc is the right dotted tab for TOC page numbers
TABS = {
    "none": {"auto_left": False, "items": ()},
    "auto_left": {"auto_left": True, "items": ()},
    "toc": {"auto_left": False, "items": ((TOC_TAB_POS, "RIGHT", "DASH"),)},
}


def _per_lang(v) -> tuple:
    return tuple(v) if isinstance(v, (tuple, list)) else (v,) * len(LANGS)


@dataclass(frozen=True)
class Char:
    """Character shape"""
    face: str | tuple               # one font (shared by all slots) or 7 per-slot fonts in LANGS order
    size: float                     # pt
    bold: bool = False
    ratio: int | tuple = 100        # character width ratio %
    spacing: int | tuple = 0        # character spacing %
    border: str = "brush_ff"        # BORDER_FILLS key
    shadow: str = "#B2B2B2"         # shadow color stored while shadow is off

    @property
    def faces(self) -> tuple:
        return _per_lang(self.face)

    @property
    def ratios(self) -> tuple:
        return _per_lang(self.ratio)

    @property
    def spacings(self) -> tuple:
        return _per_lang(self.spacing)


ABSENT = "absent"  # paragraph that does not write the heading element at all (reproduces the form's stored format as is)


def bullet(char: str, offset: int = 50, adjust: int = 0) -> tuple:
    """Bullet. offset is the gap between symbol and text (% of font size), adjust is the symbol width adjustment (HWPUNIT)
    The Hangul bullet character U+00AD is a soft hyphen that Hangul draws as '-'; DOCX replaces it with '-'"""
    return ("BULLET", char, offset, adjust)


def outline(level: int) -> tuple:
    """Outline-numbered paragraph. Numbers are written into the text, so outline numbering is turned off when typesetting"""
    return ("OUTLINE", level)


@dataclass(frozen=True)
class Para:
    """Paragraph shape"""
    align: str = "JUSTIFY"
    line: int = 160                               # line spacing % (of font size)
    margin: tuple = (0, 0, 0, 0, 0)               # first line (negative is a hanging indent), left, right, above, below
    legacy_margin: tuple | None = None            # value stored for older Hangul versions. If None, written as 2x margin
    head: tuple | str | None = None               # bullet(), outline(), ABSENT, None (no bullet)
    grid: bool = True                             # snap to the page grid
    tab: str = "none"                             # TABS key
    break_word: bool = False                      # Hangul line-break unit (True: character, False: word)
    border: str = "brush_ff"                      # BORDER_FILLS key
    keep_next: bool = False                       # keep on the same page as the next paragraph (so headings and □ are not stranded at a page bottom)


@dataclass(frozen=True)
class Style:
    role: str        # role name referenced by the typesetter
    name: str        # Hangul style name
    eng: str         # Hangul style English name
    char: Char
    para: Para
    kind: str = "PARA"
    next_self: bool = True   # whether the next paragraph style is this style itself (False: body style)


@dataclass(frozen=True)
class NoteSpec:
    """Footnote/endnote shape (hp:footNotePr, hp:endNotePr)"""
    line_length: int
    line_type: str
    between: int
    below: int
    above: int
    place: str


@dataclass(frozen=True)
class Page:
    """Page settings. In Hangul, the header area sits inside the top margin as an extra area"""
    width: int = 59528      # A4 210mm
    height: int = 84188     # A4 297mm
    left: int = 5669        # 20mm
    right: int = 5669
    top: int = 4252         # 15mm
    bottom: int = 4252
    header: int = 2835      # 10mm
    footer: int = 2835
    footnote: NoteSpec = NoteSpec(-1, "SOLID", 284, 568, 852, "EACH_COLUMN")
    endnote: NoteSpec = NoteSpec(0, "NONE", 0, 576, 864, "END_OF_DOCUMENT")
    note_suffix: str = ")"  # character after the footnote number


@dataclass(frozen=True)
class Form:
    page: Page
    styles: tuple
    default_char: Char           # character shape 0. Applies to text without an assigned character shape (header text and so on)
    first_para: tuple            # (style role, Para, Char): the first empty paragraph of the document that holds the section settings
    first_line: tuple            # stored line layout of the first empty paragraph (vertical position, line height, text height, baseline, line spacing, width, flags)
    outline_levels: tuple        # per outline level (format string, whether the number width fits the character width)
    outline_start: int = 0
    restart_page_number: bool = False

    def style(self, role: str) -> Style | None:
        return next((s for s in self.styles if s.role == role), None)


# ── Chapter form: 제N장 / N.N / N.N.N / 가. / □ / ○ / - / ㆍ / ※ ─────────────
CHAPTER = Form(
    page=Page(),
    outline_levels=tuple(("^N", False) for _ in range(7)),
    default_char=Char(GOTHIC, 11, border="plain"),
    first_para=("body", Para(align="CENTER", line=130, grid=False, break_word=True), Char(GOTHIC, 10)),
    first_line=(0, 1000, 1000, 850, 600, 48188, 393216),
    styles=(
        Style("body", "바탕글", "Normal",
              Char(GOTHIC, 10),
              Para(grid=False)),
        Style("chapter", "장 제목", "Chapter Heading",
              Char(GOTHIC, 20, bold=True),
              Para(line=140, margin=(0, 1000, 0, 0, 0), grid=False, keep_next=True)),
        Style("section", "절 제목", "Section Heading",
              Char(GOTHIC, 15, bold=True),
              Para(line=140, margin=(0, 0, 0, 2500, 0), grid=False, keep_next=True)),
        Style("subsection", "소절 제목", "Subsection Heading",
              Char(GOTHIC, 14, bold=True),
              Para(line=140, margin=(0, 0, 0, 2000, 0), keep_next=True)),
        Style("ganada", "가나다 제목", "Ganada Heading",
              Char(GOTHIC, 13, bold=True),
              Para(line=140, margin=(-2290, 300, 0, 1500, 0), keep_next=True)),
        Style("square", "□ 내용", "Square Body",
              Char(GOTHIC, 13, bold=True),
              Para(line=140, margin=(0, 500, 0, 1500, 0), head=bullet(MARK_SQUARE), keep_next=True)),
        Style("circle", "○ 내용", "Circle Body",
              Char(GOTHIC, 12),
              Para(line=140, margin=(0, 1000, 0, 1000, 0), head=bullet(MARK_CIRCLE))),
        Style("dash", "- 내용", "Dash Body",
              Char(GOTHIC, 12),
              Para(line=140, margin=(0, 2410, 0, 700, 0), head=bullet(MARK_DASH))),
        Style("dot", "ㆍ 내용", "Dot Body",
              Char(GOTHIC, 12),
              Para(line=140, margin=(0, 3410, 0, 700, 0), head=bullet(MARK_DOT), grid=False)),
        Style("note", "※ 내용", "Note Body",
              Char(GOTHIC, 10),
              Para(line=140, margin=(0, 3000, 0, 400, 0), head=bullet(MARK_NOTE))),
        Style("table_pos", "표 위치", "Table Position",
              Char(GOTHIC, 10,
                   ratio=(100, 95, 95, 95, 95, 95, 95), spacing=(0, -5, -5, -5, -5, -5, -5)),
              Para(align="CENTER", margin=(0, 0, 0, 0, 1000), grid=False, break_word=True)),
        Style("table_cell", "표 내용", "Table Body",
              Char(GOTHIC, 11, ratio=95, spacing=-5, border="plain"),
              Para(align="CENTER", line=130)),
        # the left-aligned table content and cell bullet styles are left-aligned. Justified text stretches the word gaps of wrapped lines in narrow cells
        Style("table_cell_left", "표 내용 왼쪽", "Table Body Left",
              Char(GOTHIC, 10),
              Para(align="LEFT", line=130, grid=False)),
        Style("table_cell_bullet", "표 내용 ○", "Table Body Circle",
              Char(GOTHIC, 10),
              Para(align="LEFT", line=130, margin=(0, 0, 0, 0, 300), head=bullet(MARK_CELL_CIRCLE, offset=20),
                   grid=False)),
        Style("table_cell_dash", "표 내용 -", "Table Body Dash",
              Char(GOTHIC, 10),
              Para(align="LEFT", line=130, margin=(0, 1000, 0, 0, 300), head=bullet(MARK_DASH, offset=20, adjust=300),
                   grid=False)),
        Style("table_title", "표 제목", "Table Caption",
              Char(GOTHIC, 11, bold=True),
              Para(align="CENTER", margin=(0, 0, 0, 1000, 0), grid=False, break_word=True)),
        Style("unit", "단위", "Unit",
              Char(GOTHIC, 9),
              Para(align="RIGHT", margin=(0, 0, 0, 500, 0), break_word=True)),
        Style("source", "출처", "Source",
              Char(GOTHIC, 9),
              Para(line=130, margin=(-1320, 300, 0, 500, 0))),
        Style("fig_pos", "그림 위치", "Figure Position",
              Char(GOTHIC, 10,
                   ratio=(100, 95, 95, 95, 95, 95, 95), spacing=(0, -5, -5, -5, -5, -5, -5)),
              Para(align="CENTER", margin=(0, 0, 0, 1000, 1000), grid=False, break_word=True)),
        Style("fig_title", "그림 제목", "Figure Caption",
              Char(GOTHIC, 11, bold=True, spacing=(-6, 0, -6, -6, -6, -6, -6)),
              Para(align="CENTER", margin=(0, 0, 0, 500, 0), grid=False, break_word=True)),
        Style("footnote", "각주", "Footnote",
              Char(GOTHIC, 10, shadow="#C0C0C0"),
              Para(align="LEFT", line=130, margin=(-1337, 0, 0, 0, 0))),
        Style("toc_chapter", "목차 장", "TOC Chapter",
              Char(GOTHIC, 14, bold=True),
              Para(line=155, margin=(0, 0, 0, 1000, 0), tab="toc")),
        Style("toc_section", "목차 절", "TOC Section",
              Char(GOTHIC, 12),
              Para(line=155, margin=(0, 1500, 0, 500, 0), tab="toc")),
    ),
)

# ── Form without chapters: document title / N. / N.N / 가. / □ / ○ / - / ㆍ / ※ ────────────────
FLAT = Form(
    page=Page(top=4251, bottom=2834, header=2834, footer=4251,
              footnote=NoteSpec(-1, "SOLID", 283, 567, 850, "EACH_COLUMN"),
              endnote=NoteSpec(14692344, "SOLID", 0, 567, 850, "END_OF_DOCUMENT")),
    outline_levels=tuple((".".join(f"^{k}" for k in range(1, n + 1)) + ("." if n == 1 else ""), True)
                         for n in range(1, 8)),
    outline_start=1,
    restart_page_number=True,
    default_char=Char(GOTHIC, 12, border="brush"),
    first_para=("section", Para(line=130, margin=(-1310, 0, 0, 0, 0)), Char(BARUN, 15, border="brush")),
    first_line=(1500, 1500, 1500, 1275, 900, 48188, 2490368),
    styles=(
        Style("body", "바탕글", "Normal",
              Char(GOTHIC, 10, shadow="#C0C0C0"),
              Para()),
        Style("chapter", "문서 제목", "Document Title",
              Char(BARUN, 20, bold=True, border="brush"),
              Para(align="CENTER", margin=(0, 0, 0, 0, 2000), legacy_margin=(0, 0, 0, 0, 2000), tab="auto_left",
                   keep_next=True),
              next_self=False),
        Style("section", "절 제목", "Section Heading",
              Char(BARUN, 15, bold=True, border="brush"),
              Para(margin=(0, 0, 0, 1500, 0), head=outline(1), tab="auto_left", keep_next=True)),
        Style("subsection", "소절 제목", "Subsection Heading",
              Char(BARUN, 14, bold=True, border="brush"),
              Para(margin=(0, 0, 0, 1500, 0), head=outline(2), tab="auto_left", keep_next=True)),
        Style("ganada", "가나다 제목", "Ganada Heading",
              Char(GOTHIC, 13, bold=True, border="brush"),
              Para(line=140, margin=(0, 500, 0, 1400, 0), legacy_margin=(0, 500, 0, 1400, 0), head=ABSENT,
                   keep_next=True)),
        Style("square", "□ 내용", "Square Body",
              Char(GOTHIC, 12, bold=True, border="brush"),
              Para(line=140, margin=(0, 1000, 0, 1400, 0), head=bullet(MARK_SQUARE), keep_next=True)),
        Style("circle", "○ 내용", "Circle Body",
              Char(GOTHIC, 12, border="brush"),
              Para(margin=(0, 1500, 0, 1200, 0), legacy_margin=(0, 2000, 0, 2400, 0), head=bullet(MARK_CIRCLE))),
        Style("dash", "- 내용", "Dash Body",
              Char(GOTHIC, 12, spacing=3, border="brush"),
              Para(margin=(0, 2413, 0, 700, 0), head=bullet(MARK_DASH))),
        Style("dot", "ㆍ 내용", "Dot Body",
              Char(GOTHIC, 12, spacing=2, border="brush"),
              Para(margin=(0, 3413, 0, 500, 0), head=bullet(MARK_DOT), grid=False, border="brush")),
        Style("note", "※ 내용", "Note Body",
              Char(GOTHIC, 12, spacing=2, border="brush"),
              Para(margin=(0, 3410, 0, 200, 200), head=bullet(MARK_NOTE), grid=False, border="brush")),
        Style("table_pos", "표 위치", "Table Position",
              Char(GOTHIC, 11, border="brush", shadow="#C0C0C0"),
              Para(align="CENTER", line=140, margin=(0, 0, 0, 0, 1000), break_word=True, border="brush")),
        Style("table_cell", "표 내용", "Table Body",
              Char(GOTHIC, 10, spacing=-7, border="brush"),
              Para(align="CENTER", line=130, margin=(0, 300, 300, 0, 0), grid=False, break_word=True, border="brush")),
        Style("table_header", "표 머리글", "Table Header",
              Char(GOTHIC, 10, bold=True, spacing=-7, border="brush"),
              Para(align="CENTER", line=130, margin=(0, 300, 300, 0, 0), grid=False, break_word=True, border="brush")),
        # cell bullets: the same setup as the chapter form (left-aligned) with the flat table content character shape and cell padding
        Style("table_cell_bullet", "표 내용 ○", "Table Body Circle",
              Char(GOTHIC, 10, spacing=-7, border="brush"),
              Para(align="LEFT", line=130, margin=(0, 300, 300, 0, 300), head=bullet(MARK_CELL_CIRCLE, offset=20),
                   grid=False, border="brush")),
        Style("table_cell_dash", "표 내용 -", "Table Body Dash",
              Char(GOTHIC, 10, spacing=-7, border="brush"),
              Para(align="LEFT", line=130, margin=(0, 1300, 300, 0, 300), head=bullet(MARK_DASH, offset=20, adjust=300),
                   grid=False, border="brush")),
        Style("table_title", "표 제목", "Table Caption",
              Char(GOTHIC, 11, border="brush"),
              Para(align="CENTER", margin=(0, 0, 0, 1000, 0), grid=False, break_word=True, border="brush")),
        Style("unit", "단위", "Unit",
              Char(GOTHIC, 9, spacing=-7, border="brush"),
              Para(align="RIGHT", line=130, margin=(0, 0, 300, 0, 0), grid=False, break_word=True, border="brush"),
              next_self=False),
        Style("source", "출처", "Source",
              Char(GOTHIC, 9, spacing=-7, border="brush"),
              Para(align="LEFT", line=130, margin=(0, 0, 300, 0, 0), grid=False, break_word=True, border="brush"),
              next_self=False),
        Style("fig_pos", "그림 위치", "Figure Position",
              Char(GOTHIC, 10, ratio=(100, 95, 95, 95, 95, 95, 95), spacing=(0, -5, -5, -5, -5, -5, -5), border="brush"),
              Para(align="CENTER", line=130, margin=(0, 0, 0, 1000, 1000), grid=False, break_word=True, border="brush")),
        Style("fig_title", "그림 제목", "Figure Caption",
              Char(GOTHIC, 11, spacing=(-6, 0, -6, -6, -6, -6, -6), border="brush"),
              Para(align="CENTER", margin=(0, 0, 0, 500, 1000), grid=False, break_word=True, border="brush")),
        Style("footnote", "각주", "Footnote",
              Char(GOTHIC, 9, shadow="#C0C0C0"),
              Para(align="LEFT", line=130, margin=(-1310, 0, 0, 0, 0))),
        Style("page_number", "쪽 번호", "Page Number",
              Char(GOTHIC, 10, shadow="#C0C0C0"),
              Para(line=130, margin=(-1310, 0, 0, 0, 0)), kind="CHAR", next_self=False),
    ),
)

FORMS = {"chapter": CHAPTER, "flat": FLAT}
