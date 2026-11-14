"""목차 책갈피와 쪽 참조: 산출 파일(HWPX, DOCX)에서 찾기와 정적화.

- 한/글과 Word가 다시 저장한 파일은 run 분할과 속성이 build 산출물과 다르므로 요소 종류와 참조 관계로만 찾는다
- 조판 라이브러리 없이 zipfile과 lxml만 쓴다. 제출 파일에서 대상 요소만 지우고 나머지 내용은 다시 만들지 않기 위함
- 메시지는 출력하지 않는다. 호출하는 명령이 결과를 받아 안내한다
"""
from __future__ import annotations

import os
import re
import zipfile
from dataclasses import dataclass, field
from enum import Enum

from lxml import etree as ET

# ── 설정부 ─────────────────────────────────────────────────────────────────
# 쪽 참조의 자리 표시 값. 한/글과 Word가 쪽번호를 계산하기 전까지 보이는 글자
# Why 근사값을 넣지 않음: 다른 조판 엔진이 계산한 쪽은 Word와 달라 독자가 실제 쪽번호로 오인함 (LibreOffice 값은 16건 중 11건이 Word와 달랐음)
PLACEHOLDER = "?"
KINDS = ("chapter", "section", "subsection", "ganada", "module", "task", "table", "figure")   # 목차 수록 항목의 종류
OTHER = "other"          # 종류를 판별하지 못한 책갈피
BAND_KIND_RE = re.compile(r"^\s*(Module|Task|Step)\b", re.I)   # 밴드 번호 칸의 글자. 일치하지 않는 밴드는 장
DOCX_REF_RE = re.compile(r"^\s*(PAGEREF|REF)\s+(\S+)")           # 책갈피를 가리키는 Word 필드 (쪽 참조, 글자 참조)
HWPX_SECTION_RE = re.compile(r"Contents/section(\d+)\.xml$")
HWPX_HEADER = "Contents/header.xml"
DOCX_BODY = "word/document.xml"
DOCX_STYLES = "word/styles.xml"
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class RefState(Enum):
    """쪽 참조 저장값의 상태"""
    UPDATED = "updated"            # 한/글이나 Word가 계산한 쪽번호
    PLACEHOLDER = "placeholder"    # 자리 표시 값이 남음 (편집기에서 갱신하지 않은 파일)


@dataclass
class TocItem:
    """쪽 참조가 가리키는 책갈피 1개"""
    name: str
    kind: str                                          # KINDS 중 하나 또는 OTHER
    text: str                                          # 책갈피가 놓인 문단의 글자
    values: list[str] = field(default_factory=list)    # 이 책갈피를 가리키는 쪽 참조의 저장값

    @property
    def state(self) -> RefState:
        if all(v.strip().isdigit() for v in self.values):
            return RefState.UPDATED
        return RefState.PLACEHOLDER   # 자리 표시 값과 숫자가 아닌 값(편집기의 참조 오류 글자 등)


def is_docx(path: str) -> bool:
    return path.lower().endswith(".docx")


# ── 공통 보조 ──────────────────────────────────────────────────────────────
def _local(el) -> str:
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def _drop(el):
    """요소를 지우되 뒤따르는 글자(tail)는 남김"""
    parent, tail = el.getparent(), el.tail
    if tail:
        prev = el.getprevious()
        if prev is not None:
            prev.tail = (prev.tail or "") + tail
        else:
            parent.text = (parent.text or "") + tail
    parent.remove(el)


def _serialize(root, original: bytes) -> bytes:
    """원본의 XML 선언은 그대로 두고 본문만 다시 직렬화"""
    head = re.match(rb"\s*<\?xml[^>]*\?>\s*", original)
    return (head.group(0) if head else b"") + ET.tostring(root, encoding="UTF-8", xml_declaration=False)


def _rewrite(src: str, out: str, replaced: dict[str, bytes]):
    """압축 파일의 일부 항목만 바꿔 다시 기록. 나머지 항목은 순서와 압축 방식을 유지
    HWPX는 mimetype 항목이 맨 앞에 무압축으로 있어야 한/글이 문서로 인식"""
    tmp = out + ".tmp"
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        infos = sorted(zin.infolist(), key=lambda it: it.filename != "mimetype")   # 안정 정렬: mimetype만 맨 앞으로
        for it in infos:
            data = replaced.get(it.filename, zin.read(it.filename))
            if it.filename == "mimetype":
                zout.writestr(zipfile.ZipInfo("mimetype"), data, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(it, data)
    os.replace(tmp, out)


def _band_kind(text: str) -> str:
    m = BAND_KIND_RE.match(text)
    if not m:
        return "chapter"
    return "module" if m.group(1).lower() == "module" else "task"


# ── HWPX ──────────────────────────────────────────────────────────────────
def _hwpx_parts(path: str) -> tuple[dict[str, bytes], dict[str, str]]:
    """구역 XML(구역 번호 순)과 스타일 id → 스타일 이름"""
    with zipfile.ZipFile(path) as z:
        names = sorted((n for n in z.namelist() if HWPX_SECTION_RE.search(n)),
                       key=lambda n: int(HWPX_SECTION_RE.search(n).group(1)))
        sections = {n: z.read(n) for n in names}
        header = ET.fromstring(z.read(HWPX_HEADER))
    return sections, {s.get("id"): s.get("name") for s in header.iter(f"{HH}style")}


def _hwpx_target(begin) -> tuple[str, str] | None:
    """책갈피를 가리키는 상호참조의 (책갈피 이름, 내용 종류). 각주 번호 참조 등 다른 필드는 None
    Why RefType: 각주 번호 상호참조도 같은 CROSSREF 필드이며 값만 다름"""
    if begin.get("type") != "CROSSREF":
        return None
    params = {p.get("name"): p.text or "" for p in begin.iter() if p.get("name")}
    if params.get("RefType") != "TARGET_BOOKMARK":
        return None
    path = params.get("RefPath") or params.get("Command", "")   # "?이름;" 또는 "?이름;6;0;0;0;"
    return path.lstrip("?").split(";", 1)[0], params.get("RefContentType", "")


def _hwpx_value(begin) -> str:
    """필드 시작과 끝 사이의 저장값 글자. 시작과 끝이 다른 run에 있어도 같은 문단 안에서 찾음"""
    para = next(a for a in begin.iterancestors() if a.tag == f"{HP}p")
    out, inside = [], False
    for el in para.iter():
        if el is begin:
            inside = True
        elif inside and el.tag == f"{HP}fieldEnd" and el.get("beginIDRef") == begin.get("id"):
            break
        elif inside and el.tag == f"{HP}t":
            out.append("".join(el.itertext()))
    return "".join(out)


def _hwpx_para_text(para) -> str:
    return "".join("".join(t.itertext()) for t in para.findall(f"{HP}run/{HP}t"))


def _hwpx_kind(mark, style_kinds: dict[str, str], styles: dict[str, str]) -> str:
    """책갈피가 놓인 자리로 항목 종류를 판별
    캡션이 딸린 개체 안(셀 문단, 캡션 문단)이면 개체의 번호 유형, 캡션 없는 표의 셀 안이면 밴드, 그 밖은 문단 스타일의 역할"""
    para = next(a for a in mark.iterancestors() if a.tag == f"{HP}p")
    for a in para.iterancestors():
        tag = _local(a)
        if tag in ("tbl", "pic"):
            if a.find(f"{HP}caption") is None:
                return _band_kind(_hwpx_para_text(para)) if tag == "tbl" else OTHER
            return "figure" if tag == "pic" or a.get("numberingType") == "PICTURE" else "table"
        if tag in ("footNote", "endNote", "header", "footer"):
            return OTHER
    return style_kinds.get(styles.get(para.get("styleIDRef"), ""), OTHER)


def _scan_hwpx(path: str, style_kinds: dict[str, str]) -> list[TocItem]:
    sections, styles = _hwpx_parts(path)
    marks: dict[str, TocItem] = {}
    values: dict[str, list[str]] = {}
    for data in sections.values():
        root = ET.fromstring(data)
        for mark in root.iter(f"{HP}bookmark"):
            para = next(a for a in mark.iterancestors() if a.tag == f"{HP}p")
            marks.setdefault(mark.get("name"), TocItem(mark.get("name"), _hwpx_kind(mark, style_kinds, styles),
                                                       _hwpx_para_text(para)))
        for begin in root.iter(f"{HP}fieldBegin"):
            target = _hwpx_target(begin)
            if target and target[1] == "OBJECT_TYPE_PAGE":
                values.setdefault(target[0], []).append(_hwpx_value(begin))
    for name, item in marks.items():
        item.values = values.get(name, [])
    return [it for it in marks.values() if it.values]   # 쪽 참조가 없는 책갈피는 목차 항목이 아님


def _drop_ctrl(el):
    """컨트롤 요소를 지움. 감싼 hp:ctrl에 다른 컨트롤이 없으면 hp:ctrl 전체를 지움"""
    parent = el.getparent()
    _drop(parent if parent.tag == f"{HP}ctrl" and len(parent) == 1 else el)


def _static_hwpx(src: str, out: str, names: set[str]):
    """대상 책갈피를 가리키는 상호참조(쪽 번호, 책갈피 이름)의 필드 시작과 끝을 지우고 저장값 글자는 남김. 대상 책갈피를 지움
    Why 줄 배치 값(linesegarray) 유지: 지우면 줄바꿈을 다시 계산하는 렌더러에서 쪽 배치가 달라짐"""
    sections, _ = _hwpx_parts(src)
    replaced = {}
    for part, data in sections.items():
        root = ET.fromstring(data)
        begins = [b for b in root.iter(f"{HP}fieldBegin") if (_hwpx_target(b) or ("",))[0] in names]
        ids = {b.get("id") for b in begins}
        doomed = begins + [e for e in root.iter(f"{HP}fieldEnd") if e.get("beginIDRef") in ids] \
            + [m for m in root.iter(f"{HP}bookmark") if m.get("name") in names]
        for el in doomed:
            _drop_ctrl(el)
        if doomed:
            replaced[part] = _serialize(root, data)
    _rewrite(src, out, replaced)


# ── DOCX ──────────────────────────────────────────────────────────────────
def _docx_fields(root) -> list[dict]:
    """필드 목록 (문서 순서). instr: 명령, parts: 필드를 이루는 fldChar와 instrText, result: 결과 글자 요소, simple: fldSimple 요소
    Why 순회: Word와 LibreOffice는 필드 요소를 run마다 나누어 저장하므로 run 구성에 기대지 않고 fldChar 순서로 짝을 맞춤"""
    done, open_fields = [], []
    for el in root.iter(f"{W}fldSimple", f"{W}fldChar", f"{W}instrText", f"{W}t"):
        tag = _local(el)
        if tag == "fldSimple":
            done.append({"instr": el.get(f"{W}instr", ""), "parts": [], "result": list(el.iter(f"{W}t")), "simple": el})
        elif tag == "fldChar":
            kind = el.get(f"{W}fldCharType")
            if kind == "begin":
                open_fields.append({"instr": "", "parts": [el], "result": [], "simple": None, "separated": False})
            elif open_fields and kind == "separate":
                open_fields[-1]["separated"] = True
                open_fields[-1]["parts"].append(el)
            elif open_fields and kind == "end":
                open_fields[-1]["parts"].append(el)
                done.append(open_fields.pop())
        elif open_fields and tag == "instrText" and not open_fields[-1]["separated"]:
            open_fields[-1]["instr"] += el.text or ""
            open_fields[-1]["parts"].append(el)
        elif open_fields and tag == "t" and open_fields[-1]["separated"]:
            open_fields[-1]["result"].append(el)
    return done


def _docx_refs(root) -> list[tuple[str, bool, dict]]:
    """책갈피를 가리키는 필드의 (책갈피 이름, 쪽 참조 여부, 필드). 각주 번호 참조(NOTEREF)는 대상이 아님"""
    out = []
    for f in _docx_fields(root):
        m = DOCX_REF_RE.match(f["instr"])
        if m:
            out.append((m.group(2), m.group(1) == "PAGEREF", f))
    return out


def _docx_roots(path: str) -> tuple[bytes, "ET._Element", dict[str, str]]:
    """본문 XML 원문, 본문 뿌리, 스타일 id → 소문자 스타일 이름"""
    with zipfile.ZipFile(path) as z:
        data = z.read(DOCX_BODY)
        styles = ET.fromstring(z.read(DOCX_STYLES))
    names = {}
    for st in styles.iter(f"{W}style"):
        name = st.find(f"{W}name")
        if name is not None:
            names[st.get(f"{W}styleId")] = name.get(f"{W}val", "").lower()
    return data, ET.fromstring(data), names


def _docx_host(mark):
    """책갈피가 놓인 문단. 문단 사이에 놓인 책갈피는 바로 뒤 문단"""
    for a in mark.iterancestors():
        if a.tag == f"{W}p":
            return a
    nxt = mark.getnext()
    while nxt is not None and nxt.tag != f"{W}p":
        nxt = nxt.getnext()
    return nxt


def _docx_kind(para, style_kinds: dict[str, str], styles: dict[str, str]) -> str:
    """표 셀 안이면 밴드, 그 밖은 문단 스타일의 역할 (제목, 표 캡션, 그림 캡션)"""
    if para is None:
        return OTHER
    text = "".join(t.text or "" for t in para.iter(f"{W}t"))
    if any(a.tag == f"{W}tc" for a in para.iterancestors()):
        return _band_kind(text)
    style = para.find(f"{W}pPr/{W}pStyle")
    return style_kinds.get(styles.get(style.get(f"{W}val"), "") if style is not None else "", OTHER)


def _scan_docx(path: str, style_kinds: dict[str, str]) -> list[TocItem]:
    _, root, styles = _docx_roots(path)
    kinds = {k.lower(): v for k, v in style_kinds.items()}   # Word와 LibreOffice는 기본 스타일 이름의 대소문자를 바꿔 저장
    marks: dict[str, TocItem] = {}
    for mark in root.iter(f"{W}bookmarkStart"):
        para = _docx_host(mark)
        text = "".join(t.text or "" for t in para.iter(f"{W}t")) if para is not None else ""
        marks.setdefault(mark.get(f"{W}name"), TocItem(mark.get(f"{W}name"), _docx_kind(para, kinds, styles), text))
    for name, is_page, f in _docx_refs(root):
        if is_page and name in marks:
            marks[name].values.append("".join(t.text or "" for t in f["result"]))
    return [it for it in marks.values() if it.values]


def _static_docx(src: str, out: str, names: set[str]):
    """대상 책갈피를 가리키는 PAGEREF와 REF 필드의 fldChar와 instrText를 지우고 결과 글자는 남김. fldSimple은 감싼 요소만 풂
    대상 책갈피의 bookmarkStart와 같은 id의 bookmarkEnd를 지움"""
    data, root, _ = _docx_roots(src)
    for name, _, f in _docx_refs(root):
        if name not in names:
            continue
        for el in f["parts"]:
            run = el.getparent()
            _drop(el)
            if all(c.tag == f"{W}rPr" for c in run):   # 필드 요소만 담았던 run
                _drop(run)
        if f["simple"] is not None:
            for child in list(f["simple"]):
                f["simple"].addprevious(child)
            _drop(f["simple"])
    ids = set()
    for mark in list(root.iter(f"{W}bookmarkStart")):
        if mark.get(f"{W}name") in names:
            ids.add(mark.get(f"{W}id"))
            _drop(mark)
    for end in list(root.iter(f"{W}bookmarkEnd")):
        if end.get(f"{W}id") in ids:
            _drop(end)
    _rewrite(src, out, {DOCX_BODY: _serialize(root, data)})


def docx_page_values(path: str) -> dict[str, str]:
    """책갈피 이름 → PAGEREF 결과 글자"""
    _, root, _ = _docx_roots(path)
    return {name: "".join(t.text or "" for t in f["result"]) for name, is_page, f in _docx_refs(root) if is_page}


# ── 형식 공통 진입점 ────────────────────────────────────────────────────────
def scan(path: str, style_kinds: dict[str, str]) -> list[TocItem]:
    """쪽 참조가 가리키는 책갈피 목록 (문서 순서). style_kinds: 문단 스타일 이름 → 항목 종류"""
    return (_scan_docx if is_docx(path) else _scan_hwpx)(path, style_kinds)


def make_static(src: str, out: str, names: set[str]):
    """이름이 names에 든 책갈피와 그 책갈피를 가리키는 참조를 일반 글자로 바꾼 사본을 out에 기록"""
    (_static_docx if is_docx(src) else _static_hwpx)(src, out, names)
