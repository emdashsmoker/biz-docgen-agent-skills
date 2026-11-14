"""TOC bookmarks and page references: finding them in output files (HWPX, DOCX) and static conversion.

- Files saved again by 한/글 and Word differ from build output in run splitting and attributes, so everything is found by element kind and reference relation only
- Uses only zipfile and lxml, no typesetting library, so that only the target elements are removed from a submitted file and the rest is not rebuilt
- Prints no messages. The calling command receives the results and reports them
"""
from __future__ import annotations

import os
import re
import zipfile
from dataclasses import dataclass, field
from enum import Enum

from lxml import etree as ET

# ── Settings ───────────────────────────────────────────────────────────────
# placeholder of a page reference. The text shown until 한/글 or Word calculates the page number
# Why no approximation: pages calculated by another layout engine differ from Word and look like plausible wrong numbers (LibreOffice values differed from Word in 11 of 16 entries)
PLACEHOLDER = "?"
KINDS = ("chapter", "section", "subsection", "ganada", "module", "task", "table", "figure")   # kinds of items listed in the TOC
OTHER = "other"          # bookmark whose kind was not identified
BAND_KIND_RE = re.compile(r"^\s*(Module|Task|Step)\b", re.I)   # text of a band number cell. A band that does not match is a chapter
DOCX_REF_RE = re.compile(r"^\s*(PAGEREF|REF)\s+(\S+)")           # Word fields that target a bookmark (page reference, text reference)
HWPX_SECTION_RE = re.compile(r"Contents/section(\d+)\.xml$")
HWPX_HEADER = "Contents/header.xml"
DOCX_BODY = "word/document.xml"
DOCX_STYLES = "word/styles.xml"
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class RefState(Enum):
    """State of the stored value of a page reference"""
    UPDATED = "updated"            # page number calculated by 한/글 or Word
    PLACEHOLDER = "placeholder"    # the placeholder remains (a file not updated in the editor)


@dataclass
class TocItem:
    """One bookmark targeted by page references"""
    name: str
    kind: str                                          # one of KINDS, or OTHER
    text: str                                          # text of the paragraph holding the bookmark
    values: list[str] = field(default_factory=list)    # stored values of the page references targeting this bookmark

    @property
    def state(self) -> RefState:
        if all(v.strip().isdigit() for v in self.values):
            return RefState.UPDATED
        return RefState.PLACEHOLDER   # the placeholder and non-numeric values (such as an editor's reference error text)


def is_docx(path: str) -> bool:
    return path.lower().endswith(".docx")


# ── Shared helpers ─────────────────────────────────────────────────────────
def _local(el) -> str:
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def _drop(el):
    """Removes an element but keeps the text that follows it (tail)"""
    parent, tail = el.getparent(), el.tail
    if tail:
        prev = el.getprevious()
        if prev is not None:
            prev.tail = (prev.tail or "") + tail
        else:
            parent.text = (parent.text or "") + tail
    parent.remove(el)


def _serialize(root, original: bytes) -> bytes:
    """Keeps the XML declaration of the original and serializes only the body again"""
    head = re.match(rb"\s*<\?xml[^>]*\?>\s*", original)
    return (head.group(0) if head else b"") + ET.tostring(root, encoding="UTF-8", xml_declaration=False)


def _rewrite(src: str, out: str, replaced: dict[str, bytes]):
    """Rewrites the archive with only some entries replaced. The other entries keep their order and compression
    한/글 recognizes an HWPX as a document only when the mimetype entry comes first and is stored uncompressed"""
    tmp = out + ".tmp"
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        infos = sorted(zin.infolist(), key=lambda it: it.filename != "mimetype")   # stable sort: only mimetype moves to the front
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
    """Section XML (in section number order) and style id → style name"""
    with zipfile.ZipFile(path) as z:
        names = sorted((n for n in z.namelist() if HWPX_SECTION_RE.search(n)),
                       key=lambda n: int(HWPX_SECTION_RE.search(n).group(1)))
        sections = {n: z.read(n) for n in names}
        header = ET.fromstring(z.read(HWPX_HEADER))
    return sections, {s.get("id"): s.get("name") for s in header.iter(f"{HH}style")}


def _hwpx_target(begin) -> tuple[str, str] | None:
    """(bookmark name, content type) of a cross-reference that targets a bookmark. None for other fields such as footnote number references
    Why RefType: a footnote number cross-reference is the same CROSSREF field with different values"""
    if begin.get("type") != "CROSSREF":
        return None
    params = {p.get("name"): p.text or "" for p in begin.iter() if p.get("name")}
    if params.get("RefType") != "TARGET_BOOKMARK":
        return None
    path = params.get("RefPath") or params.get("Command", "")   # "?name;" or "?name;6;0;0;0;"
    return path.lstrip("?").split(";", 1)[0], params.get("RefContentType", "")


def _hwpx_value(begin) -> str:
    """Stored value text between the field begin and end. Found within the same paragraph even when begin and end are in different runs"""
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
    """Identifies the item kind from where the bookmark sits
    Inside a captioned object (cell paragraph, caption paragraph): the numbering type of the object. Inside a cell of a table without a caption: a band. Otherwise: the role of the paragraph style"""
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
    return [it for it in marks.values() if it.values]   # a bookmark without a page reference is not a TOC item


def _drop_ctrl(el):
    """Removes a control element. Removes the wrapping hp:ctrl as well when it holds no other control"""
    parent = el.getparent()
    _drop(parent if parent.tag == f"{HP}ctrl" and len(parent) == 1 else el)


def _static_hwpx(src: str, out: str, names: set[str]):
    """Removes the field begin and end of cross-references (page number, bookmark name) that target the given bookmarks and keeps the stored value text. Removes the target bookmarks
    Why the line layout values (linesegarray) are kept: removing them changes the page layout in renderers that recalculate line breaks"""
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
    """List of fields (document order). instr: instruction, parts: the fldChar and instrText elements of the field, result: result text elements, simple: fldSimple element
    Why a traversal: Word and LibreOffice save field elements split across runs, so begin and end are paired by fldChar order without relying on the run structure"""
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
    """(bookmark name, whether it is a page reference, field) of fields that target a bookmark. Footnote number references (NOTEREF) are not included"""
    out = []
    for f in _docx_fields(root):
        m = DOCX_REF_RE.match(f["instr"])
        if m:
            out.append((m.group(2), m.group(1) == "PAGEREF", f))
    return out


def _docx_roots(path: str) -> tuple[bytes, "ET._Element", dict[str, str]]:
    """Raw body XML, body root, style id → lower-case style name"""
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
    """Paragraph holding the bookmark. A bookmark placed between paragraphs belongs to the next paragraph"""
    for a in mark.iterancestors():
        if a.tag == f"{W}p":
            return a
    nxt = mark.getnext()
    while nxt is not None and nxt.tag != f"{W}p":
        nxt = nxt.getnext()
    return nxt


def _docx_kind(para, style_kinds: dict[str, str], styles: dict[str, str]) -> str:
    """Inside a table cell: a band. Otherwise: the role of the paragraph style (heading, table caption, figure caption)"""
    if para is None:
        return OTHER
    text = "".join(t.text or "" for t in para.iter(f"{W}t"))
    if any(a.tag == f"{W}tc" for a in para.iterancestors()):
        return _band_kind(text)
    style = para.find(f"{W}pPr/{W}pStyle")
    return style_kinds.get(styles.get(style.get(f"{W}val"), "") if style is not None else "", OTHER)


def _scan_docx(path: str, style_kinds: dict[str, str]) -> list[TocItem]:
    _, root, styles = _docx_roots(path)
    kinds = {k.lower(): v for k, v in style_kinds.items()}   # Word and LibreOffice save built-in style names with different letter case
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
    """Removes the fldChar and instrText of PAGEREF and REF fields that target the given bookmarks and keeps the result text. A fldSimple is only unwrapped
    Removes the bookmarkStart of each target bookmark and the bookmarkEnd with the same id"""
    data, root, _ = _docx_roots(src)
    for name, _, f in _docx_refs(root):
        if name not in names:
            continue
        for el in f["parts"]:
            run = el.getparent()
            _drop(el)
            if all(c.tag == f"{W}rPr" for c in run):   # a run that held only field elements
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
    """Bookmark name → PAGEREF result text"""
    _, root, _ = _docx_roots(path)
    return {name: "".join(t.text or "" for t in f["result"]) for name, is_page, f in _docx_refs(root) if is_page}


# ── Entry points for both formats ──────────────────────────────────────────
def scan(path: str, style_kinds: dict[str, str]) -> list[TocItem]:
    """List of bookmarks targeted by page references (document order). style_kinds: paragraph style name → item kind"""
    return (_scan_docx if is_docx(path) else _scan_hwpx)(path, style_kinds)


def make_static(src: str, out: str, names: set[str]):
    """Writes to out a copy in which the bookmarks named in names and the references to them are turned into plain text"""
    (_static_docx if is_docx(src) else _static_hwpx)(src, out, names)
