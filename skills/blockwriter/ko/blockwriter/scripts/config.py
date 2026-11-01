"""설정부: 조판 수치, 렌더러, 글꼴 대응, 메시지.
수치를 바꿀 때는 이 파일(조판 규범)과 form.py(양식 모양)만 고친다."""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

LANG = "ko"   # CLI 메시지 언어: ko | en

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 양식별 번호 체계. 스타일 이름은 form.py가 정한다 ─────────────────────────
# numbering: manual은 번호를 본문에 직접 기입, auto는 한/글 개요 번호에 맡김
PROFILE_FORMATS = {
    "chapter": {"numbering": "manual", "chapter_format": "제{n}장 {t}", "section_format": "{c}.{s} {t}",
                "subsection_format": "{c}.{s}.{ss} {t}", "caption_prefix": "{c}-"},
    "flat": {"numbering": "manual", "chapter_format": "{t}", "section_format": "{s}. {t}",
             "subsection_format": "{s}.{ss} {t}", "caption_prefix": ""},
}
PROFILE_DEFAULTS = {"numbering": "manual", "chapter_format": "제{n}장 {t}", "section_format": "{c}.{s} {t}",
                    "subsection_format": "{c}.{s}.{ss} {t}", "caption_prefix": ""}
NON_ROLE_KEYS = tuple(PROFILE_DEFAULTS)

# ── 라벨: build가 문서에 찍는 고정 문구와 파일에 기록하는 언어 태그 ──────────────────
# 기본값은 한국어 값. build --labels 파일.json이 같은 키의 중첩 JSON으로 일부를 덮어쓰며 빠진 키는 기본값 유지
LABEL_DEFAULTS = {
    # 제목 번호 형식. None이면 현재 프로파일의 형식(PROFILE_FORMATS 또는 프로파일 JSON) 유지
    "formats": {"chapter": None, "section": None, "subsection": None},
    "letters": {"items": "가나다라마바사아자차카타파하", "format": "{x}."},   # 가나다 계위: 글자 순서와 번호 형식({x}가 글자)
    "toc": {"title": "목  차"},
    # 캡션 번호부 = open + label + 공백 + 번호 + close + 공백. seq는 Word SEQ 필드 이름 (None이면 label 사용)
    "caption": {"table": {"label": "표", "open": "<", "close": ">", "seq": None},
                "figure": {"label": "그림", "open": "[", "close": "]", "seq": None}},
    # 원고 해석기가 인식하는 표기 토큰. 라벨 파일의 토큰은 여기에 추가되며 기본 토큰을 대체하지 않음
    "notation": {"source": ["출처", "자료", "주"], "unit": ["단위"], "table": ["표"], "figure": ["그림"], "colwidth": ["열 폭"]},
    # DOCX 문서 기본 언어(w:lang). 내장 양식 HWPX의 content.hpf 언어와 스타일 langID(Windows LCID)
    "language": {"latin": "en-US", "east_asia": "ko-KR", "hwpx_package": "ko", "hwpx_style_lcid": 1042},
}
# 괄호로도 쓰는 기본 출처 토큰('(출처)'). '(주)'는 주식회사의 약어이므로 출처 줄로 보지 않음
SOURCE_PAREN_TOKENS = ("출처", "자료")
# 형식별로 쓸 수 있는 자리표시와 반드시 들어갈 자리표시
LABEL_FORMAT_FIELDS = {"formats.chapter": (("n", "t"), "t"), "formats.section": (("c", "s", "t"), "t"),
                       "formats.subsection": (("c", "s", "ss", "t"), "t"), "letters.format": (("x",), "x")}
CAPTION_KINDS = {"TABLE": "table", "PICTURE": "figure"}   # 조판기의 캡션 종류 → 캡션 라벨 키
LABELS = copy.deepcopy(LABEL_DEFAULTS)   # 현재 라벨. set_labels가 교체

XLSX_WIDE_COLS = 6              # 시트 열이 이 값을 넘으면 행열 전환 또는 표 분할을 유저에게 질의

# ── 원고 린트 ──────────────────────────────────────────────────────────────
SHORT_SECTION_ELEMS = 8   # 절당 요소 수가 이 값 미만이면 쪽 나눔 시 여백만 남을 가능성

# ── 표 (HWPUNIT). 표는 ○ 서술의 하위 정보이므로 열 폭을 글자에 맞춰 ○ 계위 안쪽에 두고 정보가 많은 표만 상한까지 넓힘 ──
TABLE_INDENT_MARGIN = 1500      # 본문 폭에서 뺄 계위 들여쓰기 (표 폭 상한 = 본문 폭 - 이 값)
TABLE_MIN_RATIO = 0.5           # 표 폭 하한 (상한 대비). 라벨 2-3열 표의 과소 폭 방지
COL_MIN_W = 3000                # 열 최소 폭 (약 10.6mm)
COL_PAD_W = 1800                # 열별 좌우 여백과 글자 폭 오차 여유
COL_ONE_LINE_W = 12000          # 1줄 보장 폭 (약 42mm, 12pt 한글 10자). 가장 긴 줄이 이 폭을 넘는 열은 2줄 접힘 전제로 축소
COL_WRAP_RATIO = 0.6            # 접힘 전제 축소율
COL_WIDTH_PCT_MAX = 100         # 원고 열 폭 줄의 기준 (표 폭 상한 = 100%). 합계가 이를 넘으면 표가 ○ 계위 밖으로 나감
COL_WIDTH_PCT_TOL = 0.01        # 열 폭 합계의 부동소수 오차 허용 (33.34 + 33.33 + 33.33 등)
COL_WIDTH_PCT_DIGITS = 2        # build가 출력하는 열 폭 %의 소수 자릿수. 출력값을 열 폭 줄에 그대로 옮겨 쓰는 정밀도
COL_WIDTH_NOWRAP_TOL = 2        # 열 폭 줄 합계가 줄바꿈 없는 폭 합계를 이 값(%p) 이상 넘으면 WARN. 넘는 폭은 줄 수를 줄이지 않음
MERGE_LABEL_COLS = 2            # 선행 라벨 열 중 세로 병합 대상 최대 열 수
LONG_TABLE_ROWS = 25            # 초과 시 장표 처리 (쪽 경계 분할과 제목행 반복)
# 가중 길이 단위는 한글 반 자 폭 (CELL_HANGUL_EM의 절반). 글자 폭을 이 단위로 세어 열 폭과 행 줄 수를 산정
WIDE_UNITS = 2                  # 한글, 한자 등 전각 문자의 가중 폭
OTHER_UNITS = 1                 # 폭 표(GLYPH_EM)에 없는 그 밖의 글자의 가중 폭
# 나눔고딕 글자별 폭 (글자 크기 배수). 영문, 숫자, 기호의 실제 폭으로 세어야 좁은 글자(i, l, t)와 넓은 글자(m, w)가 섞인 이름의 폭이 맞음.
# dev/gen_glyph_em.py로 생성하며 값은 보통과 굵게 중 넓은 쪽 (머리글은 굵게)
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
SPACE_EM_HWPX = 0.5             # 한/글 빈칸 폭. 양식 글자 모양이 글꼴 빈칸 폭을 쓰지 않아 글자 크기의 절반 (rhwp 실측 동일)
SPACE_EM_DOCX = 0.28            # Word 빈칸 폭. 나눔고딕 빈칸 글자 폭
DEFAULT_PAGE_BREAK = "chapter"  # --page-break를 지정하지 않은 build의 새 쪽 시작 단위
DEFAULT_LONG_TABLE = "engine"   # --long-table을 지정하지 않은 build의 장표 처리 방식
HEADER_FILL = "#D9D9D9"         # 표 머리글 배경
BORDER_WIDTH = "0.15 mm"        # 셀 선 굵기
BORDER_WIDTH_MM = 0.15
BORDER_COLOR = "#000000"
EDGE_OPEN_SIDES = True          # 표 좌우 바깥선을 비움. 좌측 끝 셀은 왼선, 우측 끝 셀은 오른선 없음
FIGURE_IN_TABLE = True          # 그림을 투명 1열 표에 넣어 그림과 출처가 함께 이동 (캡션은 HWPX 캡션 개체, DOCX 표 뒤 문단)
ROW_BASE_H = 2000               # 1줄 행 높이 (내용에 맞춰 늘어나는 최소값)
ROW_LINE_H = 1400               # 접힘·개행 1줄 추가분
CELL_MARGIN_LR = 510            # 셀 안 좌우 여백 (조판 라이브러리 기본값과 같게 DOCX에도 적용)
CELL_MARGIN_TB = 141            # 셀 안 위아래 여백
CELL_HANGUL_EM = 0.94           # 한글 1자 폭 / 글자 크기. 나눔고딕 실측값이며 가중 길이 단위와 행 높이의 줄 수 추정에 사용
CAPTION_GAP = 850               # 캡션과 표 사이 간격

# ── 그림 (mm, 본문 폭 약 170mm 기준). 좌우를 가득 채운 그림은 본문 계위와 어긋나고 세로형은 한 쪽을 넘긴다
IMG_LANDSCAPE_RATIO = 1.4       # 폭/높이 비율이 이 값 이상이면 가로형
IMG_PORTRAIT_RATIO = 0.8        # 이 값 이하면 세로형, 사이는 정사각형 근방
IMG_LANDSCAPE_W_MM = 140.0
IMG_SQUARE_W_MM = 90.0
IMG_PORTRAIT_H_MM = 110.0
IMG_DEFAULT_DPI = 96.0
IMG_FALLBACK_PX = (800, 600)    # 크기를 읽지 못한 그림의 가정 크기
IMG_URL_TIMEOUT = 20
IMAGE_MIME_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/bmp": "bmp", "image/webp": "webp"}
IMAGE_CONVERT_TO_JPG = ("webp",)
JPEG_QUALITY = 90
HTTP_USER_AGENT = "blockwriter (image fetch for document typesetting)"

# ── 표지와 목차 ────────────────────────────────────────────────────────────
COVER_TOP_LINES = 8             # 표지 제목 위 빈 줄 수
COVER_TITLE_PT = 24
COVER_SUB_PT = 16
COVER_DATE_PT = 14
COVER_ORG_PT = 16
COVER_GAP_LINES = 14            # 일자와 기관 사이 빈 줄 수
from form import TOC_TAB_POS  # noqa: E402  목차 쪽번호 오른쪽 점선 탭 위치 (양식 정의가 기준)
TOC_SECTION_INDENT = 1500       # 목차 절 들여쓰기
TOC_SUB_INDENT = 3000           # 목차 소절 들여쓰기
TOC_MAX_PASSES = 2              # 목차 쪽번호 기입 후 재렌더링 대조에서 불일치가 남을 때 다시 조판하는 최대 횟수
TOC_FIRST_LINE_KEY = 10         # 제목 고립 판정에 쓰는 첫 본문 줄의 앞 글자 수 (빈칸 제외). 줄이 쪽을 넘어가도 시작 쪽에서 찾음
BLOCK_GAP_LINES = 0             # 표·그림 블록 앞뒤 빈 문단 수. 간격은 표 위치·그림 위치 스타일 여백이 담당

# ── HWPX 렌더러 (rhwp) ─────────────────────────────────────────────────────
RHWP_REPO = "https://github.com/edwardkim/rhwp"
# rhwp는 명령 체계가 자주 바뀐다. 아래 이름이 현 버전에 없으면 `rhwp --help`에서 같은 기능의 명령을 찾아 값만 교체
RHWP_PDF_COMMAND = "export-pdf"          # 문서를 PDF로 출력
RHWP_VERIFY_COMMAND = "verify"           # 기대 조건 대조
RHWP_UNKNOWN_COMMAND_MARKERS = ("알 수 없는 명령", "unknown command", "unrecognized")
RHWP_PDF_OUTLINE_FLAG = "--text-as-paths"   # 글꼴 미설치 환경에서 글자를 윤곽선으로 출력. 글자 추출이 필요한 목차 쪽번호 산정에는 쓰지 않음
RHWP_FONT_PATH_FLAG = "--font-path"
RENDER_DPI = 80
# 검수 사본에서 소프트 하이픈(U+00AD) 글머리를 대체할 글리프. 근사 렌더러가 U+00AD를 그리지 않아 - 계위 기호가 빈칸으로 보인다
SOFT_HYPHEN_GLYPH = "-"
LIBREOFFICE_TIMEOUT = 600

# ── 글꼴 ───────────────────────────────────────────────────────────────────
# 문서에는 양식 글꼴 이름을 그대로 기록한다. 아래 표는 그 글꼴이 설치되지 않은 환경에서 검수 렌더링할 때만 쓰는 대체 글꼴
# 나눔바른고딕은 내장 양식(flat 제목) 글꼴이고 나머지는 유저 HWPX 양식에 흔한 Windows·한컴오피스 글꼴
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
# 자유 글꼴 라이선스(SIL OFL 1.1) 글꼴의 내려받기 경로 (Google Fonts 공식 저장소)
# 이 저장소의 나눔고딕과 나눔명조에는 한자가 없음. 나눔명조는 유저 양식의 명조 계열 글꼴을 대신하는 렌더링 대체 글꼴로만 씀
FREE_FONT_BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl"
FREE_FONTS = {
    "NanumGothic": ("nanumgothic", ["NanumGothic-Regular.ttf", "NanumGothic-Bold.ttf", "NanumGothic-ExtraBold.ttf"]),
    "NanumMyeongjo": ("nanummyeongjo", ["NanumMyeongjo-Regular.ttf", "NanumMyeongjo-Bold.ttf", "NanumMyeongjo-ExtraBold.ttf"]),
}
FREE_FONT_LICENSE_FILE = "OFL.txt"
USER_FONT_DIR = os.path.expanduser("~/.local/share/fonts/blockwriter")
FONTCONFIG_FILE = os.path.expanduser("~/.config/fontconfig/conf.d/60-blockwriter.conf")
# KS X 1001 한자 영역(EUC-KR 첫 바이트 0xCA-0xFD, 둘째 바이트 0xA1-0xFE, 4,888자). fonts는 이 중 통합 한자 4,620자가
# 모두 있는지로 글꼴의 한자 포함 여부를 판정. 나머지 268자는 같은 한자의 음이 다른 호환 코드
KSX1001_HANJA_LEAD = range(0xCA, 0xFE)
KSX1001_HANJA_TRAIL = range(0xA1, 0xFF)
CJK_UNIFIED_RANGE = (0x4E00, 0x9FFF)   # 한중일 통합 한자 기본 영역
# fontconfig가 없는 운영체제에서 fonts가 설치 글꼴을 찾는 폴더 (Windows는 모든 사용자용과 사용자별 설치 폴더)
FONT_DIRS = {
    "win32": ["%WINDIR%\\Fonts", "%LOCALAPPDATA%\\Microsoft\\Windows\\Fonts"],
    "darwin": ["/Library/Fonts", "~/Library/Fonts", "/System/Library/Fonts"],
}
FONT_FILE_EXTS = (".ttf", ".otf", ".ttc")
REGULAR_WEIGHT = 400   # 같은 이름의 파일이 여럿이면 보통 굵기 파일로 한자를 판정
# 양식 글꼴의 확보 경로
FONT_SOURCES = {"나눔고딕": "src_nanum_auto", "나눔바른고딕": "src_nanum_manual"}   # 값은 MESSAGES 키

# ── DOCX ───────────────────────────────────────────────────────────────────
DOCX_HEADING_STYLES = {   # 제목 역할 → Word 기본 제목 스타일 (목차 필드와 탐색 창이 인식하는 스타일)
    "chapter": {"chapter": "Heading 1", "section": "Heading 2", "subsection": "Heading 3", "ganada": "Heading 4"},
    "flat": {"chapter": "Title", "section": "Heading 1", "subsection": "Heading 2", "ganada": "Heading 3"},
}
DOCX_FULLWIDTH_BULLET = 1.0     # 전각 글머리 기호 폭 (글자 크기 대비)
DOCX_HALFWIDTH_BULLET = 0.5     # 반각 글머리 기호 폭
DOCX_SPACER_PT = 1              # 표 아래 간격용 빈 문단의 줄 높이
# 제목 책갈피 이름. 밑줄로 시작하는 이름은 Word가 숨은 책갈피로 다룸. 목차 항목의 PAGEREF 필드가 이 책갈피로 제목 쪽을 찾음
DOCX_TOC_BOOKMARK = "_Toc{n:09d}"
# 글꼴 표(fontTable) 기록값. Word는 문서 글꼴이 없는 환경에서 이 정보로 같은 계열의 대체 글꼴을 고른다
# 영문 이름에 Myeongjo가 있으면 roman(명조 계열), 그 외 swiss(고딕 계열)로 기록. 문자 집합은 한글(charset 81)
DOCX_FONT_ALT_NAMES = {"나눔고딕": "NanumGothic", "나눔바른고딕": "NanumBarunGothic"}

# ── 메시지 ─────────────────────────────────────────────────────────────────
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
    "warn_colwidth_nowrap": {
        "ko": "WARN: 표 '{title}' 열 폭 합계 {total}%가 줄바꿈 없는 폭 {nowrap}%를 {tol}%p 이상 넘음. 넘는 폭은 줄 수를 줄이지 않음. 결함 수정용 열 폭 줄이면 합계를 {nowrap}% 이하로 조정. 지정값으로 조판",
        "en": "WARN: table '{title}' column widths sum to {total}%, {tol} percentage points or more above the no-wrap width {nowrap}%. Width beyond it does not reduce line count. For a column width line that fixes a defect, lower the sum to {nowrap}% or less. Typeset with the given values"},
    "info_colwidth": {
        "ko": "INFO: 표 '{title}' ○ 계위 폭 대비 현재 폭 {cur}% (열별 {cur_cols}), 줄바꿈 없는 폭 {nowrap}% (열별 {nowrap_cols})",
        "en": "INFO: table '{title}' as % of the ○ level width: current {cur}% (columns {cur_cols}), no-wrap {nowrap}% (columns {nowrap_cols})"},
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


# 한글과컴퓨터 공개 문서 이용 고지 (CLI 도움말과 소스 머리에 표기)
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


# ── 라벨 ───────────────────────────────────────────────────────────────────
def label(key: str):
    """점으로 이은 키(예 'toc.title')의 현재 라벨 값"""
    node = LABELS
    for part in key.split("."):
        node = node[part]
    return node


def caption_marks(kind: str) -> tuple[str, str]:
    """캡션 번호 앞뒤 문자 ('<표 ', '> ')"""
    cap = label(f"caption.{CAPTION_KINDS[kind]}")
    return f"{cap['open']}{cap['label']} ", f"{cap['close']} "


def caption_seq(kind: str) -> str:
    """캡션 종류의 Word SEQ 필드 이름. seq 값이 없으면 캡션 라벨"""
    cap = label(f"caption.{CAPTION_KINDS[kind]}")
    return cap["seq"] or cap["label"]


def set_labels(path: str):
    """라벨 파일을 읽어 기본값 위에 병합. 알 수 없는 키와 잘못된 값은 문제 목록 전체를 출력하고 build를 중단"""
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
    """over를 base에 제자리 병합. 목록(표기 토큰)은 덧붙이고 그 밖의 값은 교체. 발견한 문제 목록을 반환"""
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
        elif isinstance(v, str):   # 문자열 값. 기본값이 None인 키(formats, seq)도 문자열을 받음
            base[k] = v
        else:
            problems.append(msg("label_type", key=key, kind=msg("label_kind_str")))
    return problems
