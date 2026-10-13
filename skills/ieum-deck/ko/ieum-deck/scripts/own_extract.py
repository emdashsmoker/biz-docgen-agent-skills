#!/usr/bin/env python3
"""own_extract.py
사용자가 제공한 PPTX 의 슬라이드 도형 전수를 절대 좌표(인치)의 원자 요소 목록으로 추출하여
build.js 가 재생(playback)할 수 있는 own-deck.json 을 생성한다. 배포본에는 커스텀 슬라이드 데이터가 없으며
이 경로는 조직이 보유한 슬라이드 배치를 정답 좌표로 재사용하려는 경우에만 쓴다.

왜 필요한가: 카탈로그 설명만으로 좌표를 근사하면 원본 장표의 배치를 재현하지 못한다. 실측 좌표를 코드로 옮겨야
원본과 같은 배치를 검증 가능한 방식으로 재생할 수 있다.

처리 내용
- 그룹 도형의 자식 좌표를 chOff/chExt 기준에서 슬라이드 절대 좌표로 변환 (중첩 그룹 포함)
- 글꼴 크기 상속(run → 도형 lstStyle → 레이아웃 자리표시자 → 마스터 → 프레젠테이션 기본값) 해소
- 테마 색상(schemeClr) 을 RGB 로 해소. 스킬 색 토큰으로의 대응은 설정 파일 colorMap 이 담당
- 표(병합, 셀 채움, 셀 텍스트 서식), 차트(유형, 범주, 계열값), 이미지(자리만 기록) 추출
- 자리표시자는 밴드 원자로 분류하여 본문에서 제외 (build.js 가 스킬의 밴드로 다시 그림)
- 회사 식별 문구를 설정 파일 규칙으로 일반화하고 식별 요소에 identity 태그 부여

사용
  python3 own_extract.py --inspect <원본.pptx>                       레이아웃과 자리표시자 목록 출력 (설정 작성용)
  python3 own_extract.py <원본.pptx> <own-deck.json> [--config deck-config.json]

설정 파일(deck-config.json) 키. 모두 선택 항목
  bandPlaceholders  {"자리표시자 idx": "secNo|secTitle|tracker|headline|marker|pageNo"}  밴드 역할 대응
  layoutModes       {"레이아웃 이름": "full|noMarker|headerOnly|blank"}               슬라이드 밴드 모드 (미지정 full)
  identityText      "정규식"  회사명 등 식별 문구. 일치한 도형에 identity 태그
  identityCheck     "정규식"  추출 후 잔존 여부를 점검할 식별 문구
  generalize        [{"pattern": "정규식", "replace": "치환", "slides": [N]}]  식별 문구 일반화 규칙
  identityPicSlides [N]  그림을 식별 요소(로고)로 취급할 슬라이드
  zeroTableSlides   [N]  표 안 숫자를 0 으로 바꿀 슬라이드 (실제 재무 수치 등)
  dropAtoms         {"N": ["도형 이름"]}  재생에서 뺄 도형
  dropTexts         {"N": ["문구"]}      재생에서 뺄 텍스트 도형
  roles             {"역할": [N]}  module_overview, org_project, people_table, pm_profile, company_fact, collaboration
  descriptions      {"N": "용도 설명"}  own_catalog.py 가 슬롯 목록에 기재
  colorMap          {"원본 RGB": "tokens.js COLOR 키"}  테마 전환 시 함께 바뀔 원본 색
"""
import json
import re
from pathlib import Path
import sys
from pptx import Presentation
from pptx.util import Emu

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
EMU_PER_IN = 914400
DEFAULT_TEXT_PT = 18.0  # presentation.xml 의 defaultTextStyle 이 없을 때 OOXML 기본 글꼴 크기
MODES = ("full", "noMarker", "headerOnly", "blank")

CFG = {}
PLACEHOLDER_ROLE = {}
IDENTITY_TEXT = re.compile(r"(?!x)x")
IDENTITY_CHECK = r"(?!x)x"
GENERALIZE = []
IDENTITY_PIC_SLIDES = set()
IDENTITY_TABLE_SLIDES = set()
DROP_ATOMS = {}
DROP_TEXTS = {}


def load_config(path):
    """설정 파일을 읽어 모듈 전역 규칙에 반영. 파일이 없으면 규칙 없이 원문 그대로 추출"""
    global CFG, PLACEHOLDER_ROLE, IDENTITY_TEXT, IDENTITY_CHECK, GENERALIZE, IDENTITY_PIC_SLIDES, IDENTITY_TABLE_SLIDES, DROP_ATOMS, DROP_TEXTS
    CFG = json.loads(Path(path).read_text(encoding="utf-8")) if path else {}
    PLACEHOLDER_ROLE = {int(k): v for k, v in (CFG.get("bandPlaceholders") or {}).items()}
    IDENTITY_TEXT = re.compile(CFG.get("identityText") or r"(?!x)x")
    IDENTITY_CHECK = CFG.get("identityCheck") or r"(?!x)x"
    GENERALIZE = [(r["pattern"], r["replace"], set(r.get("slides", []))) for r in CFG.get("generalize", [])]
    IDENTITY_PIC_SLIDES = set(CFG.get("identityPicSlides", []))
    IDENTITY_TABLE_SLIDES = set(CFG.get("zeroTableSlides", []))
    DROP_ATOMS = {int(k): set(v) for k, v in (CFG.get("dropAtoms") or {}).items()}
    DROP_TEXTS = {int(k): list(v) for k, v in (CFG.get("dropTexts") or {}).items()}


CUR_SLIDE = [0]


def generalize(text):
    for item in GENERALIZE:
        pat, rep = item[0], item[1]
        if item[2] and CUR_SLIDE[0] not in item[2]:
            continue
        text = re.sub(pat, rep, text)
    return text


def generalize_paras(paras):
    """문단 단위 치환. run 이 쪼개진 식별 문구도 잡기 위해 문단 텍스트를 합쳐 치환한 뒤 첫 run 에 담고 나머지 run 은 비움"""
    for p in paras or []:
        joined = "".join("\n" if r.get("br") else r["t"] for r in p["runs"])
        new = generalize(joined)
        if new == joined:
            continue
        base = next((r for r in p["runs"] if not r.get("br")), None)
        if base is None:
            continue
        # 치환 후 텍스트를 줄바꿈 단위로 나누어 run 과 br 을 다시 구성 (빈 줄이 남지 않게)
        segs = [x for x in new.split("\n")]
        runs = []
        for k, seg in enumerate(segs):
            if k:
                runs.append({"t": "\n", "sz": base.get("sz"), "b": False, "color": base.get("color"), "br": True})
            if seg:
                runs.append({**base, "t": seg})
        p["runs"] = runs or [{**base, "t": ""}]


WINGDINGS_MAP = {"ü": "✓", "n": "■", "l": "●", "p": "□", "q": "□", "Ø": "→", "§": "▪", "v": "❖", "u": "◆", "w": "◆", "ñ": "▪"}
# 유니코드 사용자 정의 영역(BMP). 기호 글꼴 문자가 이 범위의 코드로 저장됨
PUA_FIRST, PUA_LAST = 0xE000, 0xF8FF


def emu(v):
    return round(v / EMU_PER_IN, 3) if v is not None else None


def theme_colors(prs):
    part = prs.slide_masters[0].part
    for rel in part.rels.values():
        if rel.reltype.endswith("/theme"):
            xml = rel.target_part.blob.decode("utf-8")
            m = re.search(r"<a:clrScheme.*?</a:clrScheme>", xml, re.S)
            pairs = re.findall(r"<a:(dk1|lt1|dk2|lt2|accent\d|hlink|folHlink)>.*?val=\"(\w+)\"", m.group(0), re.S)
            d = dict(pairs)
            d.update({"tx1": d["dk1"], "bg1": d["lt1"], "tx2": d["dk2"], "bg2": d["lt2"]})
            return d
    return {}


def solid_color(el, theme):
    """el: a:solidFill 또는 그 부모. 없으면 None"""
    if el is None:
        return None
    srgb = el.find(".//a:srgbClr", NS)
    if srgb is not None:
        return srgb.get("val").upper()
    sc = el.find(".//a:schemeClr", NS)
    if sc is not None:
        base = theme.get(sc.get("val"))
        lum = sc.find("a:lumMod", NS)
        off = sc.find("a:lumOff", NS)
        if base and (lum is not None or off is not None):
            return tint(base, int(lum.get("val")) / 100000 if lum is not None else 1.0,
                        int(off.get("val")) / 100000 if off is not None else 0.0)
        return base
    return None


def tint(hex6, lum_mod, lum_off):
    """schemeClr lumMod/lumOff 근사. HSL 명도 변환 대신 RGB 선형 근사 (검수 기준 육안 대조)"""
    r, g, b = int(hex6[0:2], 16), int(hex6[2:4], 16), int(hex6[4:6], 16)
    def f(c):
        v = c * lum_mod + 255 * lum_off
        return max(0, min(255, int(round(v))))
    return "%02X%02X%02X" % (f(r), f(g), f(b))


def alpha_of(sppr):
    """solidFill 의 alpha(0-100000) → 불투명도 %. 없으면 None"""
    if sppr is None:
        return None
    a = sppr.find("a:solidFill//a:alpha", NS)
    return int(a.get("val")) / 1000 if a is not None else None


def fill_of(sppr, theme):
    if sppr is None:
        return None
    if sppr.find("a:noFill", NS) is not None:
        return "none"
    sf = sppr.find("a:solidFill", NS)
    if sf is not None:
        return solid_color(sf, theme)
    if sppr.find("a:gradFill", NS) is not None:
        return "gradient"
    return None  # 스타일 상속


def line_of(sppr, theme):
    if sppr is None:
        return None
    ln = sppr.find("a:ln", NS)
    if ln is None:
        return None
    if ln.find("a:noFill", NS) is not None:
        return {"color": "none"}
    d = {}
    w = ln.get("w")
    d["pt"] = round(int(w) / 12700, 2) if w else None
    sf = ln.find("a:solidFill", NS)
    d["color"] = solid_color(sf, theme) if sf is not None else None
    dash = ln.find("a:prstDash", NS)
    if dash is not None:
        d["dash"] = dash.get("val")
    for tag, key in (("headEnd", "head"), ("tailEnd", "tail")):
        e = ln.find("a:" + tag, NS)
        if e is not None and e.get("type", "none") != "none":
            d[key] = e.get("type")
    return d


def style_ref(sp, theme):
    """p:style 의 fillRef/lnRef/fontRef 로 상속되는 색을 해소 (채움과 선 미지정 도형용)"""
    st = sp.find("p:style", NS)
    if st is None:
        return {}
    out = {}
    fr = st.find("a:fillRef", NS)
    if fr is not None and fr.get("idx", "0") != "0":
        out["fill"] = solid_color(fr, theme)
    lr = st.find("a:lnRef", NS)
    if lr is not None and lr.get("idx", "0") != "0":
        out["line"] = solid_color(lr, theme)
    fo = st.find("a:fontRef", NS)
    if fo is not None:
        out["font"] = solid_color(fo, theme)
    return out


def placeholder_size(shape, slide):
    """자리표시자 텍스트 크기의 상속 해소: 레이아웃 → 마스터"""
    try:
        idx = shape.placeholder_format.idx
    except Exception:
        return None
    for holder in (slide.slide_layout, slide.slide_layout.slide_master):
        for ph in holder.placeholders:
            if ph.placeholder_format.idx == idx:
                for tag in (".//a:lvl1pPr/a:defRPr", ".//a:defRPr", ".//a:rPr", ".//a:endParaRPr"):
                    e = ph._element.find(tag, NS)
                    if e is not None and e.get("sz"):
                        return int(e.get("sz")) / 100
    return None


def para_props(p_el, ppr=None):
    ppr = p_el.find("a:pPr", NS) if ppr is None else ppr
    d = {}
    if ppr is None:
        return d
    if ppr.get("algn"):
        d["align"] = {"l": "left", "ctr": "center", "r": "right", "just": "justify"}.get(ppr.get("algn"), "left")
    lvl = ppr.get("lvl")
    if lvl:
        d["lvl"] = int(lvl)
    if ppr.find("a:buChar", NS) is not None or ppr.find("a:buAutoNum", NS) is not None or ppr.find("a:buBlip", NS) is not None:
        d["bullet"] = True
        if ppr.find("a:buBlip", NS) is not None:
            d["buChar"] = "◉"  # 그림 불릿(아이콘) 은 나눔고딕 기호로 대체
        bc = ppr.find("a:buChar", NS)
        if bc is not None:
            ch = bc.get("char")
            bf = ppr.find("a:buFont", NS)
            # Wingdings 계열 기호는 배포 환경에 없으므로 유니코드 기호로 치환
            if bf is not None and str(bf.get("typeface", "")).startswith("Wingdings"):
                ch = WINGDINGS_MAP.get(ch, "•")
            # 기호 글꼴의 사용자 정의 영역 문자(Symbol 글꼴 불릿 U+F0B7 등)는 나눔고딕에 글리프가 없어 빈 네모로 보이므로 둥근 점으로 치환
            if ch and PUA_FIRST <= ord(ch[0]) <= PUA_LAST:
                ch = "•"
            d["buChar"] = ch
        an = ppr.find("a:buAutoNum", NS)
        if an is not None:
            d["buNum"] = an.get("type", "arabicPeriod")
    if ppr.find("a:buNone", NS) is not None:
        d["bullet"] = False
    marl = ppr.get("marL")
    if marl:
        d["marL"] = emu(int(marl))
    ind = ppr.get("indent")
    if ind:
        d["indent"] = emu(int(ind))
    sb = ppr.find("a:spcBef/a:spcPts", NS)
    if sb is not None:
        d["spcBef"] = int(sb.get("val")) / 100
    sa = ppr.find("a:spcAft/a:spcPts", NS)
    if sa is not None:
        d["spcAft"] = int(sa.get("val")) / 100
    ls = ppr.find("a:lnSpc/a:spcPct", NS)
    if ls is not None:
        d["lnSpc"] = int(ls.get("val")) / 100000
    return d


def text_of(txbody, theme, default_sz, font_color_default):
    """txBody → paragraphs: [{runs:[{t,sz,b,color}], align, bullet, lvl, ...}]"""
    if txbody is None:
        return None, {}
    bp = txbody.find("a:bodyPr", NS)
    body = {}
    if bp is not None:
        body["va"] = {"t": "top", "ctr": "middle", "b": "bottom"}.get(bp.get("anchor"), "top")
        body["mg"] = [emu(int(bp.get(k))) if bp.get(k) else None for k in ("lIns", "tIns", "rIns", "bIns")]
        body["wrap"] = bp.get("wrap", "square")
        body["autofit"] = "sp" if bp.find("a:spAutoFit", NS) is not None else ("norm" if bp.find("a:normAutofit", NS) is not None else None)
        na = bp.find("a:normAutofit", NS)
        if na is not None and na.get("fontScale"):
            body["fontScale"] = int(na.get("fontScale")) / 100000
        if bp.get("vert"):
            body["vert"] = bp.get("vert")
    # 도형 lstStyle 의 기본 크기
    lst_sz = None
    ls = txbody.find("a:lstStyle/a:lvl1pPr/a:defRPr", NS)
    if ls is not None and ls.get("sz"):
        lst_sz = int(ls.get("sz")) / 100
    # 도형 lstStyle 의 문단 기본값(불릿, 정렬, 들여쓰기). 문단 자체 값이 없을 때 적용
    lst_p = {}
    lp = txbody.find("a:lstStyle/a:lvl1pPr", NS)
    if lp is not None:
        lst_p = para_props(None, lp)
    paras = []
    for p_el in txbody.findall("a:p", NS):
        pp = dict(lst_p)
        pp.update(para_props(p_el))
        runs = []
        for r in p_el.findall("a:r", NS):
            rpr = r.find("a:rPr", NS)
            t = r.find("a:t", NS)
            txt = t.text if t is not None and t.text else ""
            run = {"t": txt}
            sz = rpr.get("sz") if rpr is not None else None
            run["sz"] = int(sz) / 100 if sz else (lst_sz or default_sz)
            b = rpr.get("b") if rpr is not None else None
            lat = rpr.find("a:latin", NS) if rpr is not None else None
            face = lat.get("typeface") if lat is not None else None
            run["b"] = (b == "1") or bool(face and "Bold" in face)
            col = solid_color(rpr.find("a:solidFill", NS), theme) if rpr is not None and rpr.find("a:solidFill", NS) is not None else None
            run["color"] = col or font_color_default
            if rpr is not None and rpr.get("u"):
                run["u"] = True
            runs.append(run)
        for br in p_el.findall("a:br", NS):
            pass  # a:br 은 아래에서 순서 처리
        # a:br 를 순서대로 반영하기 위해 자식 순회로 재구성
        seq = []
        for child in p_el:
            tag = child.tag.split("}")[1]
            if tag == "r":
                seq.append(runs.pop(0))
            elif tag == "br":
                seq.append({"t": "\n", "sz": default_sz, "b": False, "color": font_color_default, "br": True})
        if not seq:
            # 빈 문단: endParaRPr 크기만 기록 (줄 높이 산정용)
            ep = p_el.find("a:endParaRPr", NS)
            esz = int(ep.get("sz")) / 100 if ep is not None and ep.get("sz") else (lst_sz or default_sz)
            seq = [{"t": "", "sz": esz, "b": False, "color": font_color_default}]
        pp["runs"] = seq
        paras.append(pp)
    # 문단 전체가 비었으면 텍스트 없음
    if all(all(r["t"].strip() == "" for r in p["runs"]) for p in paras):
        return None, body
    return paras, body


def xfrm_of(sp):
    x = sp.find(".//a:xfrm", NS)
    if x is None:
        return None
    off = x.find("a:off", NS)
    ext = x.find("a:ext", NS)
    d = {"x": int(off.get("x")), "y": int(off.get("y")), "w": int(ext.get("cx")), "h": int(ext.get("cy"))}
    d["rot"] = int(x.get("rot", "0")) / 60000
    d["flipH"] = x.get("flipH") == "1"
    d["flipV"] = x.get("flipV") == "1"
    ch_off = x.find("a:chOff", NS)
    ch_ext = x.find("a:chExt", NS)
    if ch_off is not None:
        d["chOff"] = (int(ch_off.get("x")), int(ch_off.get("y")))
        d["chExt"] = (int(ch_ext.get("cx")), int(ch_ext.get("cy")))
    return d


def preset_of(sp):
    pg = sp.find(".//a:prstGeom", NS)
    if pg is not None:
        return pg.get("prst")
    if sp.find(".//a:custGeom", NS) is not None:
        return "custom"
    return None


def table_of(gf, theme):
    tbl = gf.find(".//a:tbl", NS)
    if tbl is None:
        return None
    colw = [emu(int(c.get("w"))) for c in tbl.findall("a:tblGrid/a:gridCol", NS)]
    rows = []
    rowh = []
    for tr in tbl.findall("a:tr", NS):
        rowh.append(emu(int(tr.get("h"))))
        cells = []
        for tc in tr.findall("a:tc", NS):
            cell = {}
            if tc.get("gridSpan"):
                cell["colspan"] = int(tc.get("gridSpan"))
            if tc.get("rowSpan"):
                cell["rowspan"] = int(tc.get("rowSpan"))
            if tc.get("hMerge") == "1" or tc.get("vMerge") == "1":
                cell["merged"] = True
            tcpr = tc.find("a:tcPr", NS)
            if tcpr is not None:
                cell["fill"] = fill_of(tcpr, theme)
                cell["va"] = {"t": "top", "ctr": "middle", "b": "bottom"}.get(tcpr.get("anchor"), "top")
                cell["mg"] = [emu(int(tcpr.get(k))) if tcpr.get(k) else None for k in ("marL", "marT", "marR", "marB")]
                borders = {}
                for side in ("lnL", "lnR", "lnT", "lnB"):
                    ln = tcpr.find("a:" + side, NS)
                    if ln is not None:
                        if ln.find("a:noFill", NS) is not None:
                            borders[side[2]] = {"color": "none"}
                        else:
                            borders[side[2]] = {"pt": round(int(ln.get("w", "12700")) / 12700, 2),
                                                "color": solid_color(ln.find("a:solidFill", NS), theme)}
                if borders:
                    cell["borders"] = borders
            paras, body = text_of(tc.find("a:txBody", NS), theme, DEFAULT_TEXT_PT, None)
            cell["paras"] = paras
            cells.append(cell)
        rows.append(cells)
    return {"colw": colw, "rowh": rowh, "rows": rows}


CHART_TYPE_MAP = {
    "barChart": "bar", "bar3DChart": "bar", "lineChart": "line", "pieChart": "pie", "pie3DChart": "pie",
    "doughnutChart": "doughnut", "areaChart": "area", "scatterChart": "scatter", "radarChart": "radar",
}


def chart_of(gf, part):
    """차트 유형, 범주, 계열값. python-pptx chart 객체로 읽는다"""
    try:
        chart = part.chart
    except Exception:
        return None
    d = {"type": None, "categories": [], "series": [], "barDir": None, "grouping": None}
    cns = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
    nf = chart._chartSpace.find(".//" + cns + "dLbls/" + cns + "numFmt")
    if nf is None:
        nf = chart._chartSpace.find(".//" + cns + "valAx/" + cns + "numFmt")
    if nf is not None and nf.get("formatCode") and nf.get("formatCode") != "General":
        d["numFmt"] = nf.get("formatCode")
    cs = chart._chartSpace
    plot = cs.find(".//{%s}plotArea" % "http://schemas.openxmlformats.org/drawingml/2006/chart")
    for child in plot:
        tag = child.tag.split("}")[1]
        if tag in CHART_TYPE_MAP:
            d["type"] = CHART_TYPE_MAP[tag]
            bd = child.find("{http://schemas.openxmlformats.org/drawingml/2006/chart}barDir")
            if bd is not None:
                d["barDir"] = bd.get("val")
            gp = child.find("{http://schemas.openxmlformats.org/drawingml/2006/chart}grouping")
            if gp is not None:
                d["grouping"] = gp.get("val")
            hs = child.find("{http://schemas.openxmlformats.org/drawingml/2006/chart}holeSize")
            if hs is not None:
                d["holeSize"] = int(hs.get("val"))
            break
    try:
        for plot_obj in chart.plots:
            cats = list(plot_obj.categories)
            d["categories"] = [str(c) for c in cats]
            for i, s in enumerate(plot_obj.series):
                name = s.name
                if not name:
                    v = s._element.find(".//{http://schemas.openxmlformats.org/drawingml/2006/chart}tx//{http://schemas.openxmlformats.org/drawingml/2006/chart}v")
                    name = v.text if v is not None else "계열%d" % (i + 1)
                d["series"].append({"name": name, "values": [v for v in s.values]})
            break
    except Exception as e:
        d["error"] = str(e)
    d["hasTitle"] = chart.has_title
    if chart.has_title:
        try:
            d["title"] = chart.chart_title.text_frame.text
        except Exception:
            pass
    d["hasLegend"] = chart.has_legend
    return d


def walk_shapes(container_el, slide, theme, transform, out, slide_no, depth=0):
    """container_el: p:spTree 또는 p:grpSp. transform: (ox, oy, sx, sy) 로 자식 좌표 → 슬라이드 절대 EMU"""
    ox, oy, sx, sy = transform
    for sp in container_el:
        tag = sp.tag.split("}")[1]
        if tag not in ("sp", "grpSp", "graphicFrame", "pic", "cxnSp"):
            continue
        xf = xfrm_of(sp) if tag != "graphicFrame" else None
        if tag == "graphicFrame":
            x = sp.find("p:xfrm", NS)
            off = x.find("a:off", NS); ext = x.find("a:ext", NS)
            xf = {"x": int(off.get("x")), "y": int(off.get("y")), "w": int(ext.get("cx")), "h": int(ext.get("cy")), "rot": 0, "flipH": False, "flipV": False}
        if xf is None:
            # 자리표시자는 xfrm 이 없을 수 있음 → 레이아웃 좌표 사용
            xf = None
        name = sp.find(".//p:cNvPr", NS).get("name")
        if tag == "grpSp":
            g = xf
            ax = ox + g["x"] * sx
            ay = oy + g["y"] * sy
            csx = sx * (g["w"] / g["chExt"][0]) if g.get("chExt") and g["chExt"][0] else sx
            csy = sy * (g["h"] / g["chExt"][1]) if g.get("chExt") and g["chExt"][1] else sy
            cox = ax - (g["chOff"][0] * csx if g.get("chOff") else 0)
            coy = ay - (g["chOff"][1] * csy if g.get("chOff") else 0)
            start = len(out)
            walk_shapes(sp, slide, theme, (cox, coy, csx, csy), out, slide_no, depth + 1)
            grot = g.get("rot") or 0
            if grot:
                # 그룹 회전: 자식 중심을 그룹 중심 기준으로 회전시키고 자식 회전각에 합산 (자식 상자 크기는 유지)
                import math
                gcx, gcy = emu(ax + g["w"] * sx / 2), emu(ay + g["h"] * sy / 2)
                rad = math.radians(grot)
                for a in out[start:]:
                    if "x" not in a:
                        continue
                    cx, cy = a["x"] + a["w"] / 2, a["y"] + a["h"] / 2
                    dx, dy = cx - gcx, cy - gcy
                    ncx = gcx + dx * math.cos(rad) - dy * math.sin(rad)
                    ncy = gcy + dx * math.sin(rad) + dy * math.cos(rad)
                    a["x"], a["y"] = round(ncx - a["w"] / 2, 3), round(ncy - a["h"] / 2, 3)
                    a["rot"] = ((a.get("rot") or 0) + grot) % 360
                    if not a["rot"]:
                        del a["rot"]
            continue
        atom = {"name": name}
        if xf is not None:
            atom.update({"x": emu(ox + xf["x"] * sx), "y": emu(oy + xf["y"] * sy), "w": emu(xf["w"] * sx), "h": emu(xf["h"] * sy)})
            if xf["rot"]:
                atom["rot"] = xf["rot"]
            if xf["flipH"]:
                atom["flipH"] = True
            if xf["flipV"]:
                atom["flipV"] = True
        if tag == "pic":
            atom["kind"] = "image"
            atom["identity"] = slide_no in IDENTITY_PIC_SLIDES
            out.append(atom)
            continue
        if tag == "graphicFrame":
            tb = table_of(sp, theme)
            if tb is not None:
                atom["kind"] = "table"
                atom["table"] = tb
                out.append(atom)
                continue
            gd = sp.find(".//a:graphicData", NS)
            if gd is not None and gd.get("uri", "").endswith("/chart"):
                ch = gd.find("{http://schemas.openxmlformats.org/drawingml/2006/chart}chart")
                rid = ch.get("{%s}id" % NS["r"])
                part = slide.part.related_part(rid)
                atom["kind"] = "chart"
                atom["chart"] = chart_of(sp, part)
                out.append(atom)
                continue
            atom["kind"] = "graphic"
            out.append(atom)
            continue
        # sp / cxnSp
        sppr = sp.find("p:spPr", NS)
        st = style_ref(sp, theme)
        nvpr = sp.find(".//p:nvPr", NS)
        ph = nvpr.find("p:ph", NS) if nvpr is not None else None
        is_placeholder = ph is not None
        default_sz = DEFAULT_TEXT_PT
        font_default = None
        if is_placeholder:
            idx = int(ph.get("idx", "0"))
            role = PLACEHOLDER_ROLE.get(idx)
            # 좌표 없는 자리표시자는 레이아웃 좌표 적용
            if xf is None:
                for lp in slide.slide_layout.placeholders:
                    if lp.placeholder_format.idx == idx:
                        atom.update({"x": emu(lp.left), "y": emu(lp.top), "w": emu(lp.width), "h": emu(lp.height)})
            psz = None
            for shp in slide.shapes:
                if shp._element is sp:
                    psz = placeholder_size(shp, slide)
            default_sz = psz or default_sz
            paras, body = text_of(sp.find("p:txBody", NS), theme, default_sz, font_default)
            atom["kind"] = "band"
            atom["role"] = role or ("ph%d" % idx)
            atom["paras"] = paras
            atom.update(body)
            out.append(atom)
            continue
        preset = preset_of(sp)
        atom["preset"] = preset
        gd = sp.find(".//a:prstGeom/a:avLst/a:gd[@name='adj']", NS)
        if gd is not None and gd.get("fmla", "").startswith("val "):
            atom["adj"] = int(gd.get("fmla").split()[1])
        fill = fill_of(sppr, theme)
        if fill is None and "fill" in st:
            fill = st["fill"]
        atom["fill"] = fill
        al = alpha_of(sppr)
        if al is not None and al < 100:
            atom["alpha"] = al
        ln = line_of(sppr, theme)
        if ln is None and "line" in st:
            ln = {"color": st["line"], "pt": None}
        elif ln is not None and ln.get("color") is None and "line" in st:
            ln["color"] = st["line"]
        atom["line"] = ln
        if "font" in st and st["font"]:
            font_default = st["font"]
        paras, body = text_of(sp.find("p:txBody", NS), theme, default_sz, font_default)
        atom["paras"] = paras
        atom.update(body)
        if tag == "cxnSp" or preset in ("line", "straightConnector1", "bentConnector2", "bentConnector3"):
            atom["kind"] = "line"
        else:
            atom["kind"] = "shape"
        if paras and any(IDENTITY_TEXT.search(r["t"]) for p in paras for r in p["runs"]):
            atom["identity"] = True
        out.append(atom)


def extract(pptx_path):
    prs = Presentation(pptx_path)
    theme = theme_colors(prs)
    slides = []
    for i, slide in enumerate(prs.slides, start=1):
        atoms = []
        walk_shapes(slide.shapes._spTree, slide, theme, (0, 0, 1, 1), atoms, i)
        bands = {a["role"]: a for a in atoms if a["kind"] == "band"}
        body = [a for a in atoms if a["kind"] != "band" and a.get("name") not in DROP_ATOMS.get(i, set())]
        if i in DROP_TEXTS:
            def _txt(a):
                return "".join(r["t"] for p in (a.get("paras") or []) for r in p["runs"]).strip()
            body = [a for a in body if _txt(a) not in DROP_TEXTS[i]]
        def band_text(role):
            a = bands.get(role)
            if not a or not a.get("paras"):
                return ""
            return "\n".join("".join(r["t"] for r in p["runs"]) for p in a["paras"]).strip()
        if i in IDENTITY_TABLE_SLIDES:
            for a in body:
                if a["kind"] == "table":
                    for row in a["table"]["rows"]:
                        for c in row:
                            for p in (c.get("paras") or []):
                                for r in p["runs"]:
                                    r["t"] = re.sub(r"\d", "0", r["t"])
        # 회사 식별 문구 일반화 (본문, 표 셀, 밴드)
        CUR_SLIDE[0] = i
        for a in body:
            generalize_paras(a.get("paras"))
            if a["kind"] == "table":
                for row in a["table"]["rows"]:
                    for c in row:
                        generalize_paras(c.get("paras"))
        for a in bands.values():
            generalize_paras(a.get("paras"))
        layout_name = slide.slide_layout.name
        mode = (CFG.get("layoutModes") or {}).get(layout_name, "full")
        if mode not in MODES:
            raise SystemExit(f"layoutModes 값 오류 '{mode}' (허용: {', '.join(MODES)})")
        slides.append({
            "n": i,
            "layout": layout_name,
            "mode": mode,
            "band": {r: band_text(r) for r in ("secNo", "secTitle", "tracker", "headline", "marker")},
            "atoms": body,
        })
    # 원본 경로는 기록하지 않음 (사용자 폴더 구조가 산출물에 남지 않게 함)
    return {"source": Path(pptx_path).name, "slideW": emu(prs.slide_width), "slideH": emu(prs.slide_height), "theme": theme,
            "roles": CFG.get("roles", {}), "descriptions": CFG.get("descriptions", {}), "colorMap": CFG.get("colorMap", {}), "slides": slides}


def inspect(pptx_path):
    """설정 파일 작성을 돕는 목록: 레이아웃별 사용 슬라이드와 자리표시자(idx, 종류, 위치)"""
    prs = Presentation(pptx_path)
    use = {}
    for i, slide in enumerate(prs.slides, start=1):
        use.setdefault(slide.slide_layout.name, []).append(i)
    for layout in prs.slide_layouts:
        if layout.name not in use:
            continue
        print(f"## 레이아웃 '{layout.name}' 사용 슬라이드 {use[layout.name]}")
        for ph in layout.placeholders:
            f = ph.placeholder_format
            print(f"  idx={f.idx} type={f.type} name='{ph.name}' x={emu(ph.left)} y={emu(ph.top)} w={emu(ph.width)} h={emu(ph.height)}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        raise SystemExit(__doc__)
    if argv[0] == "--inspect":
        inspect(argv[1])
        sys.exit(0)
    cfg_path = argv[argv.index("--config") + 1] if "--config" in argv else None
    load_config(cfg_path)
    src, dst = argv[0], argv[1]
    data = extract(src)
    leftover = set()
    for sl in data["slides"]:
        blob = json.dumps(sl, ensure_ascii=False)
        for m in re.findall(IDENTITY_CHECK, blob):
            leftover.add((sl["n"], m))
    if leftover:
        print("잔존 식별 문구:", sorted(leftover))
    else:
        print("잔존 식별 문구 없음")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)
    kinds = {}
    for s in data["slides"]:
        for a in s["atoms"]:
            kinds[a["kind"]] = kinds.get(a["kind"], 0) + 1
    print("slides", len(data["slides"]), "atoms", kinds)
