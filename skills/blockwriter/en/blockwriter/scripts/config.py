"""Settings: typesetting values, renderers, font mapping, messages.
To change values, edit only this file (typesetting rules) and form.py (form appearance)."""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

LANG = "en"   # CLI message language: ko | en

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Numbering per form. Style names are defined in form.py ─────────────────────────
# numbering: manual writes numbers into the text, auto leaves them to Hangul outline numbering
PROFILE_FORMATS = {
    "chapter": {"numbering": "manual", "chapter_format": "제{n}장 {t}", "section_format": "{c}.{s} {t}",
                "subsection_format": "{c}.{s}.{ss} {t}", "caption_prefix": "{c}-"},
    "flat": {"numbering": "manual", "chapter_format": "{t}", "section_format": "{s}. {t}",
             "subsection_format": "{s}.{ss} {t}", "caption_prefix": ""},
}
PROFILE_DEFAULTS = {"numbering": "manual", "chapter_format": "제{n}장 {t}", "section_format": "{c}.{s} {t}",
                    "subsection_format": "{c}.{s}.{ss} {t}", "caption_prefix": ""}
NON_ROLE_KEYS = tuple(PROFILE_DEFAULTS)

# ── Labels: fixed strings that build prints into documents, and the language tags written into files ──────
# The defaults are the Korean values. build --labels FILE.json overrides any part with a nested JSON of the same keys; omitted keys keep the defaults
LABEL_DEFAULTS = {
    # heading number formats. None keeps the active profile's format (PROFILE_FORMATS or the profile JSON)
    "formats": {"chapter": None, "section": None, "subsection": None},
    "letters": {"items": "가나다라마바사아자차카타파하", "format": "{x}."},   # 가나다 level: letter sequence and number format ({x} is the letter)
    "toc": {"title": "목  차"},
    # caption number part = open + label + space + number + close + space. seq is the Word SEQ field name (None uses the label)
    "caption": {"table": {"label": "표", "open": "<", "close": ">", "seq": None},
                "figure": {"label": "그림", "open": "[", "close": "]", "seq": None}},
    # manuscript tokens the parser recognizes. Tokens in a label file are added to these and never replace them
    "notation": {"source": ["출처", "자료", "주"], "unit": ["단위"], "table": ["표"], "figure": ["그림"], "colwidth": ["열 폭"]},
    # DOCX document default language (w:lang). HWPX content.hpf language and style langID (Windows LCID) of the built-in forms
    "language": {"latin": "en-US", "east_asia": "ko-KR", "hwpx_package": "ko", "hwpx_style_lcid": 1042},
}
# built-in source tokens that are also written in parentheses ('(출처)'). '(주)' abbreviates 주식회사 (Inc.), so it does not start a source line
SOURCE_PAREN_TOKENS = ("출처", "자료")
# placeholders each format may use, and the one it must contain
LABEL_FORMAT_FIELDS = {"formats.chapter": (("n", "t"), "t"), "formats.section": (("c", "s", "t"), "t"),
                       "formats.subsection": (("c", "s", "ss", "t"), "t"), "letters.format": (("x",), "x")}
CAPTION_KINDS = {"TABLE": "table", "PICTURE": "figure"}   # writers' caption kind → caption label key
LABELS = copy.deepcopy(LABEL_DEFAULTS)   # active labels. set_labels replaces them

XLSX_WIDE_COLS = 6              # if a sheet has more columns than this, ask the user whether to transpose or split the table

# ── Manuscript lint ────────────────────────────────────────────────────────
SHORT_SECTION_ELEMS = 8   # a section with fewer elements than this may leave mostly blank space when it starts a new page

# ── Tables (HWPUNIT). A table is subordinate information under a ○ statement, so column widths fit the text and keep it inside the ○ level; only tables with much information widen up to the cap ──
TABLE_INDENT_MARGIN = 1500      # level indent subtracted from the body width (table width cap = body width - this value)
TABLE_MIN_RATIO = 0.5           # table width floor (ratio of the cap). Prevents 2-3 column label tables from being too narrow
COL_MIN_W = 3000                # minimum column width (about 10.6mm)
COL_PAD_W = 1800                # per-column left/right padding plus allowance for glyph width error
COL_ONE_LINE_W = 12000          # one-line width (about 42mm, 10 Hangul characters at 12pt). Columns whose longest line is wider are reduced assuming a 2-line wrap
COL_WRAP_RATIO = 0.6            # narrowing ratio for columns assumed to wrap
COL_WIDTH_PCT_MAX = 100         # basis of the manuscript column width line (table width cap = 100%). A sum above it would push the table outside the ○ level
COL_WIDTH_PCT_TOL = 0.01        # floating-point tolerance for the column width sum (33.34 + 33.33 + 33.33 and the like)
MERGE_LABEL_COLS = 2            # maximum number of leading label columns eligible for vertical merge
LONG_TABLE_ROWS = 25            # above this, long-table handling applies (split at page boundaries, repeat header rows)
# the weighted-length unit is half a Hangul character width (half of CELL_HANGUL_EM). Column widths and row line counts are measured in this unit
WIDE_UNITS = 2                  # weighted width of full-width characters such as Hangul and Hanja
OTHER_UNITS = 1                 # weighted width of any other character not in the width table (GLYPH_EM)
# NanumGothic width per character (multiples of the font size). Counting Latin letters, digits, and symbols by their real widths fits names that mix narrow (i, l, t) and wide (m, w) letters.
# generated by dev/gen_glyph_em.py; each value is the wider of regular and bold (headers are bold)
GLYPH_EM = {
    '!': 0.424, '"': 0.43, '#': 0.606, '$': 0.606, '%': 1.09, '&': 0.727, "'": 0.303, '(': 0.363, ')': 0.363, '*': 0.606,
    '+': 0.654, ',': 0.303, '-': 0.363, '.': 0.303, '/': 0.375, '0': 0.606, '1': 0.606, '2': 0.606, '3': 0.606, '4': 0.606,
    '5': 0.606, '6': 0.606, '7': 0.606, '8': 0.606, '9': 0.606, ':': 0.303, ';': 0.303, '<': 0.547, '=': 0.654, '>': 0.547,
    '?': 0.545, '@': 0.872, 'A': 0.727, 'B': 0.606, 'C': 0.672, 'D': 0.727, 'E': 0.576, 'F': 0.503, 'G': 0.797, 'H': 0.727,
    'I': 0.242, 'J': 0.363, 'K': 0.641, 'L': 0.484, 'M': 0.969, 'N': 0.727, 'O': 0.787, 'P': 0.577, 'Q': 0.787, 'R': 0.622,
    'S': 0.545, 'T': 0.545, 'U': 0.727, 'V': 0.666, 'W': 1.029, 'X': 0.666, 'Y': 0.666, 'Z': 0.545, '[': 0.363, '\\': 0.966,
    ']': 0.363, '^': 0.654, '_': 0.545, '`': 0.242, 'a': 0.545, 'b': 0.606, 'c': 0.484, 'd': 0.606, 'e': 0.545, 'f': 0.363,
    'g': 0.606, 'h': 0.606, 'i': 0.242, 'j': 0.269, 'k': 0.52, 'l': 0.242, 'm': 0.908, 'n': 0.606, 'o': 0.606, 'p': 0.606,
    'q': 0.606, 'r': 0.363, 's': 0.424, 't': 0.363, 'u': 0.606, 'v': 0.484, 'w': 0.848, 'x': 0.51, 'y': 0.464, 'z': 0.484,
    '{': 0.303, '|': 0.242, '}': 0.303, '~': 0.654, '¡': 0.302, '¢': 0.94, '£': 0.94, '¤': 0.838, '¥': 0.94, '§': 0.346,
    '¨': 0.54, '©': 0.855, 'ª': 0.541, '«': 0.94, '¬': 0.94, '®': 0.94, '°': 0.446, '±': 0.567, '²': 0.41, '³': 0.428,
    '´': 0.324, '¶': 0.605, '·': 0.29, '¸': 0.317, '¹': 0.405, 'º': 0.541, '»': 0.94, '¼': 0.737, '½': 0.705, '¾': 0.746,
    '¿': 0.54, 'À': 0.672, 'Á': 0.672, 'Â': 0.672, 'Æ': 0.865, 'Ç': 0.571, 'È': 0.527, 'É': 0.527, 'Ê': 0.527, 'Ë': 0.527,
    'Í': 0.412, 'Î': 0.413, 'Ï': 0.412, 'Ð': 0.794, 'Ñ': 0.727, 'Ó': 0.7, 'Ô': 0.7, '×': 0.592, 'Ø': 0.78, 'Ù': 0.651,
    'Ú': 0.651, 'Û': 0.651, 'Ü': 0.651, 'Þ': 0.53, 'ß': 0.657, 'à': 0.532, 'á': 0.532, 'â': 0.532, 'ä': 0.532, 'æ': 0.915,
    'ç': 0.51, 'è': 0.557, 'é': 0.557, 'ê': 0.557, 'ë': 0.557, 'í': 0.418, 'î': 0.413, 'ï': 0.412, 'ð': 0.592, 'ñ': 0.606,
    'ó': 0.622, 'ô': 0.622, 'ö': 0.622, '÷': 0.65, 'ø': 0.612, 'ù': 0.558, 'ú': 0.558, 'û': 0.558, 'ü': 0.558, 'þ': 0.599,
    '‐': 0.438, '–': 0.41, '—': 0.864, '―': 0.864, '‖': 0.94, '‘': 0.185, '’': 0.185, '‛': 0.185, '“': 0.35, '”': 0.35,
    '‟': 0.35, '†': 0.552, '‡': 0.552, '•': 0.94, '‥': 0.94, '…': 0.94,
}
SPACE_EM_HWPX = 0.5             # Hangul space width. The form's character shapes do not use the font's space width, so it is half the font size (same as measured in rhwp)
SPACE_EM_DOCX = 0.28            # Word space width. The space glyph width of NanumGothic
DEFAULT_PAGE_BREAK = "chapter"  # new-page unit for a build without --page-break
DEFAULT_LONG_TABLE = "engine"   # long-table handling for a build without --long-table
HEADER_FILL = "#D9D9D9"         # table header background
BORDER_WIDTH = "0.15 mm"        # cell border width
BORDER_WIDTH_MM = 0.15
BORDER_COLOR = "#000000"
EDGE_OPEN_SIDES = True          # leave the table's left and right outer borders open: no left border on the leftmost cell, no right border on the rightmost cell
FIGURE_IN_TABLE = True          # put a figure in a transparent one-column table so the figure and source move together (the caption is an HWPX caption object or a DOCX paragraph after the table)
ROW_BASE_H = 2000               # one-line row height (minimum; grows with content)
ROW_LINE_H = 1400               # added height per extra line from wrapping or line breaks
CELL_MARGIN_LR = 510            # cell left/right padding (same as the typesetting library default, also applied to DOCX)
CELL_MARGIN_TB = 141            # cell top/bottom padding
CELL_HANGUL_EM = 0.94           # Hangul character width / font size. Measured on NanumGothic; used for the weighted-length unit and for estimating row line counts
CAPTION_GAP = 850               # gap between caption and table

# ── Figures (mm, for a body width of about 170mm). Full-width figures break the level alignment and portrait figures overflow a page
IMG_LANDSCAPE_RATIO = 1.4       # width/height ratio at or above this is landscape
IMG_PORTRAIT_RATIO = 0.8        # at or below this is portrait; in between is near-square
IMG_LANDSCAPE_W_MM = 140.0
IMG_SQUARE_W_MM = 90.0
IMG_PORTRAIT_H_MM = 110.0
IMG_DEFAULT_DPI = 96.0
IMG_FALLBACK_PX = (800, 600)    # assumed size for figures whose size cannot be read
IMG_URL_TIMEOUT = 20
IMAGE_MIME_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/bmp": "bmp", "image/webp": "webp"}
IMAGE_CONVERT_TO_JPG = ("webp",)
JPEG_QUALITY = 90
HTTP_USER_AGENT = "blockwriter (image fetch for document typesetting)"

# ── Cover and table of contents ────────────────────────────────────────────
COVER_TOP_LINES = 8             # blank lines above the cover title
COVER_TITLE_PT = 24
COVER_SUB_PT = 16
COVER_DATE_PT = 14
COVER_ORG_PT = 16
COVER_GAP_LINES = 14            # blank lines between the date and the organization
from form import TOC_TAB_POS  # noqa: E402  TOC page-number right dotted tab position (the form definition is the source)
TOC_SECTION_INDENT = 1500       # TOC section indent
TOC_SUB_INDENT = 3000           # TOC subsection indent
TOC_MAX_PASSES = 2              # maximum re-typesetting passes when the re-render check after filling TOC page numbers still finds mismatches
TOC_FIRST_LINE_KEY = 10         # number of leading characters (spaces excluded) of the first body line used for the stranded-heading check; found on its starting page even if the line runs onto the next page
BLOCK_GAP_LINES = 0             # blank paragraphs before and after table/figure blocks. Spacing is handled by the table/figure position style margins

# ── HWPX renderer (rhwp) ───────────────────────────────────────────────────
RHWP_REPO = "https://github.com/edwardkim/rhwp"
# rhwp changes its command set often. If a name below is missing in the current version, find the command with the same function in `rhwp --help` and replace only the value
RHWP_PDF_COMMAND = "export-pdf"          # export the document to PDF
RHWP_VERIFY_COMMAND = "verify"           # check expectations
RHWP_UNKNOWN_COMMAND_MARKERS = ("알 수 없는 명령", "unknown command", "unrecognized")
RHWP_PDF_OUTLINE_FLAG = "--text-as-paths"   # draw glyphs as outlines when fonts are not installed. Not used for TOC page-number calculation, which needs text extraction
RHWP_FONT_PATH_FLAG = "--font-path"
RENDER_DPI = 80
# glyph that replaces soft hyphen (U+00AD) bullets in the review copy. Approximate renderers do not draw U+00AD, so the - level symbol looks blank
SOFT_HYPHEN_GLYPH = "-"
LIBREOFFICE_TIMEOUT = 600

# ── Fonts ──────────────────────────────────────────────────────────────────
# Documents record the form font names as they are. The table below lists substitutes used only for review rendering where that font is not installed
# 나눔바른고딕 (NanumBarunGothic) is a built-in form font (flat headings); the rest are Windows and Hancom Office fonts common in user HWPX forms
FONT_SUBSTITUTES = {
    "나눔바른고딕": "NanumGothic",
    "맑은 고딕": "NanumGothic", "Malgun Gothic": "NanumGothic",
    "한컴돋움": "NanumGothic", "돋움": "NanumGothic", "굴림": "NanumGothic", "함초롬돋움": "NanumGothic",
    "한양중고딕": "NanumGothic", "HCI Hollyhock": "NanumGothic",
    "휴먼명조": "NanumMyeongjo", "바탕": "NanumMyeongjo", "함초롬바탕": "NanumMyeongjo",
    "한양신명조": "NanumMyeongjo", "명조": "NanumMyeongjo", "HCI Poppy": "NanumMyeongjo",
    "HY헤드라인M": "NanumGothic ExtraBold",
    "Arial": "Liberation Sans",
}
# Download location of the free-license (SIL OFL 1.1) fonts (official Google Fonts repository)
# NanumGothic and NanumMyeongjo in this repository have no Hanja. NanumMyeongjo is used only as a rendering substitute for serif fonts of user forms
FREE_FONT_BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl"
FREE_FONTS = {
    "NanumGothic": ("nanumgothic", ["NanumGothic-Regular.ttf", "NanumGothic-Bold.ttf", "NanumGothic-ExtraBold.ttf"]),
    "NanumMyeongjo": ("nanummyeongjo", ["NanumMyeongjo-Regular.ttf", "NanumMyeongjo-Bold.ttf", "NanumMyeongjo-ExtraBold.ttf"]),
}
FREE_FONT_LICENSE_FILE = "OFL.txt"
USER_FONT_DIR = os.path.expanduser("~/.local/share/fonts/blockwriter")
FONTCONFIG_FILE = os.path.expanduser("~/.config/fontconfig/conf.d/60-blockwriter.conf")
# KS X 1001 Hanja area (EUC-KR lead byte 0xCA-0xFD, trail byte 0xA1-0xFE, 4,888 characters). The fonts command judges Hanja coverage by whether
# all 4,620 unified ideographs among them are present. The other 268 are compatibility codes for the same Hanja with other readings
KSX1001_HANJA_LEAD = range(0xCA, 0xFE)
KSX1001_HANJA_TRAIL = range(0xA1, 0xFF)
CJK_UNIFIED_RANGE = (0x4E00, 0x9FFF)   # CJK Unified Ideographs basic block
# Folders where the fonts command looks for installed fonts on systems without fontconfig (on Windows, the all-users and per-user font folders)
FONT_DIRS = {
    "win32": ["%WINDIR%\\Fonts", "%LOCALAPPDATA%\\Microsoft\\Windows\\Fonts"],
    "darwin": ["/Library/Fonts", "~/Library/Fonts", "/System/Library/Fonts"],
}
FONT_FILE_EXTS = (".ttf", ".otf", ".ttc")
REGULAR_WEIGHT = 400   # when several files share the name, Hanja are judged on the regular-weight file
# Where to obtain each form font
FONT_SOURCES = {"나눔고딕": "src_nanum_auto", "나눔바른고딕": "src_nanum_manual"}   # values are MESSAGES keys

# ── DOCX ───────────────────────────────────────────────────────────────────
DOCX_HEADING_STYLES = {   # heading role → Word built-in heading style (the styles that the TOC field and navigation pane recognize)
    "chapter": {"chapter": "Heading 1", "section": "Heading 2", "subsection": "Heading 3", "ganada": "Heading 4"},
    "flat": {"chapter": "Title", "section": "Heading 1", "subsection": "Heading 2", "ganada": "Heading 3"},
}
DOCX_FULLWIDTH_BULLET = 1.0     # full-width bullet symbol width (ratio of font size)
DOCX_HALFWIDTH_BULLET = 0.5     # half-width bullet symbol width
DOCX_SPACER_PT = 1              # line height of the empty paragraph used as spacing below tables
# heading bookmark name. Word treats names starting with an underscore as hidden bookmarks. The PAGEREF fields of TOC entries find heading pages through these bookmarks
DOCX_TOC_BOOKMARK = "_Toc{n:09d}"
# values written to the font table (fontTable). When a document font is missing, Word uses this information to pick a substitute of the same family
# Recorded as roman (serif family) when the English name contains Myeongjo, otherwise swiss (sans-serif family). Character set is Hangul (charset 81)
DOCX_FONT_ALT_NAMES = {"나눔고딕": "NanumGothic", "나눔바른고딕": "NanumBarunGothic"}

# ── Messages ───────────────────────────────────────────────────────────────
MESSAGES = {
    "hitl_page_break": {
        "ko": "[쪽 나눔] 장과 절 {total}개 중 짧은 절 {short}개 (요소 {limit}개 미만): --page-break chapter|section|none 택일을 유저에게 질의",
        "en": "[page-break] {short} of {total} chapters/sections are short (fewer than {limit} elements): ask the user to choose --page-break chapter|section|none"},
    "lint_heading_skip": {
        "ko": "[헤더 건너뜀] '{text}' (#{prev} 다음에 #{cur})",
        "en": "[heading skip] '{text}' (#{cur} right after #{prev})"},
    "lint_square_alone": {
        "ko": "[□ 단독] '{text}' 아래에 ○ 또는 - 서술이 없음",
        "en": "[□ alone] '{text}' has no ○ or - statement under it"},
    "hitl_long_table": {
        "ko": "[장표] '{title}' {rows}행 표: 유저에게 --long-table engine|split 택일을 질의",
        "en": "[long table] '{title}' {rows}-row table: ask the user to choose --long-table engine|split"},
    "lint_no_caption": {
        "ko": "[표 캡션 없음] 표 앞 줄에 '<표> 제목' 형식 캡션 권장",
        "en": "[no table caption] add a '<표> title' caption line before the table"},
    "lint_footnote_undefined": {
        "ko": "[각주 정의 없음] [^{key}] 참조에 맞는 '[^{key}]: 내용' 정의가 없어 빈 각주로 출력",
        "en": "[footnote undefined] [^{key}] has no '[^{key}]: text' definition and prints as an empty footnote"},
    "lint_footnote_unused": {
        "ko": "[각주 참조 없음] '[^{key}]:' 정의를 참조하는 본문 문단이 없어 출력 안 됨",
        "en": "[footnote unused] no body paragraph references the '[^{key}]:' definition, so it is not printed"},
    "lint_source_no_para": {
        "ko": "[출처 줄 위치] '{text}' 앞에 같은 절의 본문 문단이 없어 ※ 주석 문단으로 출력. 근거 문단 바로 뒤에 둠",
        "en": "[source line position] '{text}' has no body paragraph before it in the same section and prints as a ※ note paragraph. Put it right after the paragraph it supports"},
    "lint_colwidth_alone": {
        "ko": "[열 폭 줄 위치] '{text}' 바로 뒤에 표가 없어 적용 안 됨. 캡션과 표 사이에 둠",
        "en": "[column width line] '{text}' is not followed by a table and is ignored. Put it between the caption and the table"},
    "warn_colwidth_value": {
        "ko": "WARN: 표 '{title}' 열 폭 줄 '{spec}'이 양수 목록이 아니어서 자동 산정으로 조판",
        "en": "WARN: table '{title}' column width line '{spec}' is not a list of positive numbers; automatic sizing used"},
    "warn_colwidth_count": {
        "ko": "WARN: 표 '{title}' 열 폭 값 {n}개가 열 수 {ncol}개와 달라 자동 산정으로 조판",
        "en": "WARN: table '{title}' has {n} column width values for {ncol} columns; automatic sizing used"},
    "warn_colwidth_over": {
        "ko": "WARN: 표 '{title}' 열 폭 합계 {total}%가 {limit}%를 넘어 자동 산정으로 조판",
        "en": "WARN: table '{title}' column widths sum to {total}%, over {limit}%; automatic sizing used"},
    "warn_image_missing": {"ko": "WARN: 이미지 없음 {path}", "en": "WARN: image not found {path}"},
    "err_no_hwpx": {
        "ko": "ERROR: python-hwpx 미설치. `pip install -U python-hwpx` 후 재실행",
        "en": "ERROR: python-hwpx is not installed. Run `pip install -U python-hwpx` and retry"},
    "err_no_docx": {
        "ko": "ERROR: python-docx 미설치. `pip install -U python-docx` 후 재실행",
        "en": "ERROR: python-docx is not installed. Run `pip install -U python-docx` and retry"},
    "err_skeleton_zip": {
        "ko": "ERROR: 스켈레톤 zip 손상 항목 {item}. 양식 파일을 다시 확인",
        "en": "ERROR: skeleton zip has a corrupt entry {item}. Check the form file"},
    "err_skeleton_load": {
        "ko": "ERROR: 스켈레톤 로드 실패 ({err}). python-hwpx 버전 문제 가능성. `pip show python-hwpx` 확인 후 최신 버전 재설치. "
              "이후에도 실패하면 이 스크립트를 최신 API에 맞게 수정 (python-hwpx API로 문서를 새로 조립하는 우회는 결함)",
        "en": "ERROR: failed to load the skeleton ({err}). Likely a python-hwpx version issue: check `pip show python-hwpx` "
              "and reinstall the latest. If it still fails, update this script to the latest API (assembling the document directly with the python-hwpx API is a defect)"},
    "err_missing_styles": {
        "ko": "ERROR: 스켈레톤에 없는 스타일 {names}: 프로파일 수정 또는 `skeleton` 명령으로 스타일 목록 확인",
        "en": "ERROR: styles missing from the skeleton {names}: fix the profile or list the styles with the `skeleton` command"},
    "err_no_skeleton": {"ko": "ERROR: 스켈레톤 없음 {path}", "en": "ERROR: skeleton not found {path}"},
    "warn_no_style": {
        "ko": "WARN: 프로파일에 '{role}' 스타일 없음 → 바탕글로 출력. 파생, 스켈레톤 추가, 기존 계위 흡수 중 유저 택일 필요",
        "en": "WARN: profile has no '{role}' style, using the body style. Ask the user to derive, add to the skeleton, or merge into an existing level"},
    "warn_no_toc_style": {
        "ko": "WARN: 프로파일에 목차 스타일(toc_chapter, toc_section)이 없어 --toc 생략",
        "en": "WARN: the profile has no TOC styles (toc_chapter, toc_section); --toc skipped"},
    "warn_hmerge_overlap": {
        "ko": "WARN: 표 {row}행 {c0}-{c1}열 가로 병합이 세로 병합과 겹쳐 생략",
        "en": "WARN: horizontal merge at row {row}, columns {c0}-{c1} overlaps a vertical merge; skipped"},
    "err_image_ref": {
        "ko": "ERROR: 그림 바이너리 참조 누락 ({path}). python-hwpx media.add_image 반환값 확인 필요",
        "en": "ERROR: picture binary reference missing ({path}). Check the python-hwpx media.add_image return value"},
    "warn_schema": {"ko": "WARN: 스키마 검증 이슈 {n}건", "en": "WARN: {n} schema validation issues"},
    "manifest_fixed": {
        "ko": "이미지 매니페스트 누락 {n}건 등록",
        "en": "Registered {n} image(s) missing from the manifest"},
    "toc_numbers": {
        "ko": "목차 쪽번호 {found}/{total}건 기입 (근사 렌더러 기준)",
        "en": "TOC page numbers filled {found}/{total} (approximate renderer)"},
    "toc_verified": {
        "ko": "목차 쪽번호 대조: 기입값과 재렌더링 쪽 위치 일치 {n}/{total}건",
        "en": "TOC page check: filled numbers match the re-rendered page positions {n}/{total}"},
    "warn_toc_missing": {
        "ko": "WARN: 목차 항목 {n}건의 쪽을 찾지 못해 쪽번호 미기입 {items}: 렌더링 PNG에서 해당 제목 확인",
        "en": "WARN: {n} TOC entries not found in the render, page numbers left blank {items}: check those headings in the rendered PNGs"},
    "warn_toc_stranded": {
        "ko": "WARN: [목차 제목 고립] {n}건 {items}: 제목이 쪽 끝에 있고 첫 본문 줄은 다음 쪽에서 시작. 한/글은 제목을 다음 쪽으로 넘겨 목차 쪽번호가 1 작게 보임. 원고의 해당 제목 앞에 --- 를 두어 맞춤",
        "en": "WARN: [stranded TOC heading] {n} {items}: the heading sits at a page bottom and its first body line starts on the next page. Hangul moves the heading to the next page, so the TOC number shows 1 less. Put --- before that heading in the manuscript"},
    "warn_toc_mismatch": {
        "ko": "WARN: 목차 쪽번호 불일치 {n}건 {items}: 렌더링 PNG에서 해당 제목의 쪽을 확인",
        "en": "WARN: {n} TOC page numbers do not match {items}: check those headings' pages in the rendered PNGs"},
    "warn_toc_numbers": {
        "ko": "WARN: 렌더러 또는 pdftotext 부재, 또는 제목 탐색 실패로 목차 쪽번호 미기입",
        "en": "WARN: TOC page numbers not filled (renderer or pdftotext missing, or headings not found)"},
    "build_ok": {"ko": "OK: {out} (요소 {n}, 각주 {fn})", "en": "OK: {out} ({n} elements, {fn} footnotes)"},
    "err_docx_builtin_only": {
        "ko": "ERROR: DOCX는 내장 양식(chapter, flat)만 지원. 유저 HWPX 양식은 HWPX 산출에만 사용",
        "en": "ERROR: DOCX supports the built-in forms (chapter, flat) only. User HWPX forms apply to HWPX output"},
    "err_format": {
        "ko": "ERROR: 산출 파일 확장자는 .hwpx 또는 .docx",
        "en": "ERROR: the output file extension must be .hwpx or .docx"},
    "err_no_input": {"ko": "ERROR: 입력 파일 없음: {path}", "en": "ERROR: input file not found: {path}"},
    "skeleton_ok": {
        "ko": "OK: {out} ({size} bytes, 구역 {sec})", "en": "OK: {out} ({size} bytes, section {sec})"},
    "skeleton_styles": {"ko": "스타일: {names}", "en": "Styles: {names}"},
    "skeleton_bullets": {"ko": "글머리: {bullets}", "en": "Bullets: {bullets}"},
    "skeleton_profile": {
        "ko": "프로파일 초안: {path}: null 항목은 스타일명을 직접 지정한 뒤 build --profile 로 전달",
        "en": "Profile draft: {path}: fill the null entries with style names, then pass it to build --profile"},
    "builtin_ok": {"ko": "OK: 내장 양식 {form} → {out}", "en": "OK: built-in form {form} -> {out}"},
    "export_ok": {"ko": "OK: {out} ({n}자{extra})", "en": "OK: {out} ({n} chars{extra})"},
    "export_hier": {"ko": ", 계위 복원", "en": ", levels restored"},
    "fill_cells": {"ko": "표 셀: 적용 {ok} 실패 {fail}", "en": "Table cells: applied {ok}, failed {fail}"},
    "fill_cell_failed": {"ko": "  실패: {path} ({reason})", "en": "  failed: {path} ({reason})"},
    "fill_ok": {"ko": "OK: 텍스트 치환 {n}건 → {out}", "en": "OK: {n} text replacements -> {out}"},
    "err_no_rhwp": {
        "ko": "ERROR: rhwp 미확보: references/renderers.md 절차로 확보 후 --rhwp 경로 지정 또는 scripts/rhwp/ 에 배치",
        "en": "ERROR: rhwp not available: obtain it per references/renderers.md, then pass --rhwp or place it in scripts/rhwp/"},
    "err_rhwp_command": {
        "ko": "ERROR: 이 rhwp 버전에 {cmd} 명령이 없음: `rhwp --help`에서 같은 기능의 명령을 찾아 config.py의 값을 교체 "
              "(인자 형식이 다르면 render.py의 호출부도 수정)",
        "en": "ERROR: this rhwp version has no {cmd} command: find the command with the same function in `rhwp --help` "
              "and replace the value in config.py (update the call in render.py if the arguments differ)"},
    "err_rhwp_failed": {
        "ko": "ERROR: rhwp 변환 실패 (문서 결함 신호일 수 있음): {detail}",
        "en": "ERROR: rhwp conversion failed (may signal a document defect): {detail}"},
    "err_no_soffice": {
        "ko": "ERROR: LibreOffice 미확보: references/renderers.md의 설치 절차 참조",
        "en": "ERROR: LibreOffice not available: see the install steps in references/renderers.md"},
    "err_soffice_failed": {
        "ko": "ERROR: LibreOffice 변환 실패: H2Orestart 확장 미설치(HWPX)이거나 문서 결함(요소 순서, 참조 ID) 신호: {detail}",
        "en": "ERROR: LibreOffice conversion failed: H2Orestart extension missing (HWPX) or a document defect (element order, reference IDs): {detail}"},
    "err_no_renderer": {
        "ko": "ERROR: 렌더러 없음: rhwp 또는 LibreOffice(+H2Orestart) 확보 후 재실행 (references/renderers.md)",
        "en": "ERROR: no renderer: obtain rhwp or LibreOffice (+H2Orestart) and retry (references/renderers.md)"},
    "render_ok": {"ko": "OK[{engine}]: {pdf} → {outdir}/ ({n}쪽)", "en": "OK[{engine}]: {pdf} -> {outdir}/ ({n} pages)"},
    "render_pdf_only": {
        "ko": "OK[{engine}]: {pdf} (pdftoppm 부재로 PNG 생략)", "en": "OK[{engine}]: {pdf} (pdftoppm missing, PNG skipped)"},
    "warn_fields_not_updated": {
        "ko": "WARN: LibreOffice 파이썬 연동(uno) 부재로 목차 필드를 갱신하지 않고 렌더링. 목차는 저장된 값으로 표시",
        "en": "WARN: LibreOffice Python bridge (uno) missing; rendered without updating the TOC field. The TOC shows stored values"},
    "check_images": {
        "ko": "이미지: BinData {files}, binItem {items}, 매니페스트 {manifest}, 본문 참조 {refs}",
        "en": "Images: BinData {files}, binItem {items}, manifest {manifest}, body references {refs}"},
    "check_schema": {"ko": "스키마 검증: 이슈 {n}건", "en": "Schema validation: {n} issues"},
    "check_manifest_missing": {"ko": "매니페스트 미등록 이미지: {items}", "en": "Images missing from the manifest: {items}"},
    "check_bin_missing": {"ko": "binItem에 대응하는 BinData 파일 없음: {items}", "en": "No BinData file for binItem: {items}"},
    "check_ref_missing": {"ko": "본문 참조에 대응하는 BinData 없음: {items}", "en": "No BinData for body reference: {items}"},
    "warn_verify_missing": {
        "ko": "WARN: rhwp {cmd} 명령이 이 버전에 없어 생략: `rhwp --help`에서 기대 조건 검증 기능의 명령을 찾아 config.py의 값을 교체",
        "en": "WARN: rhwp has no {cmd} command in this version; skipped. Find the expectation-check command in `rhwp --help` and update config.py"},
    "verify_result": {"ko": "rhwp verify: {verdict} {items}", "en": "rhwp verify: {verdict} {items}"},
    "verify_parse_fail": {"ko": "rhwp verify 출력 해석 실패: {out}", "en": "Could not parse rhwp verify output: {out}"},
    "docx_check_parts": {
        "ko": "DOCX 구성: 문단 {paras}, 표 {tables}, 그림 {images}, 각주 {notes}, 목차 필드 {toc}",
        "en": "DOCX parts: {paras} paragraphs, {tables} tables, {images} images, {notes} footnotes, TOC field {toc}"},
    "docx2md_keys": {
        "ko": "키 = 스타일명|들여쓰기(pt*10)|자동번호|선두기호  →  건수, 표본. 대응 JSON 예: {{\"본문|0||□\": \"square\"}}",
        "en": "key = style|indent(pt*10)|autonumber|leading symbol  ->  count, sample. Mapping JSON example: {{\"Body|0||□\": \"square\"}}"},
    "docx2md_key_line": {"ko": "  {key!r}: {n}건  예) {sample}", "en": "  {key!r}: {n}  e.g. {sample}"},
    "docx2md_roles": {
        "ko": "역할: chapter section subsection ganada square circle dash dot note source skip",
        "en": "Roles: chapter section subsection ganada square circle dash dot note source skip"},
    "docx2md_ok": {
        "ko": "OK: {out} (문단 {paras}, 표 {tables}): 표 캡션 <표> 줄과 그림은 원고에서 보완",
        "en": "OK: {out} ({paras} paragraphs, {tables} tables): add <표> caption lines and figures in the manuscript"},
    "xlsx2md_wide": {
        "ko": "WARN: 시트 '{sheet}' 열 {n}개: 행열 전환 또는 표 분할을 유저에게 질의 (--allow-wide 로 그대로 진행)",
        "en": "WARN: sheet '{sheet}' has {n} columns: ask the user to transpose or split (--allow-wide to keep as is)"},
    "xlsx2md_ok": {
        "ko": "OK: {out} (시트 {n}): 캡션 제목, (단위: ) 줄, 자료: 줄은 원고에서 보완",
        "en": "OK: {out} ({n} sheets): add caption titles, (단위: ) lines and source lines in the manuscript"},
    "fonts_header": {
        "ko": "글꼴 | 설치 여부 | KS X 1001 한자 4,620자 | 렌더링 대체 글꼴 | 확보 경로",
        "en": "Font | installed | KS X 1001 Hanja (4,620) | rendering substitute | where to get it"},
    "fonts_row": {"ko": "{face} | {installed} | {hanja} | {sub} | {source}", "en": "{face} | {installed} | {hanja} | {sub} | {source}"},
    "fonts_hanja_yes": {"ko": "모두 있음", "en": "all present"},
    "fonts_hanja_no": {"ko": "빠짐 (한자가 다른 글꼴이나 빈칸으로 표시됨)", "en": "incomplete (Hanja appear in another font or as blanks)"},
    "src_nanum_auto": {
        "ko": "SIL OFL 1.1 무료 글꼴. 한자가 든 네이버 배포본은 공유마당 안심글꼴 또는 운영체제 패키지(fonts-nanum)로 설치. fonts --setup은 한자 없는 Google Fonts 배포본을 내려받음",
        "en": "free font under SIL OFL 1.1; install the NAVER release with Hanja from the Korea Copyright Commission safe-font service (공유마당 안심글꼴) or an OS package (fonts-nanum). fonts --setup downloads the Google Fonts release, which has no Hanja"},
    "src_nanum_manual": {
        "ko": "SIL OFL 1.1 무료 글꼴. 네이버 배포본을 공유마당 안심글꼴 또는 운영체제 패키지(fonts-nanum)로 설치. Google Fonts 저장소에 없어 fonts --setup이 내려받지 않음",
        "en": "free font under SIL OFL 1.1; install the NAVER release from the Korea Copyright Commission safe-font service (공유마당 안심글꼴) or an OS package (fonts-nanum). It is not in the Google Fonts repository, so fonts --setup does not download it"},
    "fonts_yes": {"ko": "설치됨", "en": "installed"},
    "fonts_no": {"ko": "없음", "en": "missing"},
    "fonts_download": {
        "ko": "내려받기: {name} (SIL Open Font License 1.1, {url})",
        "en": "Downloading: {name} (SIL Open Font License 1.1, {url})"},
    "fonts_download_fail": {
        "ko": "WARN: {name} 내려받기 실패 ({err}). 운영체제 패키지(예: fonts-nanum) 설치로 대체 가능",
        "en": "WARN: failed to download {name} ({err}). Installing an OS package (e.g. fonts-nanum) also works"},
    "fonts_config": {
        "ko": "OK: 대체 글꼴 규칙 {path} 기록 (LibreOffice 렌더링에 적용)",
        "en": "OK: wrote substitution rules to {path} (applies to LibreOffice rendering)"},
    "fonts_no_fc": {
        "ko": "WARN: fontconfig 없는 환경. 대체 글꼴 규칙 생략 (Windows와 macOS는 설치된 원래 글꼴 사용)",
        "en": "WARN: no fontconfig on this system; substitution rules skipped (Windows and macOS use the installed original fonts)"},
    "err_labels_read": {
        "ko": "ERROR: 라벨 파일을 읽지 못함 {path} ({err})",
        "en": "ERROR: cannot read the label file {path} ({err})"},
    "err_labels": {
        "ko": "ERROR: 라벨 파일 {path} 오류 {n}건: {items}. 키와 기본값은 references/layout.md의 라벨 절",
        "en": "ERROR: label file {path} has {n} problem(s): {items}. Keys and defaults are in the Labels section of references/layout.md"},
    "label_unknown": {"ko": "알 수 없는 키 {key}", "en": "unknown key {key}"},
    "label_type": {"ko": "{key} 값은 {kind}", "en": "{key} must be {kind}"},
    "label_kind_str": {"ko": "문자열", "en": "a string"},
    "label_kind_list": {"ko": "빈칸 아닌 문자열의 목록", "en": "a list of non-empty strings"},
    "label_kind_int": {"ko": "정수", "en": "an integer"},
    "label_kind_dict": {"ko": "객체", "en": "an object"},
    "label_format": {
        "ko": "{key} 형식 오류 ({err}). 쓸 수 있는 자리표시 {fields}",
        "en": "{key} is not a valid format ({err}); allowed placeholders {fields}"},
    "label_format_missing": {"ko": "{key}에 {field} 자리표시가 없음", "en": "{key} has no {field} placeholder"},
    "label_empty": {"ko": "{key} 값이 비어 있음", "en": "{key} is empty"},
    "label_seq": {
        "ko": "{key} 값 '{value}'은 Word SEQ 필드 이름으로 쓸 수 없음 (빈칸과 공백 불가). caption 아래 seq를 따로 지정",
        "en": "{key} value '{value}' cannot be a Word SEQ field name (no blanks or spaces); set seq under caption"},
}


# notice for using Hancom's published documents (shown in CLI help and source headers)
NOTICE = {
    "ko": ("본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.\n"
           "한/글, 한컴오피스, HWPX는 한글과컴퓨터의 상표이며 이 도구는 한글과컴퓨터와 제휴 관계가 없는 독립 도구임"),
    "en": ("본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.\n"
           "(This product was developed with reference to Hancom's published HWP document file (.hwp) specification.)\n"
           "Hangul, Hancom Office, and HWPX are trademarks of Hancom Inc. This tool is independent and not affiliated with Hancom Inc."),
}


def msg(msg_key: str, /, **kw) -> str:
    entry = MESSAGES[msg_key]
    return (entry.get(LANG) or entry["ko"]).format(**kw)


# ── Labels ─────────────────────────────────────────────────────────────────
def label(key: str):
    """Active label value of a dotted key (for example 'toc.title')"""
    node = LABELS
    for part in key.split("."):
        node = node[part]
    return node


def caption_marks(kind: str) -> tuple[str, str]:
    """Characters before and after the caption number ('<표 ', '> ')"""
    cap = label(f"caption.{CAPTION_KINDS[kind]}")
    return f"{cap['open']}{cap['label']} ", f"{cap['close']} "


def caption_seq(kind: str) -> str:
    """Word SEQ field name of a caption kind. Without a seq value, the caption label"""
    cap = label(f"caption.{CAPTION_KINDS[kind]}")
    return cap["seq"] or cap["label"]


def set_labels(path: str):
    """Reads a label file and merges it over the defaults. Unknown keys and invalid values stop build with the list of all problems"""
    global LABELS
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        sys.exit(msg("err_labels_read", path=path, err=ex))
    merged = copy.deepcopy(LABEL_DEFAULTS)
    problems = _merge_labels(merged, data, "")
    for key, (fields, required) in LABEL_FORMAT_FIELDS.items():
        fmt = merged[key.split(".")[0]][key.split(".")[1]]
        if fmt is None:
            continue
        try:
            fmt.format(**{f: 1 for f in fields})
        except (KeyError, IndexError, ValueError) as ex:
            problems.append(msg("label_format", key=key, err=ex, fields=" ".join(f"{{{f}}}" for f in fields)))
            continue
        if f"{{{required}}}" not in fmt:
            problems.append(msg("label_format_missing", key=key, field=f"{{{required}}}"))
    if not merged["letters"]["items"]:
        problems.append(msg("label_empty", key="letters.items"))
    for kind, cap in merged["caption"].items():
        seq = cap["seq"] or cap["label"]
        if not seq or any(ch.isspace() for ch in seq):
            problems.append(msg("label_seq", key=f"caption.{kind}." + ("seq" if cap["seq"] else "label"), value=seq))
    if problems:
        sys.exit(msg("err_labels", path=path, n=len(problems), items="; ".join(problems)))
    LABELS = merged


def _merge_labels(base: dict, over, prefix: str) -> list[str]:
    """Merges over into base in place. Lists (notation tokens) are extended, other values replaced. Returns the problems found"""
    if not isinstance(over, dict):
        return [msg("label_type", key=prefix.rstrip(".") or "/", kind=msg("label_kind_dict"))]
    problems = []
    for k, v in over.items():
        key, cur = prefix + k, base.get(k)
        if k not in base:
            problems.append(msg("label_unknown", key=key))
        elif isinstance(cur, dict):
            problems += _merge_labels(cur, v, key + ".")
        elif isinstance(cur, list):
            if isinstance(v, list) and all(isinstance(t, str) and t.strip() for t in v):
                cur += [t for t in v if t not in cur]
            else:
                problems.append(msg("label_type", key=key, kind=msg("label_kind_list")))
        elif isinstance(cur, int) and not isinstance(cur, bool):
            if isinstance(v, int) and not isinstance(v, bool):
                base[k] = v
            else:
                problems.append(msg("label_type", key=key, kind=msg("label_kind_int")))
        elif isinstance(v, str):   # string values; None defaults (formats, seq) also take a string
            base[k] = v
        else:
            problems.append(msg("label_type", key=key, kind=msg("label_kind_str")))
    return problems
