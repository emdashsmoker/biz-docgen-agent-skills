#!/usr/bin/env python3
"""deck_source.py: 제안 발표자료(pptx, pdf)를 제안서 원고의 재료로 변환

사용
  python3 deck_source.py parse  발표자료(pptx|pdf) 출력폴더 [--dpi 110]
  python3 deck_source.py grid   출력폴더 쪽
  python3 deck_source.py figure 출력폴더 쪽 [--crop 좌,상,우,하] [--name 이름] [--no-trim]

Why 단일 경로: pptx는 도형, 그룹, SmartArt, 차트, 표가 서로 다른 XML로 흩어져 있어 형식별 파서를 두면 경로가 늘어남.
  pptx를 먼저 PDF로 바꾸면 본문, 표, 내장 이미지, 도식 캡처가 전부 PDF 처리 하나로 귀결.
산출 (출력폴더)
  발표자료.pdf          입력 pdf의 사본 또는 pptx 변환본. 이후 모든 처리의 기준본
  pages/p001.png        쪽 단위 검토용 PNG (저해상도. 그림 삽입에는 figure 명령의 산출을 사용)
  sheets/sheet_01.png   쪽 축소판 모음. 도식 후보를 고를 때 쪽 PNG를 전부 여는 대신 이 파일을 먼저 확인
  img/                  PDF 내장 이미지와 manifest.json (extract_images.py 산출)
  pages/p001_grid.png   grid 명령이 10% 간격 눈금을 덧그린 쪽 PNG. --crop 값을 읽는 용도
  figures/              figure 명령이 PDF에서 고해상도로 다시 그린 도식 캡처
  pages.json            쪽별 제목, 추정 유형, 글자 수, 표와 이미지와 도형 수, 텍스트 복원 글자 수
  원문.md               쪽별 본문과 표 (표 영역의 글자는 표로만 수록)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from enum import Enum

# ── 설정 ─────────────────────────────────────────────────────────────
REVIEW_DPI = 110            # 검토용 쪽 PNG. 글자 판독이 가능한 최소 수준으로 두어 열람 비용을 줄임
FIGURE_DPI = 220            # 삽입용 도식 캡처. 폭 140mm 인쇄에서 계단 현상이 없는 수준
SHEET_COLS, SHEET_ROWS = 4, 3
SHEET_THUMB_WIDTH = 480
SHEET_LABEL_HEIGHT = 22
PDF_CONVERT_TIMEOUT_SEC = 600
TITLE_ZONE_RATIO = 0.30     # 슬라이드 제목은 통상 상단 30% 안에 위치
DIVIDER_MAX_CHARS = 60      # 표지, 간지, 감사 인사 쪽의 글자 수 상한
TABLE_AREA_RATIO = 0.35     # 표가 쪽 면적에서 이 비율 이상이면 표 중심 쪽
DIAGRAM_MIN_DRAWINGS = 15   # 도형(선, 상자, 화살표) 수의 절대 하한
DIAGRAM_MEDIAN_FACTOR = 1.5  # 서식의 머리띠와 바닥글도 도형이므로 문서 중앙값의 이 배수를 넘어야 도식 후보
IMAGE_AREA_RATIO = 0.12     # 내장 이미지 면적 비율이 이 값 이상이면 도식 후보
SHIFT_REPAIR_OFFSET = 0x100  # PowerPoint PDF 내보내기의 ToUnicode 오류. 일부 음절이 0x100 낮은 코드로 기록됨
GARBLE_WARN_RATIO = 0.02    # 비상용 음절이 이 비율을 넘으면 텍스트 레이어 불신
SHIFT_ACCEPT_RARE_RATIO = 0.005  # 복원 후 문서 전체의 비상용 음절 비율이 이 값 이하일 때만 0x100 밀림 가설을 채택
BOILERPLATE_PAGE_RATIO = 0.4  # 전체 쪽의 이 비율 이상에서 반복되는 줄은 머리글과 바닥글로 보고 제거
BOILERPLATE_MIN_PAGES = 5     # 쪽수가 적은 문서에서 본문 줄을 머리글로 오인하지 않기 위한 하한
BULLET_ONLY_RE = r"^[•·▪■□○●◦§üØ✓ü\-–]+$"   # 글머리 기호만 있는 줄. PDF는 글머리와 본문을 다른 줄로 내보냄
PAGE_NUMBER_RE = r"^\d{1,3}$"
LONG_TOKEN_SYLLABLES = 8    # 띄어쓰기가 살아 있는 한국어 어절은 8음절 이상이 드묾
LONG_TOKEN_WARN_RATIO = 0.15  # 긴 어절 비율이 이 값을 넘으면 공백이 빠진 텍스트 레이어
FRAME_TABLE_AREA_RATIO = 0.85  # 쪽 전체를 덮는 표는 슬라이드 서식의 틀을 표로 오인한 결과
TABLE_MIN_FILLED_RATIO = 0.40  # 빈 칸이 대부분인 표는 도형 배치를 표로 오인한 결과
MAX_OBJECT_DEPTH = 15       # 도형 묶음(Form XObject) 안의 객체까지 찾는 깊이
POINTS_PER_INCH = 72        # PDF 좌표 단위. 렌더 배율 = DPI ÷ 72
GRID_STEP_PERCENT = 10      # 눈금 간격. --crop 값은 눈금에서 읽은 백분율
GRID_COLOR = (220, 0, 0)
TRIM_TOLERANCE = 12         # 여백 제거 시 배경색과 같은 색으로 보는 채널 차이
RECOMPRESSOR_PRODUCERS = ("ghostscript", "ilovepdf", "smallpdf", "pdfcompressor", "sejda")  # 용량 압축과 재저장 도구의 producer 표지 (안내 문구용. 중단 판정은 텍스트 검사가 담당)
METRIC_COMPATIBLE_FONTS = ("arial", "calibri", "cambria", "times new roman", "courier new")  # LibreOffice가 글자 폭이 같은 대체 글꼴(Liberation, Carlito, Caladea)로 바꾸므로 배치가 유지됨
EXIT_GARBLED = 2            # 텍스트 레이어 불완전으로 중단했음을 호출부가 구분하기 위한 종료 코드
F_PDF, F_PAGES_JSON, F_TEXT = "발표자료.pdf", "pages.json", "원문.md"
D_PAGES, D_SHEETS, D_IMG, D_FIGURES = "pages", "sheets", "img", "figures"


def say(*parts) -> None:
    """Why: stdout을 head로 자르는 호출에서 BrokenPipe로 중단되면 뒤따르는 파일 산출(내장 이미지, 상태 기록)이 누락됨"""
    try:
        print(*parts, flush=True)
    except BrokenPipeError:
        sys.stdout = open(os.devnull, "w")


class PageKind(str, Enum):
    DIVIDER = "간지"
    EMPTY = "빈 쪽"       # 본문 서식의 도형만 있고 내용이 없는 쪽. 작성 중인 자료의 미완성 쪽
    IMAGE = "이미지 쪽"   # 글자가 거의 없고 이미지가 큰 쪽. 배경 그림을 깐 표지와 간지일 수도, 표나 재무제표를 그림으로 붙인 내용 쪽일 수도 있음
    TABLE = "표"
    DIAGRAM = "도식 후보"
    TEXT = "본문"


# ── PDF 확보 ─────────────────────────────────────────────────────────
def substituted_fonts(pptx: str) -> list[str]:
    """pptx가 지정한 글꼴 중 이 환경에 없는 글꼴. Why: 대체 글꼴은 글자 폭이 달라 변환본의 줄바꿈과 도식 안 글자 넘침을 만듦"""
    if not shutil.which("fc-list") or not zipfile.is_zipfile(pptx):
        return []
    used = set()
    with zipfile.ZipFile(pptx) as zf:
        for name in zf.namelist():
            # 테마 파일은 쓰지 않는 문자권별 글꼴표(태국어, 크메르어 등)를 담고 있어 제외. 슬라이드 본문이 지정한 글꼴만 확인
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                used.update(re.findall(r'typeface="([^"+][^"]*)"', zf.read(name).decode("utf-8", "replace")))
    installed = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout.lower()
    return sorted(f for f in used if f.lower() not in installed and f.lower() not in METRIC_COMPATIBLE_FONTS)


def to_pdf(src: str, out_dir: str) -> str:
    """입력을 기준본 PDF로 통일. pdf는 복사, pptx는 LibreOffice로 변환"""
    target = os.path.join(out_dir, F_PDF)
    if not os.path.isfile(src):
        sys.exit(f"ERROR: 입력 파일 없음 {src}")
    ext = os.path.splitext(src)[1].lower()
    if ext == ".pdf":
        shutil.copyfile(src, target)
        return target
    if ext not in (".pptx", ".ppt"):
        sys.exit(f"ERROR: 지원하지 않는 입력 형식 {ext} (pptx, pdf)")
    missing = substituted_fonts(src)
    if missing:
        say(f"  WARN 이 환경에 없는 글꼴 {len(missing)}종 {missing[:5]}. 본문 추출에는 영향 없음. 대체 글꼴은 글자 폭이 달라 도식 안 글자가 넘칠 수 있으므로 "
            "도식 캡처 쪽은 캡처 결과를 확인. 넘침이 있는 쪽은 PowerPoint에서 저장한 PDF를 받아 figure --pdf로 캡처")
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("ERROR: LibreOffice 부재로 pptx를 PDF로 변환하지 못함. "
                 "LibreOffice 설치 후 재실행하거나 PowerPoint에서 PDF로 저장한 파일을 입력으로 제출")
    with tempfile.TemporaryDirectory() as tmp:
        # Why 별도 프로필: 기존 soffice 프로세스나 잠긴 프로필과 충돌하면 변환이 무응답으로 끝남
        cmd = [soffice, f"-env:UserInstallation=file://{tmp}/profile", "--headless",
               "--convert-to", "pdf", "--outdir", tmp, os.path.abspath(src)]
        subprocess.run(cmd, check=False, capture_output=True, timeout=PDF_CONVERT_TIMEOUT_SEC)
        made = os.path.join(tmp, os.path.splitext(os.path.basename(src))[0] + ".pdf")
        if not os.path.exists(made):
            sys.exit("ERROR: pptx의 PDF 변환 실패. PowerPoint에서 PDF로 저장한 파일을 입력으로 제출")
        shutil.move(made, target)
    return target


# ── 텍스트 ───────────────────────────────────────────────────────────
def _is_common_hangul(ch: str) -> bool:
    # Why 길이 판정: 파이썬 euc-kr 코덱은 KS X 1001 밖의 음절도 8바이트 조합열로 부호화하므로 예외가 나지 않음
    return len(ch.encode("euc-kr", "ignore")) == 2


def repair_shifted_hangul(text: str) -> tuple[str, int, int, int]:
    """비상용 한글 음절 중 +0x100이 상용 음절인 글자를 복원. 반환은 (본문, 복원 글자 수, 복원 불가 비상용 글자 수, 한글 글자 수)"""
    out, fixed, hangul, rare = [], 0, 0, 0
    for ch in text:
        if "가" <= ch <= "힣":
            hangul += 1
            if not _is_common_hangul(ch):
                cand = chr(ord(ch) + SHIFT_REPAIR_OFFSET)
                if cand <= "힣" and _is_common_hangul(cand):
                    ch, fixed = cand, fixed + 1
                else:
                    rare += 1
        out.append(ch)
    return "".join(out), fixed, rare, hangul


def clean_lines(lines: list[str], boilerplate: set[str]) -> list[str]:
    """머리글과 바닥글, 쪽 번호를 제거하고 글머리 기호만 있는 줄을 다음 줄과 합침"""
    out, pending_bullet = [], False
    for ln in lines:
        if ln in boilerplate or re.match(PAGE_NUMBER_RE, ln):
            continue
        if re.match(BULLET_ONLY_RE, ln):
            pending_bullet = True
            continue
        if out and out[-1].removeprefix("- ") == ln:
            continue  # 그림자와 윤곽 효과를 준 글자는 PDF에 같은 줄로 두 번 기록됨
        out.append(("- " if pending_bullet else "") + ln)
        pending_bullet = False
    return out


def find_boilerplate(pages: list[dict]) -> set[str]:
    if len(pages) < BOILERPLATE_MIN_PAGES:
        return set()
    seen = Counter(ln for p in pages for ln in set(p["lines"]))
    return {ln for ln, n in seen.items() if n / len(pages) >= BOILERPLATE_PAGE_RATIO}


def finalize_text(pages: list[dict]) -> bool:
    """문서 단위 후처리. 반환은 0x100 밀림 가설의 채택 여부
    Why 문서 단위: 글자 코드 오류는 내보내기 방식에서 생기므로 문서 전체에 같은 유형으로 나타남.
      밀림이 아닌 다른 유형의 오류에 복원을 적용하면 오자를 다른 오자로 바꿀 뿐이므로 복원 후 비상용 음절이 사라질 때만 채택"""
    boilerplate = find_boilerplate(pages)
    fixed_total = rare_total = hangul_total = 0
    for p in pages:
        p["lines"] = clean_lines(p["lines"], boilerplate)
        raw = "\n".join(p["lines"] + p["table_md"] + [p["title"]])
        _, fixed, rare, hangul = repair_shifted_hangul(raw)
        p["_fixed"], p["_rare"], p["_hangul"] = fixed, rare, hangul
        fixed_total, rare_total, hangul_total = fixed_total + fixed, rare_total + rare, hangul_total + hangul
    accept = fixed_total > 0 and rare_total / max(1, hangul_total) <= SHIFT_ACCEPT_RARE_RATIO
    for p in pages:
        fixed, rare, hangul = p.pop("_fixed"), p.pop("_rare"), p.pop("_hangul")
        if accept:
            p["lines"] = [repair_shifted_hangul(ln)[0] for ln in p["lines"]]
            p["table_md"] = [repair_shifted_hangul(md)[0] for md in p["table_md"]]
            p["title"] = repair_shifted_hangul(p["title"])[0]
        p["repaired"] = fixed if accept else 0
        p["body"] = "\n".join(p["lines"])
        p["garbled"] = (rare if accept else rare + fixed) / max(1, hangul) > GARBLE_WARN_RATIO or p["repaired"] > 0
        p["unspaced"] = spaces_missing(p["body"])
        p["chars"] = len(p["body"].replace("\n", "")) + sum(len(t) for t in p["table_md"])
        del p["lines"]
    return accept


def spaces_missing(text: str) -> bool:
    tokens = re.findall(r"[가-힣]+", text)
    long_tokens = sum(1 for t in tokens if len(t) >= LONG_TOKEN_SYLLABLES)
    return bool(tokens) and long_tokens / len(tokens) > LONG_TOKEN_WARN_RATIO


def _inside(inner, outer) -> bool:
    cx, cy = (inner[0] + inner[2]) / 2, (inner[1] + inner[3]) / 2
    return outer[0] <= cx <= outer[2] and outer[1] <= cy <= outer[3]


def page_tables(page) -> list[tuple[tuple, str]]:
    """(영역, 마크다운 표) 목록. 영역은 (좌, 상, 우, 하). 표 인식 실패는 빈 목록으로 처리하여 본문 추출을 막지 않음"""
    found = []
    try:
        tables = page.find_tables()
    except Exception:
        return found
    page_area = _area(page_box(page)) or 1.0
    for tb in tables:
        if _area(tb.bbox) / page_area >= FRAME_TABLE_AREA_RATIO:
            continue
        rows = [[(c or "").replace("\n", "<br>").replace("|", "/").strip() for c in r] for r in tb.extract()]
        rows = [r for r in rows if any(r)]
        cells = [c for r in rows for c in r]
        if len(rows) < 2 or len(rows[0]) < 2 or sum(1 for c in cells if c) / len(cells) < TABLE_MIN_FILLED_RATIO:
            continue
        md = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
        md += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        found.append((tuple(tb.bbox), "\n".join(md)))
    return found


def page_title(boxes: list[dict], page_height: float, body_lines: list[str]) -> str:
    """상단 영역에서 가장 큰 글자의 줄을 제목으로 추정. 없으면 본문 첫 줄
    같은 높이와 같은 크기의 조각(번호와 제목 등)은 왼쪽부터 이어 붙여 한 줄로 봄. 크기가 같은 줄이 여럿이면 위쪽 줄을 선택"""
    limit = page_height * TITLE_ZONE_RATIO
    rows: dict[tuple, list] = {}
    for box in boxes:
        for top, x0, text, size in box["lines"]:
            if top <= limit and text:
                rows.setdefault((round(top), round(size, 1)), []).append((x0, text))
    best = None
    for (top, size), parts in rows.items():
        text = squeeze(" ".join(t for _, t in sorted(parts)))
        if len(text) >= 2 and (best is None or size > best[0] or (size == best[0] and top < best[1])):
            best = (size, top, text)
    return best[2] if best else (body_lines[0] if body_lines else "")


def classify(page: dict, diagram_threshold: float) -> PageKind:
    # Why 도형 수 조건: 글자가 윤곽선으로 저장된 PDF는 본문 쪽도 글자 수가 적게 잡힘
    if page["chars"] < DIVIDER_MAX_CHARS and page["table_area"] == 0 and page["drawings"] < diagram_threshold:
        if page["image_area"] >= IMAGE_AREA_RATIO:
            return PageKind.IMAGE
        # 간지는 본문 서식을 쓰지 않아 도형이 거의 없음. 도형이 서식 수준으로 있는데 글자가 없으면 내용을 채우지 않은 쪽
        return PageKind.EMPTY if page["drawings"] >= DIAGRAM_MIN_DRAWINGS and not page["garbled"] else PageKind.DIVIDER
    if page["table_area"] >= TABLE_AREA_RATIO:
        return PageKind.TABLE
    if page["drawings"] >= diagram_threshold or page["image_area"] >= IMAGE_AREA_RATIO:
        return PageKind.DIAGRAM
    return PageKind.TEXT


def _area(box) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def squeeze(line: str) -> str:
    """연속 공백을 1칸으로 줄임. Why: pdfminer는 공백 글자와 글자 간격을 함께 공백으로 옮겨 2칸 공백을 만듦"""
    return re.sub(r"[ \t]{2,}", " ", line).strip()


def page_box(page) -> tuple:
    return (0.0, 0.0, float(page.width), float(page.height))


def text_boxes(page) -> list[dict]:
    """글상자 목록. 항목은 box(쪽 상단 기준 좌, 상, 우, 하), text(본문), lines(줄마다 상단 위치, 왼쪽 위치, 본문, 최대 글자 크기)
    정렬은 위에서 아래, 왼쪽에서 오른쪽
    Why 글상자 단위: 슬라이드의 나란한 글상자를 한 줄로 합치지 않도록 pdfminer의 배치 분석 결과를 사용"""
    from pdfminer.layout import LTChar, LTFigure, LTTextBox, LTTextLine
    height = float(page.height)
    boxes = []

    def walk(objs):
        for obj in objs:
            if isinstance(obj, LTTextBox):
                lines = [(height - ln.y1, ln.x0, squeeze(ln.get_text()),
                          max((c.size for c in ln if isinstance(c, LTChar)), default=0))
                         for ln in obj if isinstance(ln, LTTextLine)]
                boxes.append({"box": (obj.x0, height - obj.y1, obj.x1, height - obj.y0),
                              "text": obj.get_text(), "lines": lines})
            elif isinstance(obj, LTFigure):
                walk(obj)
    walk(page.layout)
    return sorted(boxes, key=lambda b: (round(b["box"][1], 1), b["box"][0]))


def count_paths(pdfium_page) -> int:
    """벡터 경로(선, 상자, 화살표) 객체의 수. 도형 묶음(Form XObject) 안의 경로도 셈"""
    import pypdfium2.raw as pdfium_c
    return len(list(pdfium_page.get_objects(filter=(pdfium_c.FPDF_PAGEOBJ_PATH,), max_depth=MAX_OBJECT_DEPTH)))


def parse_page(page, pdfium_page) -> dict:
    """page는 pdfplumber 쪽(본문, 표, 이미지 위치), pdfium_page는 pypdfium2 쪽(벡터 경로 수)"""
    tables = page_tables(page)
    boxes = [b for b, _ in tables]
    text_items = text_boxes(page)
    lines = []
    for item in text_items:
        if any(_inside(item["box"], b) for b in boxes):
            continue  # 표 안의 글자는 제외 (표는 아래에서 표로 수록)
        lines += [squeeze(ln) for ln in item["text"].splitlines() if ln.strip()]
    table_mds = [md for _, md in tables]
    title = page_title(text_items, float(page.height), lines)
    page_area = _area(page_box(page)) or 1.0
    image_boxes = [(i["x0"], i["top"], i["x1"], i["bottom"]) for i in page.images]
    image_area = sum(_area(b) for b in image_boxes) / page_area
    drawings = count_paths(pdfium_page)
    return {"title": title, "kind": "", "chars": 0, "table_area": round(sum(_area(b) for b in boxes) / page_area, 2),
            "image_area": round(image_area, 2), "tables": len(table_mds),
            "images": len(image_boxes), "drawings": drawings,
            "repaired": 0, "garbled": False, "unspaced": False, "lines": lines, "body": "", "table_md": table_mds}


# ── 쪽 PNG와 축소판 모음 ─────────────────────────────────────────────
def render_pages(pdf: str, out_dir: str, dpi: int) -> list[str]:
    import pypdfium2 as pdfium
    os.makedirs(os.path.join(out_dir, D_PAGES), exist_ok=True)
    paths = []
    doc = pdfium.PdfDocument(pdf)
    try:
        for i in range(len(doc)):
            path = os.path.join(out_dir, D_PAGES, f"p{i + 1:03d}.png")
            doc[i].render(scale=dpi / POINTS_PER_INCH).to_pil().save(path)
            paths.append(path)
    finally:
        doc.close()
    return paths


def contact_sheets(page_pngs: list[str], out_dir: str) -> int:
    from PIL import Image, ImageDraw
    os.makedirs(os.path.join(out_dir, D_SHEETS), exist_ok=True)
    per_sheet = SHEET_COLS * SHEET_ROWS
    count = 0
    for start in range(0, len(page_pngs), per_sheet):
        chunk = page_pngs[start:start + per_sheet]
        thumbs = []
        for p in chunk:
            im = Image.open(p).convert("RGB")
            thumbs.append(im.resize((SHEET_THUMB_WIDTH, round(im.height * SHEET_THUMB_WIDTH / im.width))))
        cell_h = max(t.height for t in thumbs) + SHEET_LABEL_HEIGHT
        rows = -(-len(chunk) // SHEET_COLS)
        sheet = Image.new("RGB", (SHEET_COLS * SHEET_THUMB_WIDTH, rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for k, t in enumerate(thumbs):
            x, y = (k % SHEET_COLS) * SHEET_THUMB_WIDTH, (k // SHEET_COLS) * cell_h
            draw.text((x + 6, y + 4), f"p{start + k + 1}", fill="black")
            sheet.paste(t, (x, y + SHEET_LABEL_HEIGHT))
        count += 1
        sheet.save(os.path.join(out_dir, D_SHEETS, f"sheet_{count:02d}.png"))
    return count


# ── 산출 기록 ────────────────────────────────────────────────────────
def write_text(out_dir: str, src: str, pages: list[dict]) -> None:
    repaired = sum(p["repaired"] for p in pages)
    layer = "불완전 (글자 누락과 오자 가능. 쪽 PNG가 기준이고 이 파일은 보조 자료)" if text_layer_unreliable(pages) else "정상"
    out = ["# 발표자료 원문", f"- 입력 파일 {os.path.basename(src)}", f"- 쪽수 {len(pages)}",
           f"- 텍스트 레이어 {layer}", f"- 글자 코드 자동 복원 {repaired}자", ""]
    for n, p in enumerate(pages, 1):
        out.append(f"## p{n} {p['title']}")
        note = (", 텍스트 불완전" if p["garbled"] else "") + (", 공백 누락(띄어쓰기를 복원하여 이관)" if p["unspaced"] else "")
        out.append(f"- (추정 유형) {p['kind']}, 글자 {p['chars']}, 표 {p['tables']}, 이미지 {p['images']}, 도형 {p['drawings']}{note}")
        out += ["", p["body"], ""]
        for md in p["table_md"]:
            out += [md, ""]
    open(os.path.join(out_dir, F_TEXT), "w", encoding="utf-8").write("\n".join(out))


def text_layer_unreliable(pages: list[dict]) -> bool:
    """내보내기 방식은 문서 전체에 같으므로 한 쪽이라도 불완전하면 문서 전체를 불완전으로 봄"""
    return any(p["garbled"] for p in pages)


def write_manifest(out_dir: str, pages: list[dict]) -> None:
    slim = [{"page": n, **{k: v for k, v in p.items() if k not in ("body", "table_md")}} for n, p in enumerate(pages, 1)]
    json.dump(slim, open(os.path.join(out_dir, F_PAGES_JSON), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def extract_embedded_images(pdf: str, out_dir: str) -> None:
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extract_images.py")
    done = subprocess.run([sys.executable, script, pdf, os.path.join(out_dir, D_IMG)], capture_output=True, text=True)
    first = (done.stdout or done.stderr).strip().splitlines()
    say("  내장 이미지:", first[0] if first else "추출 결과 없음")


def probe_text_layer(doc) -> tuple[bool, str]:
    """쪽 렌더링 전에 텍스트 레이어를 검사. 반환은 (불완전 여부, 안내 문구)
    Why 선행 검사: 용량 압축 도구로 재저장한 PDF는 글자가 임의 코드로 바뀌거나 윤곽선이 되어 본문 추출이 무의미해짐.
      수십 쪽을 렌더링한 뒤에 알리면 시간과 열람 비용을 이미 쓴 뒤이므로 가장 먼저 판정"""
    text = "\n".join((page.extract_text() or "") for page in doc.pages)
    _, fixed, rare, hangul = repair_shifted_hangul(text)
    # Why 오자만 중단 사유: 공백만 빠진 본문은 글자가 온전하여 띄어쓰기 복원으로 이관 가능. 다른 음절로 바뀐 본문은 복원 불가
    if (fixed + rare) / max(1, hangul) <= GARBLE_WARN_RATIO:
        return False, ""
    producer = (doc.metadata.get("Producer") or "").strip()
    cause = f"producer가 '{producer}'이므로 용량 압축이나 재저장을 거친 파일로 추정" if any(
        k in producer.lower().replace(" ", "") for k in RECOMPRESSOR_PRODUCERS) else f"producer '{producer or '미상'}'"
    detail = f"한글 {hangul}자 중 비상용 음절 {fixed + rare}자, 공백 누락 {'있음' if spaces_missing(text) else '없음'}"
    return True, f"{cause} (수정 시각 {doc.metadata.get('ModDate') or '미상'}). {detail}"


def parse(src: str, out_dir: str, dpi: int = REVIEW_DPI, allow_garbled: bool = False) -> list[dict]:
    import pdfplumber
    os.makedirs(out_dir, exist_ok=True)
    pdf = to_pdf(src, out_dir)
    import pypdfium2 as pdfium
    doc = pdfplumber.open(pdf, laparams={"all_texts": True})  # all_texts: 도형 묶음 안의 글자도 글상자로 분석
    broken, reason = probe_text_layer(doc)
    if broken:
        say(f"경고: 텍스트 레이어 불완전. {reason}")
        if not allow_garbled:
            say("중단: 본문 추출이 불가능한 PDF. 유저에게 pptx 원본 또는 압축 전 PDF(PowerPoint에서 직접 저장한 파일)를 요청. "
                  "원본이 없어 쪽 PNG 판독으로 진행하기로 유저가 정한 경우에만 --allow-garbled로 재실행")
            doc.close()
            sys.exit(EXIT_GARBLED)
    vector_doc = pdfium.PdfDocument(pdf)
    try:
        pages = [parse_page(page, vector_doc[i]) for i, page in enumerate(doc.pages)]
    finally:
        vector_doc.close()
        doc.close()
    finalize_text(pages)
    threshold = max(DIAGRAM_MIN_DRAWINGS, DIAGRAM_MEDIAN_FACTOR * statistics.median(p["drawings"] for p in pages))
    for p in pages:
        p["kind"] = classify(p, threshold).value
    sheets = contact_sheets(render_pages(pdf, out_dir, dpi), out_dir)
    write_text(out_dir, src, pages)
    write_manifest(out_dir, pages)
    kinds = {k.value: sum(1 for p in pages if p["kind"] == k.value) for k in PageKind}
    say(f"OK: {pdf} 쪽수 {len(pages)}, 유형 {kinds}, 축소판 모음 {sheets}장, 텍스트 복원 {sum(p['repaired'] for p in pages)}자")
    unspaced = [n for n, p in enumerate(pages, 1) if p["unspaced"]]
    if unspaced:
        say(f"  WARN 공백 누락 쪽 {len(unspaced)}개 {unspaced[:12]}{' 외' if len(unspaced) > 12 else ''}. 글자는 온전하므로 띄어쓰기를 복원하여 이관")
    empty = [n for n, p in enumerate(pages, 1) if p["kind"] == PageKind.EMPTY.value]
    if empty:
        say(f"  WARN 내용이 빈 쪽 {empty}. 작성 중인 자료로 추정. 유저에게 쪽 번호를 알리고 채울 내용을 확인")
    if text_layer_unreliable(pages):
        say("  WARN 텍스트 레이어 불완전 (글자 누락, 오자, 공백 누락). 쪽 PNG를 기준으로 판독하고 원문.md는 보조 자료로 사용")
    extract_embedded_images(pdf, out_dir)
    return pages


# ── 도식 캡처 ────────────────────────────────────────────────────────
def trim_margin(image):
    """네 귀퉁이 색을 배경으로 보고 같은 색의 바깥 여백을 제거"""
    from PIL import Image, ImageChops
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
    diff = ImageChops.difference(rgb, background).point(lambda v: 255 if v > TRIM_TOLERANCE else 0)
    box = diff.getbbox()
    return rgb.crop(box) if box else rgb


def grid(out_dir: str, page_no: int) -> str:
    """쪽 PNG에 백분율 눈금을 덧그림. Why: 축소판에서 어림한 자르기 값은 빗나가기 쉬워 재시도가 반복됨"""
    from PIL import Image, ImageDraw
    src = os.path.join(out_dir, D_PAGES, f"p{page_no:03d}.png")
    if not os.path.exists(src):
        sys.exit(f"ERROR: {src} 부재. parse를 먼저 실행")
    image = Image.open(src).convert("RGB")
    draw = ImageDraw.Draw(image)
    for percent in range(GRID_STEP_PERCENT, 100, GRID_STEP_PERCENT):
        x, y = image.width * percent // 100, image.height * percent // 100
        draw.line([(x, 0), (x, image.height)], fill=GRID_COLOR, width=1)
        draw.line([(0, y), (image.width, y)], fill=GRID_COLOR, width=1)
        draw.text((x + 3, 2), str(percent), fill=GRID_COLOR)
        draw.text((2, y + 2), str(percent), fill=GRID_COLOR)
    path = os.path.join(out_dir, D_PAGES, f"p{page_no:03d}_grid.png")
    image.save(path)
    say(f"OK: {path}")
    return path


def figure(out_dir: str, page_no: int, crop: str | None, name: str | None, trim: bool = True, pdf: str | None = None) -> str:
    """쪽 전체 또는 일부를 PDF에서 고해상도로 다시 그려 저장. crop은 쪽 크기에 대한 백분율 좌,상,우,하
    pdf는 캡처 원천의 교체. pptx 변환본에서 글자가 넘친 도식을 PowerPoint 저장 PDF에서 캡처할 때 사용 (쪽 번호가 같다는 전제)"""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf or os.path.join(out_dir, F_PDF))
    if not 1 <= page_no <= len(doc):
        sys.exit(f"ERROR: 쪽 번호 {page_no}가 범위(1-{len(doc)}) 밖")
    page = doc[page_no - 1]
    width, height = page.get_size()
    margins = (0, 0, 0, 0)  # 좌, 하, 우, 상에서 잘라낼 폭 (포인트)
    if crop:
        try:
            left, top, right, bottom = (float(v) / 100 for v in crop.split(","))
        except ValueError:
            sys.exit("ERROR: --crop 형식은 좌,상,우,하 백분율 (예: 5,20,95,88)")
        if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
            sys.exit("ERROR: --crop 값은 0-100 범위에서 좌<우, 상<하")
        margins = (width * left, height * (1 - bottom), width * (1 - right), height * top)
    image = page.render(scale=FIGURE_DPI / POINTS_PER_INCH, crop=margins).to_pil().convert("RGB")
    doc.close()
    if trim:
        image = trim_margin(image)
    os.makedirs(os.path.join(out_dir, D_FIGURES), exist_ok=True)
    safe = "".join(c for c in (name or "") if c.isalnum() or c in "-_")
    path = os.path.join(out_dir, D_FIGURES, f"p{page_no:03d}" + (f"_{safe}" if safe else "") + ".png")
    image.save(path)
    say(f"OK: {path} {image.width}x{image.height}")
    return path


def main():
    ap = argparse.ArgumentParser(description="제안 발표자료(pptx, pdf) → 원고 재료")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse")
    p.add_argument("input")
    p.add_argument("out")
    p.add_argument("--dpi", type=int, default=REVIEW_DPI)
    p.add_argument("--allow-garbled", action="store_true", help="텍스트 레이어가 불완전해도 쪽 PNG 판독 전제로 진행 (유저 결정 시에만)")
    p = sub.add_parser("grid")
    p.add_argument("out")
    p.add_argument("page", type=int)
    p = sub.add_parser("figure")
    p.add_argument("out")
    p.add_argument("page", type=int)
    p.add_argument("--crop")
    p.add_argument("--name")
    p.add_argument("--no-trim", action="store_true")
    p.add_argument("--pdf", help="캡처 원천 PDF의 교체 (PowerPoint 저장본)")
    a = ap.parse_args()
    if a.cmd == "parse":
        parse(a.input, a.out, a.dpi, a.allow_garbled)
    elif a.cmd == "grid":
        grid(a.out, a.page)
    else:
        figure(a.out, a.page, a.crop, a.name, not a.no_trim, a.pdf)


if __name__ == "__main__":
    main()
