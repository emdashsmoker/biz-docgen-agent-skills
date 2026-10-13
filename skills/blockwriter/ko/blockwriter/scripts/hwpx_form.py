"""form.py의 양식 정의로 HWPX 스켈레톤(빈 양식 파일)을 만든다.

스켈레톤에는 양식이 쓰는 스타일과 그 스타일이 참조하는 글꼴, 글자 모양, 문단 모양,
글머리표, 개요 번호, 탭, 테두리 정의만 들어간다. 조판기는 이 파일을 열어 본문을 채운다.
"""
from __future__ import annotations

import zipfile

from lxml import etree as ET

from form import BORDER_FILLS, FONT_CATALOG, LANGS, TABS, ABSENT, Form

NS = {
    "ha": "http://www.hancom.co.kr/hwpml/2011/app",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hp10": "http://www.hancom.co.kr/hwpml/2016/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hhs": "http://www.hancom.co.kr/hwpml/2011/history",
    "hm": "http://www.hancom.co.kr/hwpml/2011/master-page",
    "hpf": "http://www.hancom.co.kr/schema/2011/hpf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "opf": "http://www.idpf.org/2007/opf/",
    "ooxmlchart": "http://www.hancom.co.kr/hwpml/2016/ooxmlchart",
    "hwpunitchar": "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar",
    "epub": "http://www.idpf.org/2007/ops",
    "config": "urn:oasis:names:tc:opendocument:xmlns:config:1.0",
}
HH, HP, HC, HS = (f"{{{NS[k]}}}" for k in ("hh", "hp", "hc", "hs"))
XML_DECL = b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
# 쪽 테두리 간격 5mm, 단 간격 4mm, 기본 탭 간격 40pt는 한/글 새 문서 기본값
PAGE_BORDER_OFFSET = 1417
COLUMN_GAP = 1134
TYPE_INFO_KEYS = ("familyType", "weight", "proportion", "contrast", "strokeVariation",
                  "armStyle", "letterform", "midline", "xHeight")
# 메모 모양. 인쇄에 나타나지 않는 편집 화면 설정이며 한/글 새 문서 기본값
MEMO_SHAPE = dict(width="15591", lineWidth="1", lineType="SOLID", lineColor="#B6D7AE",
                  fillColor="#F0FFE9", activeColor="#CFF1C7", memoType="NOMAL")


def _sub(parent, tag: str, **attrs):
    el = ET.SubElement(parent, tag)
    for k, v in attrs.items():
        el.set(k, str(v))
    return el


class _Registry:
    """양식에서 쓰는 정의를 모아 번호를 붙인다. 같은 내용은 하나의 번호를 공유한다."""

    def __init__(self, form: Form):
        self.fonts = {lang: [] for lang in LANGS}
        self.borders = ["plain"] + [k for k in BORDER_FILLS if k != "plain"]
        self.chars: list = []
        self.paras: list = []
        self.bullets: list = []
        self.tabs = ["none"] + [k for k in TABS if k != "none"]
        _, first_para, first_char = form.first_para
        self.char_id(form.default_char)   # 0번 글자 모양: 조판 라이브러리가 기본값으로 참조
        self.para_id(first_para)          # 0번 문단 모양: 구역 설정 문단이 참조
        self.char_id(first_char)
        for st in form.styles:
            self.para_id(st.para)
            self.char_id(st.char)
        used_tabs = {st.para.tab for st in form.styles} | {first_para.tab}
        self.tabs = [t for t in self.tabs if t in used_tabs]

    def char_id(self, char) -> int:
        for lang, face in zip(LANGS, char.faces):
            if face not in self.fonts[lang]:
                self.fonts[lang].append(face)
        if char not in self.chars:
            self.chars.append(char)
        return self.chars.index(char)

    def para_id(self, para) -> int:
        head = para.head
        if isinstance(head, tuple) and head[0] == "BULLET" and head[1:] not in self.bullets:
            self.bullets.append(head[1:])
        if para not in self.paras:
            self.paras.append(para)
        return self.paras.index(para)

    def font_id(self, lang: str, face: str) -> int:
        return self.fonts[lang].index(face)

    def border_id(self, key: str) -> int:
        return self.borders.index(key) + 1   # 테두리 번호는 1부터

    def bullet_id(self, head: tuple) -> int:
        return self.bullets.index(head[1:]) + 1


def _font_faces(root, reg: _Registry):
    ff = _sub(root, HH + "fontfaces", itemCnt=len(LANGS))
    for lang in LANGS:
        fl = _sub(ff, HH + "fontface", lang=lang.upper(), fontCnt=len(reg.fonts[lang]))
        for i, face in enumerate(reg.fonts[lang]):
            ftype, info = FONT_CATALOG[face]
            f = _sub(fl, HH + "font", id=i, face=face, type=ftype, isEmbedded=0)
            _sub(f, HH + "typeInfo", **dict(zip(TYPE_INFO_KEYS, info)))


def _border_fills(root, reg: _Registry):
    bf = _sub(root, HH + "borderFills", itemCnt=len(reg.borders))
    for i, key in enumerate(reg.borders, 1):
        el = _sub(bf, HH + "borderFill", id=i, threeD=0, shadow=0, centerLine="NONE", breakCellSeparateLine=0)
        _sub(el, HH + "slash", type="NONE", Crooked=0, isCounter=0)
        _sub(el, HH + "backSlash", type="NONE", Crooked=0, isCounter=0)
        for side in ("left", "right", "top", "bottom"):
            _sub(el, HH + f"{side}Border", type="NONE", width="0.1 mm", color="#000000")
        _sub(el, HH + "diagonal", type="SOLID", width="0.1 mm", color="#000000")
        hatch = BORDER_FILLS[key]
        if hatch is not None:
            brush = _sub(el, HC + "fillBrush")
            _sub(brush, HC + "winBrush", faceColor="none", hatchColor=hatch, alpha=0)


def _char_properties(root, reg: _Registry):
    cp = _sub(root, HH + "charProperties", itemCnt=len(reg.chars))
    for i, c in enumerate(reg.chars):
        el = _sub(cp, HH + "charPr", id=i, height=round(c.size * 100), textColor="#000000", shadeColor="none",
                  useFontSpace=0, useKerning=0, symMark="NONE", borderFillIDRef=reg.border_id(c.border))
        _sub(el, HH + "fontRef", **{l: reg.font_id(l, f) for l, f in zip(LANGS, c.faces)})
        _sub(el, HH + "ratio", **dict(zip(LANGS, c.ratios)))
        _sub(el, HH + "spacing", **dict(zip(LANGS, c.spacings)))
        _sub(el, HH + "relSz", **{l: 100 for l in LANGS})
        _sub(el, HH + "offset", **{l: 0 for l in LANGS})
        if c.bold:
            _sub(el, HH + "bold")
        _sub(el, HH + "underline", type="NONE", shape="SOLID", color="#000000")
        _sub(el, HH + "strikeout", shape="NONE", color="#000000")
        _sub(el, HH + "outline", type="NONE")
        _sub(el, HH + "shadow", type="NONE", color=c.shadow, offsetX=10, offsetY=10)


def _hwpunit_switch(parent, build):
    """새 한/글은 case(HWPUNIT 단위)를, 구형 한/글은 default를 읽는다"""
    sw = _sub(parent, HP + "switch")
    case = _sub(sw, HP + "case")
    case.set(HP + "required-namespace", NS["hwpunitchar"])
    build(case, True)
    build(_sub(sw, HP + "default"), False)


def _tab_properties(root, reg: _Registry):
    tp = _sub(root, HH + "tabProperties", itemCnt=len(reg.tabs))
    for i, key in enumerate(reg.tabs):
        spec = TABS[key]
        el = _sub(tp, HH + "tabPr", id=i, autoTabLeft=int(spec["auto_left"]), autoTabRight=0)
        for pos, kind, leader in spec["items"]:
            def item(parent, modern, pos=pos, kind=kind, leader=leader):
                attrs = dict(pos=pos if modern else pos * 2, type=kind, leader=leader)
                if modern:
                    attrs["unit"] = "HWPUNIT"
                _sub(parent, HH + "tabItem", **attrs)
            _hwpunit_switch(el, item)


def _numberings(root, form: Form):
    nb = _sub(root, HH + "numberings", itemCnt=1)
    el = _sub(nb, HH + "numbering", id=1, start=form.outline_start)
    for level, (text, inst_width) in enumerate(form.outline_levels, 1):
        ph = _sub(el, HH + "paraHead", start=1, level=level, align="LEFT", useInstWidth=int(inst_width),
                  autoIndent=1, widthAdjust=0, textOffsetType="PERCENT", textOffset=50, numFormat="DIGIT",
                  charPrIDRef=4294967295, checkable=0)
        ph.text = text


def _bullets(root, reg: _Registry):
    bl = _sub(root, HH + "bullets", itemCnt=len(reg.bullets))
    for i, (char, offset, adjust) in enumerate(reg.bullets, 1):
        el = _sub(bl, HH + "bullet", id=i, char=char, useImage=0)
        _sub(el, HH + "paraHead", level=0, align="LEFT", useInstWidth=0, autoIndent=1, widthAdjust=adjust,
             textOffsetType="PERCENT", textOffset=offset, numFormat="DIGIT", charPrIDRef=4294967295, checkable=0)


def _para_properties(root, reg: _Registry):
    pp = _sub(root, HH + "paraProperties", itemCnt=len(reg.paras))
    for i, p in enumerate(reg.paras):
        el = _sub(pp, HH + "paraPr", id=i, tabPrIDRef=reg.tabs.index(p.tab), condense=0, fontLineHeight=0,
                  snapToGrid=int(p.grid), suppressLineNumbers=0, checked=0)
        _sub(el, HH + "align", horizontal=p.align, vertical="BASELINE")
        if p.head != ABSENT:
            if p.head is None:
                _sub(el, HH + "heading", type="NONE", idRef=0, level=0)
            elif p.head[0] == "BULLET":
                _sub(el, HH + "heading", type="BULLET", idRef=reg.bullet_id(p.head), level=0)
            else:
                _sub(el, HH + "heading", type="OUTLINE", idRef=0, level=p.head[1])
        _sub(el, HH + "breakSetting", breakLatinWord="KEEP_WORD",
             breakNonLatinWord="BREAK_WORD" if p.break_word else "KEEP_WORD", widowOrphan=0,
             keepWithNext=1 if p.keep_next else 0,
             keepLines=0, pageBreakBefore=0, lineWrap="BREAK")
        _sub(el, HH + "autoSpacing", eAsianEng=0, eAsianNum=0)
        legacy = p.legacy_margin or tuple(2 * v for v in p.margin)

        def margin(parent, modern, p=p, legacy=legacy):
            m = _sub(parent, HH + "margin")
            for key, val in zip(("intent", "left", "right", "prev", "next"), p.margin if modern else legacy):
                _sub(m, HC + key, value=val, unit="HWPUNIT")
            _sub(parent, HH + "lineSpacing", type="PERCENT", value=p.line, unit="HWPUNIT")
        _hwpunit_switch(el, margin)
        _sub(el, HH + "border", borderFillIDRef=reg.border_id(p.border), offsetLeft=0, offsetRight=0,
             offsetTop=0, offsetBottom=0, connect=0, ignoreMargin=0)


def _styles(root, form: Form, reg: _Registry):
    sl = _sub(root, HH + "styles", itemCnt=len(form.styles))
    for i, st in enumerate(form.styles):
        _sub(sl, HH + "style", id=i, type=st.kind, name=st.name, engName=st.eng,
             paraPrIDRef=reg.para_id(st.para), charPrIDRef=reg.char_id(st.char),
             nextStyleIDRef=i if st.next_self else 0, langID=1042, lockForm=0)


def header_xml(form: Form) -> bytes:
    reg = _Registry(form)
    root = ET.Element(HH + "head", nsmap=NS)
    root.set("version", "1.4")
    root.set("secCnt", "1")
    _sub(root, HH + "beginNum", page=1, footnote=1, endnote=1, pic=1, tbl=1, equation=1)
    ref = _sub(root, HH + "refList")
    _font_faces(ref, reg)
    _border_fills(ref, reg)
    _char_properties(ref, reg)
    _tab_properties(ref, reg)
    _numberings(ref, form)
    _bullets(ref, reg)
    _para_properties(ref, reg)
    _styles(ref, form, reg)
    memo = _sub(ref, HH + "memoProperties", itemCnt=1)
    _sub(memo, HH + "memoPr", id=1, **MEMO_SHAPE)
    compat = _sub(root, HH + "compatibleDocument", targetProgram="HWP201X")
    _sub(compat, HH + "layoutCompatibility")
    opt = _sub(root, HH + "docOption")
    _sub(opt, HH + "linkinfo", path="", pageInherit=0, footnoteInherit=0)
    _sub(root, HH + "trackchageConfig", flags=56)
    return XML_DECL + ET.tostring(root, encoding="UTF-8")


def _note_pr(parent, tag: str, note, suffix: str):
    el = _sub(parent, HP + tag)
    _sub(el, HP + "autoNumFormat", type="DIGIT", userChar="", prefixChar="", suffixChar=suffix, supscript=0)
    _sub(el, HP + "noteLine", length=note.line_length, type=note.line_type, width="0.12 mm", color="#000000")
    _sub(el, HP + "noteSpacing", betweenNotes=note.between, belowLine=note.below, aboveLine=note.above)
    _sub(el, HP + "numbering", type="CONTINUOUS", newNum=1)
    _sub(el, HP + "placement", place=note.place, beneathText=0)


def section_xml(form: Form) -> bytes:
    """구역 설정(쪽 크기, 여백, 각주 모양)을 담은 첫 빈 문단 하나로 된 본문"""
    reg = _Registry(form)
    role, first_para, first_char = form.first_para
    style_id = [s.role for s in form.styles].index(role)
    pg = form.page
    root = ET.Element(HS + "sec", nsmap=NS)
    p = _sub(root, HP + "p", id=0, paraPrIDRef=reg.para_id(first_para), styleIDRef=style_id,
             pageBreak=0, columnBreak=0, merged=0)
    run = _sub(p, HP + "run", charPrIDRef=reg.char_id(first_char))
    sec = _sub(run, HP + "secPr", id="", textDirection="HORIZONTAL", spaceColumns=COLUMN_GAP, tabStop=8000,
               tabStopVal=4000, tabStopUnit="HWPUNIT", outlineShapeIDRef=1, memoShapeIDRef=1,
               textVerticalWidthHead=0, masterPageCnt=0)
    _sub(sec, HP + "grid", lineGrid=0, charGrid=0, wonggojiFormat=0)
    _sub(sec, HP + "startNum", pageStartsOn="BOTH", page=0, pic=0, tbl=0, equation=0)
    _sub(sec, HP + "visibility", hideFirstHeader=0, hideFirstFooter=0, hideFirstMasterPage=0, border="SHOW_ALL",
         fill="SHOW_ALL", hideFirstPageNum=0, hideFirstEmptyLine=0, showLineNumber=0)
    _sub(sec, HP + "lineNumberShape", restartType=0, countBy=0, distance=0, startNumber=0)
    pp = _sub(sec, HP + "pagePr", landscape="WIDELY", width=pg.width, height=pg.height, gutterType="LEFT_ONLY")
    _sub(pp, HP + "margin", header=pg.header, footer=pg.footer, gutter=0, left=pg.left, right=pg.right,
         top=pg.top, bottom=pg.bottom)
    _note_pr(sec, "footNotePr", pg.footnote, pg.note_suffix)
    _note_pr(sec, "endNotePr", pg.endnote, pg.note_suffix)
    for kind in ("BOTH", "EVEN", "ODD"):
        pbf = _sub(sec, HP + "pageBorderFill", type=kind, borderFillIDRef=1, textBorder="PAPER",
                   headerInside=0, footerInside=0, fillArea="PAPER")
        off = PAGE_BORDER_OFFSET
        _sub(pbf, HP + "offset", left=off, right=off, top=off, bottom=off)
    col = _sub(run, HP + "ctrl")
    _sub(col, HP + "colPr", id="", type="NEWSPAPER", layout="LEFT", colCount=1, sameSz=1, sameGap=0)
    if form.restart_page_number:
        _sub(_sub(run, HP + "ctrl"), HP + "newNum", num=1, numType="PAGE")
    _sub(run, HP + "t")
    # 첫 문단 줄 배치 저장값. 렌더러가 이 값으로 첫 줄 위치를 잡으므로 양식 정의 값을 그대로 기록
    vert, height, text_h, base, gap, width, flags = form.first_line
    segs = _sub(p, HP + "linesegarray")
    _sub(segs, HP + "lineseg", textpos=0, vertpos=vert, vertsize=height, textheight=text_h, baseline=base,
         spacing=gap, horzpos=0, horzsize=width, flags=flags)
    return XML_DECL + ET.tostring(root, encoding="UTF-8")


CONTENT_HPF = (
    '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/" version="" unique-identifier="" id="">'
    '<opf:metadata><opf:title/><opf:language>ko</opf:language>'
    + "".join(f'<opf:meta name="{n}" content="text"/>' for n in
              ("creator", "subject", "description", "lastsaveby", "CreatedDate", "ModifiedDate", "date", "keyword"))
    + '</opf:metadata><opf:manifest>'
    '<opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>'
    '<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>'
    '<opf:item id="settings" href="settings.xml" media-type="application/xml"/>'
    '</opf:manifest><opf:spine><opf:itemref idref="header" linear="yes"/>'
    '<opf:itemref idref="section0" linear="yes"/></opf:spine></opf:package>')
SETTINGS_XML = (
    '<ha:HWPApplicationSetting xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
    'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">'
    '<ha:CaretPosition listIDRef="0" paraIDRef="0" pos="0"/></ha:HWPApplicationSetting>')
VERSION_XML = (
    '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" tagetApplication="WORDPROCESSOR" '
    'major="5" minor="0" micro="5" buildNumber="0" os="1" xmlVersion="1.4" application="Hancom Office Hangul" '
    'appVersion="9, 6, 1, 0 WIN32LEWindows_Unknown_Version"/>')
CONTAINER_XML = (
    '<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container" '
    'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"><ocf:rootfiles>'
    '<ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/>'
    '<ocf:rootfile full-path="Preview/PrvText.txt" media-type="text/plain"/></ocf:rootfiles></ocf:container>')
MANIFEST_XML = '<odf:manifest xmlns:odf="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>'


def write_skeleton(form: Form, path: str) -> str:
    """HWPX 패키지 규칙: mimetype이 첫 항목이며 압축하지 않는다"""
    parts = [
        ("version.xml", XML_DECL + VERSION_XML.encode("utf-8")),
        ("Contents/header.xml", header_xml(form)),
        ("Contents/section0.xml", section_xml(form)),
        ("Preview/PrvText.txt", b""),
        ("settings.xml", XML_DECL + SETTINGS_XML.encode("utf-8")),
        ("META-INF/container.xml", XML_DECL + CONTAINER_XML.encode("utf-8")),
        ("Contents/content.hpf", XML_DECL + CONTENT_HPF.encode("utf-8")),
        ("META-INF/manifest.xml", XML_DECL + MANIFEST_XML.encode("utf-8")),
    ]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(zipfile.ZipInfo("mimetype"), b"application/hwp+zip", compress_type=zipfile.ZIP_STORED)
        for name, data in parts:
            z.writestr(name, data)
    return path
