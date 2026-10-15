"""보고서 양식 정의

HWPX 스켈레톤과 DOCX 스타일을 모두 이 파일의 정의에서 만든다.
양식 수치를 바꿀 때는 이 파일만 고친다.

단위
- 길이: HWPUNIT (1pt = 100, 1mm = 7200 / 25.4)
- 글자 크기: pt
- 줄 간격, 장평, 자간: %
"""
from __future__ import annotations

from dataclasses import dataclass

# 한/글 글꼴 슬롯 7종. 글자 모양은 슬롯마다 글꼴, 장평, 자간을 따로 가진다
LANGS = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")

# 양식 글꼴. 모두 네이버가 SIL Open Font License 1.1로 배포하는 나눔글꼴이며 글꼴 이름은 한/글과 Word가 쓰는 한국어 이름
# 한자가 많은 보고서를 위해 KS X 1001 한자 4,620자의 글자 모양을 모두 담은 글꼴(네이버 배포본)만 쓴다
# 나눔명조는 한자가 없고 나눔스퀘어는 한자 코드만 있고 글자 모양이 비어 있어 한자가 빈칸으로 찍힘
GOTHIC = "나눔고딕"        # flat 제목을 뺀 모든 스타일
BARUN = "나눔바른고딕"     # flat 제목. chapter 제목(나눔고딕)과 서체로 구분

# 글꼴 분류 정보(hh:typeInfo). 한/글이 글꼴을 찾지 못할 때 대체 글꼴을 고르는 기준
# 값 순서: familyType, weight, proportion, contrast, strokeVariation, armStyle, letterform, midline, xHeight
# familyType은 고딕·명조 구분이고 나머지는 네이버 배포 글꼴 파일의 OS/2 PANOSE 값(bWeight부터 bXHeight까지)
FONT_CATALOG = {   # 글꼴명 → (형식, 분류 정보)
    GOTHIC: ("TTF", ("FCAT_GOTHIC", 6, 4, 0, 0, 0, 0, 0, 0)),
    BARUN: ("TTF", ("FCAT_GOTHIC", 6, 3, 2, 1, 1, 2, 1, 1)),
}

# 계위 기호. 「행정업무의 운영 및 혁신에 관한 규정 시행규칙」 제2조제1항의 특수 기호(□, ○, -, ㆍ)와 주석 기호 ※이며 두 양식이 같다
# 나눔고딕(네이버, Google 배포본)과 나눔바른고딕의 모든 굵기에 글자 모양이 있는 문자. □, ○, ㆍ, ※는 글꼴마다 폭이 같아 글머리 뒤 본문 시작선이 맞음
MARK_SQUARE, MARK_CIRCLE, MARK_DASH, MARK_DOT, MARK_NOTE = "□", "○", "-", "ㆍ", "※"
MARK_CELL_CIRCLE = "◦"   # 표 셀 글머리. 셀 글자(10pt)에 맞춰 ○보다 작은 원 (글자 크기 대비 지름 0.53, ○는 0.75)

# 문단과 글자의 테두리·배경 정의(hh:borderFill). 모두 선 없음이며 배경 붓 설정만 다르다
BORDER_FILLS = {
    "plain": None,            # 배경 붓 없음. 쪽 테두리가 1번으로 참조하므로 항상 첫 번째로 기록
    "brush_ff": "#FF000000",  # 배경 없음, 무늬색 투명
    "brush": "#000000",       # 배경 없음, 무늬색 검정
}

TOC_TAB_POS = 48100   # 목차 쪽번호 오른쪽 점선 탭 위치 (HWPUNIT)

# 탭 정의(hh:tabPr). toc는 목차 쪽번호용 오른쪽 점선 탭
TABS = {
    "none": {"auto_left": False, "items": ()},
    "auto_left": {"auto_left": True, "items": ()},
    "toc": {"auto_left": False, "items": ((TOC_TAB_POS, "RIGHT", "DASH"),)},
}


def _per_lang(v) -> tuple:
    return tuple(v) if isinstance(v, (tuple, list)) else (v,) * len(LANGS)


@dataclass(frozen=True)
class Char:
    """글자 모양"""
    face: str | tuple               # 글꼴 1개(전 슬롯 공통) 또는 LANGS 순서의 슬롯별 글꼴 7개
    size: float                     # pt
    bold: bool = False
    ratio: int | tuple = 100        # 장평 %
    spacing: int | tuple = 0        # 자간 %
    border: str = "brush_ff"        # BORDER_FILLS 키
    shadow: str = "#B2B2B2"         # 그림자 없음 상태에서 저장되는 그림자 색

    @property
    def faces(self) -> tuple:
        return _per_lang(self.face)

    @property
    def ratios(self) -> tuple:
        return _per_lang(self.ratio)

    @property
    def spacings(self) -> tuple:
        return _per_lang(self.spacing)


def bullet(char: str, offset: int = 50, adjust: int = 0) -> tuple:
    """글머리표. offset은 기호와 본문 사이 간격(글자 크기 대비 %), adjust는 기호 폭 조정(HWPUNIT)
    한/글 글머리 문자 U+00AD는 한/글이 '-'로 그리는 붙임표이며 DOCX에서는 '-'로 바꿔 쓴다"""
    return ("BULLET", char, offset, adjust)


def outline(level: int) -> tuple:
    """개요 번호 문단. 번호는 본문에 직접 쓰므로 조판 시 개요 번호를 끄고 사용"""
    return ("OUTLINE", level)


@dataclass(frozen=True)
class Para:
    """문단 모양"""
    align: str = "JUSTIFY"
    line: int = 160                               # 줄 간격 % (글자 크기 대비)
    margin: tuple = (0, 0, 0, 0, 0)               # 첫 줄(음수는 내어쓰기), 왼쪽, 오른쪽, 위, 아래
    legacy_margin: tuple | None = None            # 구형 한/글용 저장값. 없으면 margin의 2배로 기록
    head: tuple | None = None                     # bullet(), outline(), None(글머리 없음)
    grid: bool = True                             # 편집 용지 격자에 맞춤
    tab: str = "none"                             # TABS 키
    break_word: bool = False                      # 한글 줄 나눔 기준 (True: 글자, False: 어절)
    border: str = "brush_ff"                      # BORDER_FILLS 키
    keep_next: bool = False                       # 다음 문단과 같은 쪽에 둠 (제목과 □가 쪽 끝에 홀로 남지 않게)


@dataclass(frozen=True)
class Style:
    role: str        # 조판기가 참조하는 역할명
    name: str        # 한/글 스타일 이름
    eng: str         # 한/글 스타일 영문 이름
    char: Char
    para: Para
    kind: str = "PARA"
    next_self: bool = True   # 다음 문단 스타일을 자기 자신으로 둘지 (False면 바탕글)


@dataclass(frozen=True)
class NoteSpec:
    """각주·미주 모양(hp:footNotePr, hp:endNotePr)"""
    line_length: int
    line_type: str
    between: int
    below: int
    above: int
    place: str


@dataclass(frozen=True)
class Page:
    """쪽 설정. 한/글 쪽 여백은 위쪽 여백 안쪽에 머리말 영역이 추가로 놓이는 구조"""
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
    note_suffix: str = ")"  # 각주 번호 뒤 문자


@dataclass(frozen=True)
class Form:
    page: Page
    styles: tuple
    default_char: Char           # 0번 글자 모양. 글자 모양을 지정하지 않은 글자(머리말 문구 등)에 적용
    first_para: tuple            # (스타일 역할, Para, Char): 구역 설정을 담는 문서 첫 빈 문단
    first_line: tuple            # 첫 빈 문단의 줄 배치 저장값 (세로 위치, 줄 높이, 글자 높이, 기준선, 줄 간격, 폭, 플래그)
    outline_levels: tuple        # 개요 번호 수준별 (형식 문자열, 번호 폭을 글자 폭에 맞춤 여부)
    outline_start: int = 0
    restart_page_number: bool = False

    def style(self, role: str) -> Style | None:
        return next((s for s in self.styles if s.role == role), None)


# ── 장 체계 양식: 제N장 / N.N / N.N.N / 가. / □ / ○ / - / ㆍ / ※ ─────────────
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
        # 표 내용 왼쪽과 셀 글머리 스타일은 왼쪽 정렬. 양쪽 정렬은 좁은 셀에서 접힌 줄의 어절 간격을 크게 벌림
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

# ── 장 없는 양식: 문서 제목 / N. / N.N / 가. / □ / ○ / - / ㆍ / ※ ────────────────
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
              Para(line=140, margin=(0, 500, 0, 1400, 0), legacy_margin=(0, 500, 0, 1400, 0),
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
        # 셀 글머리: chapter 양식과 같은 구성(왼쪽 정렬)에 flat 표 내용의 글자 모양과 셀 안 여백을 적용
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
