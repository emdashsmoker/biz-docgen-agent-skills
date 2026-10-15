"""검수용 렌더링(HWPX는 rhwp 또는 LibreOffice+H2Orestart, DOCX는 LibreOffice)과 대체 글꼴 설정.
렌더러와 글꼴은 스킬에 포함하지 않고 실행 환경에 설치된 것을 찾아 쓴다."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from enum import Enum

import config as C
from config import msg

LO_HELPER = os.path.join(C.SCRIPT_DIR, "lo_convert.py")


# ── 렌더러 탐색 ────────────────────────────────────────────────────────────
def find_rhwp() -> str | None:
    for cand in (os.path.join(C.SCRIPT_DIR, "rhwp", "rhwp"), os.path.join(C.SCRIPT_DIR, "rhwp", "rhwp.exe"),
                 shutil.which("rhwp"), os.path.expanduser("~/.local/bin/rhwp")):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def rhwp_supports(rhwp: str, command: str, flag: str | None = None) -> bool:
    """명령과 옵션의 존재를 도움말 출력으로 확인. 버전마다 CLI가 달라질 수 있다."""
    res = subprocess.run([rhwp, command, "--help"], capture_output=True, text=True)
    text = res.stdout + res.stderr
    # 미지 명령에도 전체 사용법을 출력하는 버전이 있어 사용법 문구만으로는 존재를 판정할 수 없음
    unknown = any(m in text.lower() for m in C.RHWP_UNKNOWN_COMMAND_MARKERS)
    if res.returncode != 0 and (unknown or ("Usage" not in text and "사용법" not in text)):
        return False
    return flag is None or flag in text


def find_soffice() -> str | None:
    for cand in (shutil.which("soffice"), shutil.which("libreoffice"),
                 r"C:\Program Files\LibreOffice\program\soffice.exe",
                 "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if cand and os.path.isfile(cand):
            return cand
    return None


def find_lo_python(soffice: str) -> str | None:
    """LibreOffice 파이썬 연동(uno)을 쓸 수 있는 인터프리터. 현재 파이썬 또는 LibreOffice 동봉 파이썬."""
    try:
        import uno  # noqa: F401
        return sys.executable
    except ImportError:
        pass
    prog = os.path.dirname(os.path.realpath(soffice))
    for cand in (os.path.join(prog, "python"), os.path.join(prog, "python.exe"),
                 os.path.join(os.path.dirname(prog), "Resources", "python")):
        if os.path.isfile(cand):
            return cand
    for cand in ("/usr/bin/python3",):
        if os.path.isfile(cand) and subprocess.run([cand, "-c", "import uno"], capture_output=True).returncode == 0:
            return cand
    return None


def writable_dir(path: str) -> str:
    """산출물을 둘 디렉터리. 원본 옆이 읽기 전용이면 현재 작업 디렉터리를 쓴다."""
    d = os.path.dirname(os.path.abspath(path))
    return d if os.access(d, os.W_OK) else os.getcwd()


def resolve_engine(engine: str, rhwp_opt: str | None, src: str = "") -> str:
    if src.lower().endswith(".docx"):
        return "soffice"
    if engine == "auto":
        return "rhwp" if (rhwp_opt or find_rhwp()) else ("soffice" if find_soffice() else "")
    return engine


def render_copy(src: str, strip_newnum: bool = False, dest_dir: str | None = None) -> str:
    """HWPX 검수 전용 사본. 근사 렌더러 한계 회피용 치환만 넣고 납품물은 바꾸지 않는다.
    - 소프트 하이픈 글머리를 하이픈으로. 본문과 글머리 정의 양쪽 치환
    - strip_newnum: 본문 중간 번호 새로 시작 컨트롤 제거 (H2Orestart가 첫 문단 밖의 것에서 변환 실패)"""
    # ASCII 파일명 (H2Orestart 로케일 문제 회피). 같은 폴더의 동시 렌더링이 겹치지 않도록 이름마다 고유 접미사.
    # dest_dir는 검수 파일을 두는 폴더 (render --outdir, build 목차 대조의 임시 폴더). 없으면 원본 옆
    fd, work = tempfile.mkstemp(prefix="_render_copy_", suffix=".hwpx", dir=dest_dir or writable_dir(src))
    os.close(fd)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(work, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            d = zin.read(it.filename)
            # - 계위 기호는 header.xml의 글머리 정의에 있음. 본문만 치환하면 기호가 사라진 채 렌더됨
            if it.filename == "Contents/header.xml":
                d = re.sub(r'(<hh:bullet\b[^>]*\bchar=")\u00ad(")', rf'\g<1>{C.SOFT_HYPHEN_GLYPH}\g<2>',
                           d.decode("utf-8")).encode("utf-8")
            if it.filename.startswith("Contents/section") and it.filename.endswith(".xml"):
                t = d.decode("utf-8").replace("\u00ad", C.SOFT_HYPHEN_GLYPH)
                if strip_newnum:
                    t = re.sub(r'<hp:run charPrIDRef="\d+"><hp:ctrl><hp:newNum[^>]*/></hp:ctrl></hp:run>', "", t)
                d = t.encode("utf-8")
            if it.filename == "mimetype":
                zout.writestr(zipfile.ZipInfo("mimetype"), d, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(it.filename, d)
    return work


def plain_copy(src: str, dest_dir: str) -> str:
    """내용을 바꾸지 않은 검수 사본. LibreOffice는 연 문서 옆에 잠금 파일을 만들므로 납품 폴더 밖의 사본을 연다"""
    fd, work = tempfile.mkstemp(prefix="_render_copy_", suffix=os.path.splitext(src)[1], dir=dest_dir)
    os.close(fd)
    shutil.copyfile(src, work)
    return work


def _soffice_pdf(src: str, pdf: str, update_fields: bool) -> str:
    soffice = find_soffice()
    if not soffice:
        sys.exit(msg("err_no_soffice"))
    profile_dir = tempfile.mkdtemp(prefix="lo_profile_")   # 렌더링마다 전용 사용자 프로필을 쓰고 끝나면 삭제
    try:
        return _soffice_convert(soffice, src, pdf, update_fields, "file://" + profile_dir.replace(os.sep, "/"))
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)


def _soffice_convert(soffice: str, src: str, pdf: str, update_fields: bool, profile: str) -> str:
    lo_python = find_lo_python(soffice) if update_fields else None
    if update_fields and lo_python:   # 목차 필드를 갱신한 뒤 PDF로 저장 (Word가 열 때 갱신하는 결과에 가까운 검수본)
        res = subprocess.run([lo_python, LO_HELPER, soffice, os.path.abspath(src), os.path.abspath(pdf), profile],
                             capture_output=True, text=True, timeout=C.LIBREOFFICE_TIMEOUT)
        if res.returncode == 0 and os.path.exists(pdf):
            return "soffice"
        sys.exit(msg("err_soffice_failed", detail=(res.stdout + res.stderr)[-300:]))
    if update_fields:
        print(msg("warn_fields_not_updated"))
    # 같은 폴더의 동시 렌더링이 겹치지 않도록 변환 폴더 이름마다 고유 접미사. PDF를 둘 폴더에 만들어 납품 폴더를 건드리지 않음
    outdir = tempfile.mkdtemp(prefix="_lo_out_", dir=os.path.dirname(os.path.abspath(pdf)))
    try:
        env = {**os.environ, "LANG": os.environ.get("LANG") or "C.UTF-8"}
        cmd = [soffice, f"-env:UserInstallation={profile}", "--headless", "--convert-to", "pdf:writer_pdf_Export",
               "--outdir", outdir, src]
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=C.LIBREOFFICE_TIMEOUT)
        made = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".pdf")
        if not os.path.exists(made):
            sys.exit(msg("err_soffice_failed", detail=(res.stdout + res.stderr)[-300:]))
        shutil.move(made, pdf)
    finally:
        shutil.rmtree(outdir, ignore_errors=True)
    return "soffice"


def to_pdf(src: str, pdf: str, engine: str, rhwp_opt: str | None, text_layer: bool = False) -> str:
    """문서를 PDF로. text_layer=True면 글자 추출이 가능한 PDF를 만든다 (목차 쪽번호 산정용). 사용한 엔진명 반환."""
    engine = resolve_engine(engine, rhwp_opt, src)
    if engine == "rhwp":
        rhwp = rhwp_opt or find_rhwp()
        if not rhwp:
            sys.exit(msg("err_no_rhwp"))
        if not rhwp_supports(rhwp, C.RHWP_PDF_COMMAND):
            sys.exit(msg("err_rhwp_command", cmd=C.RHWP_PDF_COMMAND))
        cmd = [rhwp, C.RHWP_PDF_COMMAND, src, "-o", pdf]
        if os.path.isdir(C.USER_FONT_DIR) and rhwp_supports(rhwp, C.RHWP_PDF_COMMAND, C.RHWP_FONT_PATH_FLAG):
            cmd += [C.RHWP_FONT_PATH_FLAG, C.USER_FONT_DIR]
        if not text_layer and rhwp_supports(rhwp, C.RHWP_PDF_COMMAND, C.RHWP_PDF_OUTLINE_FLAG):
            cmd.append(C.RHWP_PDF_OUTLINE_FLAG)
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not os.path.exists(pdf):
            sys.exit(msg("err_rhwp_failed", detail=(res.stderr or res.stdout)[-400:]))
        return "rhwp"
    if engine == "soffice":
        _soffice_pdf(src, pdf, update_fields=src.lower().endswith(".docx"))
        return "soffice" if src.lower().endswith(".docx") else "soffice(H2Orestart)"
    sys.exit(msg("err_no_renderer"))


def page_pngs(folder: str) -> list[str]:
    """render가 만드는 쪽 PNG 파일 이름 (p-N.png)"""
    return [f for f in os.listdir(folder) if re.fullmatch(r"p-\d+\.png", f)]


def render(src: str, outdir: str | None, dpi: int, engine: str, rhwp_opt: str | None, keep_soft_hyphen: bool):
    engine = resolve_engine(engine, rhwp_opt, src)
    is_hwpx = src.lower().endswith(".hwpx")
    base = os.path.splitext(os.path.basename(src))[0]
    stem = os.path.join(writable_dir(src), base)
    # --outdir를 주면 PDF와 검수 사본도 그 폴더에 둔다. 납품 폴더의 문서를 렌더링해도 검수 파일이 납품 폴더에 섞이지 않음
    copy_dir = outdir
    pdf = os.path.join(outdir, base + ".pdf") if outdir else stem + ".pdf"
    outdir = outdir or stem + "_pages"
    os.makedirs(outdir, exist_ok=True)
    if is_hwpx and not keep_soft_hyphen:
        work = render_copy(src, strip_newnum=(engine == "soffice"), dest_dir=copy_dir)
    else:
        work = plain_copy(src, copy_dir) if copy_dir else src
    try:
        used = to_pdf(work, pdf, engine, rhwp_opt)
    finally:   # 렌더링이 실패해도 검수 사본을 남기지 않음
        if work != src and os.path.exists(work):
            os.remove(work)
    for f in page_pngs(outdir):   # 이전 렌더의 쪽 PNG만 지움. 같은 폴더의 PDF와 다른 파일은 유지
        os.remove(os.path.join(outdir, f))
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, os.path.join(outdir, "p")], check=True)
        print(msg("render_ok", engine=used, pdf=pdf, outdir=outdir, n=len(page_pngs(outdir))))
    else:
        print(msg("render_pdf_only", engine=used, pdf=pdf))


def text_pages(doc_path: str, rhwp_opt: str | None) -> list[str] | None:
    """문서를 글자 추출이 가능한 PDF로 렌더링하고 쪽별 텍스트를 돌려준다. 렌더러나 pdftotext가 없으면 None."""
    is_docx = doc_path.lower().endswith(".docx")
    has_renderer = find_soffice() if is_docx else (rhwp_opt or find_rhwp() or find_soffice())
    if not shutil.which("pdftotext") or not has_renderer:
        return None
    tmp = tempfile.mkdtemp(prefix="_toc_check_")   # 대조용 PDF는 납품 폴더 밖에서 만들고 중단되어도 지움
    pdf = os.path.join(tmp, "toc.pdf")
    engine = resolve_engine("auto", rhwp_opt, doc_path)
    work = plain_copy(doc_path, tmp) if is_docx else render_copy(doc_path, strip_newnum=(engine == "soffice"), dest_dir=tmp)
    try:
        to_pdf(work, pdf, engine, rhwp_opt, text_layer=True)
        # 그린 순서대로 추출. -layout은 쪽 끝 제목이 각주 영역에 겹쳐 그려지면 두 글자를 섞어 제목을 찾지 못함
        txt = subprocess.run(["pdftotext", "-raw", pdf, "-"], capture_output=True, text=True).stdout
    except SystemExit:
        return None
    finally:
        if work != doc_path and os.path.exists(work):
            os.remove(work)
        shutil.rmtree(tmp, ignore_errors=True)
    return txt.split("\f")


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text)


def locate_headings(pages: list[str], entries: list[str]) -> list[int | None]:
    """목차 항목(문서 순서)이 본문 몇 쪽에 있는지 센다. 본문 첫 쪽이 1.
    목차 제목이 처음 나오는 쪽부터 항목을 차례로 찾아 마지막 항목이 있는 쪽까지를 목차로 보고 그다음 쪽을 본문 첫 쪽으로 둔다.
    목차가 여러 쪽이어도 본문 시작을 바로 찾는다. 본문에서도 항목을 차례로 찾아 앞 제목보다 앞쪽에서 찾지 않는다."""
    found, body = _locate_pages(pages, entries)
    return [None if q is None else q - body + 1 for q in found]


def _locate_pages(pages: list[str], entries: list[str]) -> tuple[list[int | None], int]:
    """locate_headings의 탐색. 항목마다 렌더 쪽의 0부터 센 위치와 본문 첫 쪽 위치를 돌려준다"""
    keys = [_norm(e) for e in entries]
    title = _norm(C.label("toc.title"))
    toc = next((i for i, page in enumerate(pages) if title in _norm(page)), None)
    if toc is None or not keys:
        return [None] * len(keys), 0
    p = toc
    for k in keys:
        while p < len(pages) and k not in _norm(pages[p]):
            p += 1
    if p >= len(pages):
        return [None] * len(keys), 0
    body = p + 1
    found, p = [], body
    for k in keys:
        q = p
        while q < len(pages) and k not in _norm(pages[q]):
            q += 1
        if q < len(pages):
            found.append(q)
            p = q
        else:
            found.append(None)
    return found, body


def stranded_headings(pages: list[str], entries: list[str], firsts: list[str | None]) -> list[str]:
    """목차 제목은 한 쪽 끝에 있고 첫 본문 줄은 다음 쪽에서 시작하는 항목 ('제목 (본문 N쪽)').
    렌더러가 다음 문단과 같은 쪽에 두는 설정을 반영하지 않을 때 생기며 한/글은 제목을 다음 쪽으로 넘김.
    같은 문구가 앞에 있어 판정이 어긋나지 않도록 제목 뒤 글자와 바로 다음 쪽만 본다"""
    found, body = _locate_pages(pages, entries)
    out = []
    for entry, q, first in zip(entries, found, firsts):
        if q is None or not first or q + 1 >= len(pages):
            continue
        key = _norm(first)[:C.TOC_FIRST_LINE_KEY]
        page, head = _norm(pages[q]), _norm(entry)
        if key in page[page.find(head) + len(head):]:
            continue
        if key in _norm(pages[q + 1]):
            out.append(f"{entry} ({q - body + 1})")
    return out


def heading_pages(doc_path: str, entries: list[str], rhwp_opt: str | None) -> list[int | None]:
    """목차 항목의 본문 쪽번호 목록. 렌더링할 수 없으면 모두 None."""
    pages = text_pages(doc_path, rhwp_opt)
    return locate_headings(pages, entries) if pages else [None] * len(entries)


def fill_toc_numbers(make, out: str, entries: list[str], rhwp_opt: str | None, firsts: list[str | None] | None = None):
    """목차 쪽번호 2회 조판. 1회차 문서를 렌더링해 쪽번호를 구하고 기입한 뒤, 최종 문서를 다시 렌더링해 대조한다.
    불일치가 남으면 새로 구한 값으로 다시 조판한다 (최대 C.TOC_MAX_PASSES회). make(numbers)는 순번→쪽번호로 문서를 다시 만든다.
    firsts(항목별 첫 본문 줄)를 주면 최종 렌더에서 제목과 첫 본문 줄이 다른 쪽에 놓인 항목을 WARN으로 알린다."""
    used = heading_pages(out, entries, rhwp_opt)
    if not any(n is not None for n in used):
        print(msg("warn_toc_numbers"))
        return
    pages = None
    for attempt in range(C.TOC_MAX_PASSES):
        make({i: n for i, n in enumerate(used) if n is not None})
        pages = text_pages(out, rhwp_opt)
        actual = locate_headings(pages, entries) if pages else [None] * len(entries)
        diff = [i for i, (u, a) in enumerate(zip(used, actual)) if u != a]
        if not diff or attempt + 1 == C.TOC_MAX_PASSES:
            break
        used = actual
    filled = sum(n is not None for n in used)
    print(msg("toc_numbers", found=filled, total=len(entries)))
    missing = [e for e, n in zip(entries, used) if n is None]
    if missing:
        print(msg("warn_toc_missing", n=len(missing), items=missing))
    if diff:
        items = [f"{entries[i]} ({used[i]}→{actual[i]})" for i in diff]
        print(msg("warn_toc_mismatch", n=len(diff), items=items))
    else:   # 찾지 못한 항목은 일치로 세지 않음
        print(msg("toc_verified", n=filled, total=len(entries)))
    stranded = stranded_headings(pages, entries, firsts) if pages and firsts else []
    if stranded:
        print(msg("warn_toc_stranded", n=len(stranded), items=stranded))


def rhwp_verify(path: str, expect: str) -> bool | None:
    """기대 조건 대조. 통과 True, 불일치나 출력 해석 실패 False, 대조하지 않았으면 None"""
    rhwp = find_rhwp()
    if not (rhwp and expect):
        return None
    if not rhwp_supports(rhwp, C.RHWP_VERIFY_COMMAND):
        print(msg("warn_verify_missing", cmd=C.RHWP_VERIFY_COMMAND))
        return None
    res = subprocess.run([rhwp, C.RHWP_VERIFY_COMMAND, path, "--json"] + shlex.split(expect), capture_output=True, text=True)
    try:
        d = json.loads(res.stdout)
        items = [(e["kind"], e.get("actual"), e["pass"]) for e in d["expectations"]]
    except (json.JSONDecodeError, KeyError):
        print(msg("verify_parse_fail", out=(res.stdout[:200], res.stderr[:200])))
        return False
    print(msg("verify_result", verdict=d.get("verdict"), items=items))
    return all(ok for _, _, ok in items)


# ── 글꼴 ───────────────────────────────────────────────────────────────────
def installed_families() -> set[str] | None:
    if not shutil.which("fc-list"):
        return None
    out = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
    return {f.strip() for line in out.splitlines() for f in line.split(",")}


def ksx1001_hanja() -> list[int]:
    """KS X 1001 한자 중 통합 한자 4,620자의 코드 포인트"""
    first, last = C.CJK_UNIFIED_RANGE
    code_points = set()
    for lead in C.KSX1001_HANJA_LEAD:
        for trail in C.KSX1001_HANJA_TRAIL:
            ch = bytes((lead, trail)).decode("euc_kr", errors="ignore")
            if ch and first <= ord(ch) <= last:
                code_points.add(ord(ch))
    return sorted(code_points)


class FontLookup(Enum):
    """설치 글꼴을 찾는 방법"""
    FONTCONFIG = "fontconfig"   # Linux 등 fontconfig가 있는 환경
    FOLDERS = "folders"         # fontconfig가 없는 Windows와 macOS: 운영체제 글꼴 폴더를 이름표로 탐색
    NONE = "none"               # 찾을 수 없음 (fontTools 없음 또는 폴더 정보가 없는 운영체제)


def font_lookup() -> FontLookup:
    if shutil.which("fc-match"):
        return FontLookup.FONTCONFIG
    if sys.platform in C.FONT_DIRS and importlib.util.find_spec("fontTools") is not None:
        return FontLookup.FOLDERS
    return FontLookup.NONE


def fontconfig_file(face: str) -> tuple[str, int] | None:
    """fontconfig가 face에 쓰는 파일과 글꼴 번호. fc-match는 없는 이름에도 대체 글꼴을 돌려주므로 가족 이름을 대조한다."""
    escaped = re.sub(r"([\\\-:,])", r"\\\1", face)   # fontconfig 패턴의 특수 문자
    out = subprocess.run(["fc-match", "-f", "%{family}\n%{file}\n%{index}", escaped],
                         capture_output=True, text=True).stdout.split("\n")
    if len(out) < 3 or face not in (name.strip() for name in out[0].split(",")):
        return None
    return out[1], int(out[2] or 0)


def folder_file(face: str, dirs: list[str]) -> tuple[str, int] | None:
    """글꼴 폴더에서 가족 이름이 face인 파일과 글꼴 번호. 보통 굵기 파일을 우선한다."""
    from fontTools.ttLib import TTCollection, TTFont, TTLibError
    found = []
    for folder in (os.path.expanduser(os.path.expandvars(d)) for d in dirs):
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.lower().endswith(C.FONT_FILE_EXTS):
                continue
            path = os.path.join(folder, name)
            try:
                fonts = TTCollection(path, lazy=True).fonts if name.lower().endswith(".ttc") else [TTFont(path, lazy=True)]
                for index, font in enumerate(fonts):
                    families = {r.toUnicode(errors="ignore") for r in font["name"].names if r.nameID in (1, 16)}
                    if face in families:
                        found.append((font["OS/2"].usWeightClass != C.REGULAR_WEIGHT, path, index))
            except (OSError, TTLibError, KeyError):   # 읽을 수 없거나 이름표가 없는 파일은 건너뜀
                continue
    return min(found)[1:] if found else None


def has_ksx1001_hanja(path: str, index: int) -> bool | None:
    """글꼴 파일이 KS X 1001 통합 한자의 글자 모양을 모두 담았는지. fontTools가 없으면 None.
    문자 코드 등록만 보면 부족하다. Google 배포 나눔고딕은 한자 코드가 없고, 나눔스퀘어는 코드만 있고 모양이 비어 있다."""
    try:
        from fontTools.pens.boundsPen import ControlBoundsPen
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    font = TTFont(path, fontNumber=index, lazy=True)
    cmap, glyphs = font.getBestCmap(), font.getGlyphSet()
    for cp in ksx1001_hanja():
        if cp not in cmap:
            return False
        pen = ControlBoundsPen(glyphs)
        glyphs[cmap[cp]].draw(pen)
        if pen.bounds is None:   # 코드는 있으나 모양이 빈 글자
            return False
    return True


def fonts_report(faces: list[str]):
    """양식 글꼴마다 설치 여부, 한자 포함 여부, 렌더링 대체 글꼴, 확보 경로를 출력한다.
    이 명령을 실행한 컴퓨터의 상태이므로 문서를 여는 컴퓨터에서 실행해야 그 컴퓨터의 설치 상태가 된다."""
    lookup = font_lookup()
    print(msg("fonts_header"))
    for face in faces:
        if lookup is FontLookup.NONE:
            located, state, hanja = None, "?", "?"
        else:
            located = fontconfig_file(face) if lookup is FontLookup.FONTCONFIG else folder_file(face, C.FONT_DIRS[sys.platform])
            state = msg("fonts_yes" if located else "fonts_no")
            found = has_ksx1001_hanja(*located) if located else None
            hanja = "-" if not located else "?" if found is None else msg("fonts_hanja_yes" if found else "fonts_hanja_no")
        sub = "-" if located else C.FONT_SUBSTITUTES.get(face, "-")   # fonts_setup과 같은 기준
        print(msg("fonts_row", face=face, installed=state, hanja=hanja, sub=sub,
                  source=msg(C.FONT_SOURCES[face]) if face in C.FONT_SOURCES else "-"))


def fonts_setup():
    """양식 글꼴(SIL OFL 1.1) 중 저장소에 있는 것을 내려받고, 설치되지 않은 글꼴만 대체 글꼴로 잇는 fontconfig 규칙을 기록한다."""
    fams = installed_families()
    if fams is None:
        print(msg("fonts_no_fc"))
        return
    os.makedirs(C.USER_FONT_DIR, exist_ok=True)
    for family, (folder, files) in C.FREE_FONTS.items():
        if family in fams:
            continue
        for name in files + [C.FREE_FONT_LICENSE_FILE]:
            url = f"{C.FREE_FONT_BASE}/{folder}/{name}"
            dest = os.path.join(C.USER_FONT_DIR, f"{family}-{name}" if name == C.FREE_FONT_LICENSE_FILE else name)
            print(msg("fonts_download", name=name, url=url))
            try:
                with urllib.request.urlopen(url, timeout=C.IMG_URL_TIMEOUT) as resp, open(dest, "wb") as fh:
                    fh.write(resp.read())
            except Exception as ex:
                print(msg("fonts_download_fail", name=name, err=ex))
                break
    rules = []
    for face, sub in C.FONT_SUBSTITUTES.items():
        if face in fams:   # 설치된 글꼴은 대체하지 않는다
            continue
        family = sub.partition(" ExtraBold")[0]
        edit = f'<edit name="family" mode="assign" binding="same"><string>{family}</string></edit>'
        if sub.endswith("ExtraBold"):
            edit += '<edit name="weight" mode="assign" binding="same"><const>extrabold</const></edit>'
        rules.append(f'<match target="pattern"><test name="family"><string>{face}</string></test>{edit}</match>')
    os.makedirs(os.path.dirname(C.FONTCONFIG_FILE), exist_ok=True)
    with open(C.FONTCONFIG_FILE, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n<fontconfig>\n'
                 f"<dir>{C.USER_FONT_DIR}</dir>\n" + "\n".join(rules) + "\n</fontconfig>\n")
    subprocess.run(["fc-cache", "-f"], capture_output=True)
    print(msg("fonts_config", path=C.FONTCONFIG_FILE))
