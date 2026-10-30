#!/usr/bin/env python3
"""check_layout.py: 빌드된 pptx 의 구조 검수 (python-pptx 는 검수에만 사용).
사용: python3 check_layout.py <deck.pptx> [--layout 16:9|A4|10.83|4:3]
검사: 텍스트 넘침 추정(빌드와 같은 나눔고딕 실측 폭과 어절 단위 줄바꿈으로 소요 높이 산정, FAIL), 아이콘과 텍스트 겹침(FAIL), 헤드라인 글꼴 일관성(WARN), 표 열과 나란한 상자의 정렬 혼재(WARN), 가장자리 여백(0.42인치), 밴드 이탈(본문 도형이 헤드라인 밴드 침범), 본문 계열 11pt 미만 텍스트(각주, 출처, 쪽번호 제외. 커스텀 슬라이드 재생 슬라이드는 build.json 의 ownSlides 로, VISION 과 SCOPE 같은 영문 대문자 구조 라벨은 원문 크기로 제외),
      텍스트 상자 상호 겹침(20% 초과 WARN, 30% 초과나 그림이 걸리면 FAIL), 내용 상자 안 라벨과 본문의 줄 단위 글자 겹침(30% 초과 WARN), 표·차트·그림·채움 상자의 상호 겹침(15% 초과, FAIL), 어절 중간 줄바꿈 추정(글 상자와 표 셀 안쪽 폭보다 넓은 어절, WARN. 빌드 기록의 lineBreak 가 char 이면 제외), 본문 상하좌우 여백 과다(내용이 한쪽으로 몰림), 상자 내용 부족(테두리 상자와 테두리 패널 안 글 상자의 채움 비율 45% 미만), 본문 세로 채움 부족(내용 묶음이 본문 높이의 70% 미만), 빈 패널(테두리 상자 안에 텍스트 없음), 강조색 2곳 이상, 다중 줄 텍스트의 불릿 누락
결과: FAIL 과 WARN 목록. 종료 코드 1 이면 FAIL 존재
"""
import json
import math
import re
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).resolve().parent
LIM = json.load(open(HERE / "limits.json", encoding="utf-8")) if (HERE / "limits.json").exists() else {}
EDGE = LIM.get("BAND", {}).get("EDGE_MIN", 0.42)
BODY_MIN = LIM.get("SIZE", {}).get("BODY_MIN", 11)
ACCENT = "C0392B"
LABEL_INK_RATIO = 0.3  # 상자 안 라벨과 본문 글자의 겹침 판정 기준 (작은 쪽 글자 면적 대비)
# 이 크기 이상인 글은 제목으로 보고 불릿 없는 여러 줄 판정에서 제외 (표지 제목 40pt 를 축소 하한 0.6배로 줄여도 24pt, 본문 계열 상한은 목차 항목 20pt)
TITLE_PT = 24
# 표 셀에 허용되는 기본 채움색 (navy 와 mono 테마 색, 틴트, 회색, 흰색). 실행 시 빌드 기록의 palette(적용한 테마 색)를 더함. 그 외 색은 시각 검수 대상
PALETTE = {"1F3864", "17294A", "6B8EC2", "A9B9D9", "D5DDEC", "E9EBF0", "F7F8FA", "F2F2F2", "C9CDD8",
           "FFFFFF", "BFBFBF", "A6A6A6", "595959", "333333", "2B2B2B", "4D4D4D", "808080", "D9D9D9", "C0392B", "8B93A7",
           "EBEBEB", "F8F8F8", "939393"}
FM = json.load(open(HERE.parent / "assets" / "font-metrics.json", encoding="utf-8")) if (HERE.parent / "assets" / "font-metrics.json").exists() else None

def _build_record(pptx_path):
    """빌드 기록(<파일명>.build.json). pptx 와 같은 폴더에 있어야 함. 없으면 빈 기록"""
    f = Path(str(pptx_path)[:-5] + ".build.json") if str(pptx_path).endswith(".pptx") else None
    if not f or not f.exists(): return {}
    try:
        return json.load(open(f, encoding="utf-8"))
    except Exception:
        return {}


def _own_small_boxes(record):
    """커스텀 슬라이드 원문에서 본문 하한보다 작은 글꼴로 조판된 도형의 좌표 집합.

    커스텀 슬라이드 재생은 원본 글꼴 크기를 따르므로 본문 하한 검사에서 제외한다.
    슬롯을 치환해도 좌표는 원본 그대로이므로 좌표로 식별한다. 커스텀 슬라이드 미등록이면 빈 집합.
    """
    f = record.get("ownDeck")
    if not f or not Path(f).exists(): return set()
    out = set()
    for sl in json.load(open(f, encoding="utf-8")).get("slides", []):
        for a in sl.get("atoms", []):
            for para in a.get("paras", []) or []:
                if any((r.get("sz") or 18) < BODY_MIN for r in para.get("runs", []) or []):
                    out.add((round(a.get("x", 0), 2), round(a.get("y", 0), 2), round(a.get("w", 0), 2), round(a.get("h", 0), 2)))
                    break
    return out


NSA = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

# 글 폭 모델: 빌드(atoms.js 의 charEm, scriptOf, spanEm, textEm, estimateLines)와 같은 규칙. 상수는 빌드가 limits.json 에 기록한 tokens.js METRIC
# Why: 검수가 빌드와 다른 폭으로 재면 빌드가 맞춘 상자를 넘침으로 판정함. 이전 근사(한글 1.0em, 미측정 문자 0.55em, 계열 경계 간격 없음)는
#      견본 2종을 4판형(16:9, A4, 10.83, 4:3)으로 렌더한 글 상자 문단 7,337개 중 319개의 줄 수를 렌더와 다르게 셌고,
#      넘침 FAIL 46건 중 43건은 렌더에서 글이 상자를 0.02인치 넘게 벗어나지 않았음.
#      이 모델은 줄 수가 렌더와 다른 문단 41개. 넘침 FAIL 10건 중 7건은 렌더에서 넘치지 않음 (7건 모두 줄 수는 렌더와 같고 차이는 상자 여백과 행간 계산에서 생김)
METRIC = LIM.get("METRIC", {})
# 계열 경계 간격(em)은 나눔고딕 실측 값이므로 실측 폭 파일이 있을 때만 적용 (근사 폭은 SAFETY 계수가 간격을 흡수)
GAP_EM = METRIC.get("SCRIPT_GAP_EM", 0.227) if FM else 0.0
LINE_SAFETY = METRIC.get("SAFETY_LINES", 0.995) if FM else METRIC.get("SAFETY", 0.92)  # 줄 수 추정 여유
# 실측 폭 파일이 없을 때의 근사 폭(em): 한글 계열과 전각 기호, 그 외 글자, 공백
EM_HANGUL, EM_LATIN, EM_SPACE = METRIC.get("EM_HANGUL", 1.0), METRIC.get("EM_LATIN", 0.55), METRIC.get("EM_SPACE", 0.3)
WEAK, LATIN, ASIAN = 0, 1, 2  # 글자 계열


def is_hanja(c):
    """한자 코드 범위: 통합 한자, 확장 A, 호환 한자(한글 입력기가 동자이음 한자를 입력하는 영역)"""
    return 0x4E00 <= c <= 0x9FFF or 0x3400 <= c <= 0x4DBF or 0xF900 <= c <= 0xFAFF


def is_wide_symbol(c):
    """전각 폭 기호: 화살표, 괘선, 도형(○ ● ◐ □ ■), 기타 기호, ※"""
    return 0x2190 <= c <= 0x21FF or 0x2500 <= c <= 0x27BF or c == 0x203B


def is_hangul_jamo(c):
    """한글 호환 자모(ㄱ, ㅏ, ㆍ)"""
    return 0x3130 <= c <= 0x318F


def char_em(ch, bold):
    """글자 폭(em). 실측 키(ASCII와 × ÷ ± · 〉 … “ ” ‘ ’), 한글 음절, CJK 문장부호, 전각 문자, 원문자 범주 순으로 찾음
    한자, 전각 폭 기호, 한글 호환 자모, 로마 숫자(Ⅰ-Ⅹ, ⅰ-ⅹ)는 한글 폭, 그 외는 other. 실측 폭 파일이 없으면 tokens.js 근사 폭"""
    c = ord(ch)
    if FM:
        m = FM["bold" if bold else "regular"]
        if ch in m: return m[ch]
        if 0xAC00 <= c <= 0xD7A3: return m["hangul"]
        if 0x3000 <= c <= 0x303F: return m["cjkpunct"]
        if 0xFF00 <= c <= 0xFFEF: return m["fullwidth"]
        if 0x2460 <= c <= 0x24FF: return m["enclosed"]
        if is_hanja(c) or is_wide_symbol(c) or is_hangul_jamo(c) or 0x2160 <= c <= 0x2179: return m["hangul"]
        return m["other"]
    if ch == " ": return EM_SPACE
    wide = 0xAC00 <= c <= 0xD7A3 or 0x3000 <= c <= 0x303F or 0xFF00 <= c <= 0xFFEF or is_hanja(c) or 0x2460 <= c <= 0x24FF or is_hangul_jamo(c) or is_wide_symbol(c)
    return EM_HANGUL if wide else EM_LATIN


def script_of(c):
    """글자 계열. 공백과 제어 문자는 약한 문자, 라틴-1 까지는 라틴, 한글 음절, 호환 자모, CJK 문장부호, 전각 문자, 한자는 한글 계열, 그 외 기호는 약한 문자"""
    if c <= 0x20 or c == 0xA0: return WEAK
    if c <= 0xFF: return LATIN
    if 0xAC00 <= c <= 0xD7A3 or is_hangul_jamo(c) or 0x3000 <= c <= 0x303F or 0xFF00 <= c <= 0xFFEF or is_hanja(c): return ASIAN
    return WEAK


def glyphs(runs, ref_pt):
    """조각 목록 (글, 크기 pt, 굵게)을 글자별 (글자, 폭 em) 목록으로 펼침. 크기가 다른 조각은 ref_pt 의 em 으로 환산 (같은 크기면 배율 1 이라 빌드 계산과 같은 값)"""
    return [(ch, char_em(ch, bold) * (pt / ref_pt)) for txt, pt, bold in runs for ch in txt]


def span_em(gl, prev=WEAK):
    """글자 목록의 폭(em)과 첫 글자, 끝 글자 계열. prev 는 바로 앞 글자의 계열 (문단 첫머리는 WEAK)
    약한 문자는 앞 글자의 계열을 따르고 문단 첫머리에서는 라틴. 계열이 바뀌는 글자 사이마다 간격을 더함 (앞 글자와 첫 글자 사이 간격은 호출부가 판정)"""
    em, cur, first = 0.0, prev, WEAK
    for ch, w in gl:
        sc = script_of(ord(ch)) or cur or LATIN
        if first and sc != cur: em += GAP_EM
        em += w
        if not first: first = sc
        cur = sc
    return em, first, cur


def text_width_in(txt, pt, bold):
    """한 줄 문구의 폭(인치). 빌드의 textEm × pt / 72 와 같은 값 (문단 첫머리부터 이어지는 문구로 보고 계열 경계 간격 포함)"""
    return span_em(glyphs([(txt, pt, bold)], pt))[0] * pt / 72


def para_runs(p):
    """문단의 조각 목록 (글, 크기 pt, 굵게). 크기 미지정은 18pt"""
    return [(r.text, r.font.size.pt if r.font.size else 18, bool(r.font.bold)) for r in p.runs]


def para_width_in(runs):
    """문단을 한 줄로 이었을 때의 폭(인치). 조각 경계에서도 계열을 이어서 판정 (finalize 가 강조색으로 나눈 '36' 과 '억원' 사이 간격 포함)"""
    ref = max(pt for _, pt, _ in runs)
    return span_em(glyphs(runs, ref))[0] * ref / 72


def words_of(gl):
    """글자 목록을 공백 단위 어절로 나눔. (어절 글자 목록, 앞 공백 폭 em) 목록이며 연속 공백은 빈 어절 (빌드의 split(" ") 과 같음)"""
    out, word, space = [], [], 0.0
    for ch, w in gl:
        if ch == " ":
            out.append((word, space))
            word, space = [], w
        else:
            word.append((ch, w))
    out.append((word, space))
    return out


# Why 어절 단위 줄바꿈: 폭 ÷ 줄 폭 올림은 줄 끝에 남는 빈 공간을 세지 않아 줄 수를 적게 셈 (넘침을 놓치는 방향)
#     위 렌더의 글 상자 문단 7,337개에서 렌더와 줄 수가 다른 문단: 올림 122개(모두 과소), 어절 단위 41개
#     (41개는 마름모, 셰브론, 타원의 안쪽 글 영역 18개와 문구 폭이 줄 폭의 99.5% 이상인 경계 23개로 빌드 추정과 같은 차이)
def wrap_lines(runs, width_in):
    """width_in 폭에서 문단이 차지하는 줄 수와 마지막 줄 폭(인치). 빌드의 estimateLines 와 같은 어절 단위 줄바꿈
    공백에서 줄을 바꾸고 줄 폭보다 넓은 어절은 중간에서 나눔. 앞 어절과 같은 줄에 이을 때만 공백과 계열 경계 간격을 더함 (줄 끝 공백과 간격은 줄 폭에 들지 않음)"""
    ref = max(pt for _, pt, _ in runs)
    cap = width_in * 72 / ref * LINE_SAFETY
    cur, n, last = 0.0, 1, WEAK
    for word, space in words_of(glyphs(runs, ref)):
        em, first, end = span_em(word, last)
        gap = GAP_EM if first and last and first != last else 0
        need = em + (space + gap if cur > 0 else 0)
        if cur > 0 and cur + need > cap:
            n += 1
            cur = em
        else:
            cur += need
        if cur > cap:
            n += math.floor(cur / cap)
            cur = cur % cap
        last = end
    return n, cur * ref / 72


WORD_FIT_TOL = 0.02  # 어절 폭 비교 허용 오차 (인치)


def too_wide_word(paras, inner):
    """안쪽 폭(불릿 문단은 들여쓰기 제외)보다 넓은 첫 어절. (어절, 어절 폭, 안쪽 폭) 또는 None"""
    for p in paras:
        runs = [r for r in p.runs if r.text]
        if not runs: continue
        # 줄바꿈 run 은 어절 경계이므로 run 사이를 공백으로 둠
        txt = " ".join(r.text for r in runs).replace("\n", " ").replace("\x0b", " ")
        pt = max((r.font.size.pt for r in runs if r.font.size), default=12)
        bold = any(r.font.bold for r in runs)
        pxml = p._p.xml
        indent = 0.0
        if "buChar" in pxml or "buAutoNum" in pxml:
            pr = p._p.find(NSA + "pPr")
            indent = int(pr.get("marL")) / 914400 if pr is not None and pr.get("marL") else 0.28
        eff = inner - indent
        for tok in txt.split():
            tw = text_width_in(tok, pt, bold)
            if tw > eff + WORD_FIT_TOL: return tok, tw, eff
    return None


def overflow_estimate(sh):
    """텍스트 상자의 추정 소요 높이와 상자 높이 비교. (need_in, avail_in, wrap) 반환"""
    tf = sh.text_frame
    bp = tf._txBody.find(NSA + "bodyPr")
    ins = lambda k, d: int(bp.get(k)) / 914400 if bp is not None and bp.get(k) else d
    l, r, t, b = ins("lIns", 0.1), ins("rIns", 0.1), ins("tIns", 0.05), ins("bIns", 0.05)
    wrap = bp is None or bp.get("wrap") != "none"
    w, h = sh.width / 914400, sh.height / 914400
    inner_w = max(0.1, w - l - r)
    need = 0.0
    for p in tf.paragraphs:
        runs = para_runs(p)
        if not runs:
            continue
        pt = max(x[1] for x in runs)
        # 불릿 문단은 들여쓰기만큼 폭이 줄어드는 점을 반영
        pxml = p._p.xml
        indent = 0.0
        if "buChar" in pxml or "buAutoNum" in pxml:
            pr = p._p.find(NSA + "pPr")
            indent = int(pr.get("marL")) / 914400 if pr is not None and pr.get("marL") else 0.28
        eff_w = max(0.1, inner_w - indent)
        lines = wrap_lines(runs, eff_w)[0] if wrap else 1
        spc = p._p.find(NSA + "pPr/" + NSA + "spcBef/" + NSA + "spcPts")
        need += lines * pt * 1.2 / 72 + (int(spc.get("val")) / 100 / 72 if spc is not None else 0)
    # 줄바꿈 없는 짧은 라벨은 PowerPoint 가 상자 여백을 무시하고 가운데 정렬로 표시하므로 여백을 제외하지 않은 높이로 비교
    lines_total = 0
    for p in tf.paragraphs:
        runs = para_runs(p)
        if not runs:
            continue
        lines_total += wrap_lines(runs, inner_w)[0] if wrap else 1
    paras_n = sum(1 for p in tf.paragraphs if p.runs)
    if lines_total <= paras_n:
        return need, h, wrap
    return need, h - t - b, wrap
RULE_TOP_Y = 1.05  # 헤드라인 밴드 상단 선 (16:9 기준, 판형 높이 비율로 환산)
RULE_Y = 1.8  # 헤드라인 밴드 하단 선
NOTE_Y = 6.78
CONTENT_Y = LIM.get("BAND", {}).get("CONTENT_Y", 2.32)  # 마커 밴드가 있는 레이아웃의 본문 기준선
CONTENT_Y_NO_MARKER = 2.07  # 마커 밴드가 없는 레이아웃의 본문 기준선
BODY_PAD = LIM.get("BAND", {}).get("BODY_PAD", 0.1)  # 기준선에서 본문 묶음 상단까지 간격
CONTENT_BOTTOM = LIM.get("BAND", {}).get("CONTENT_BOTTOM", 6.92)  # 출처 행이 없을 때 본문이 닿을 수 있는 하단


def inch(v):
    return v / 914400


def main():
    args = sys.argv[1:]
    if not args: raise SystemExit(__doc__)
    prs = Presentation(args[0])
    record = _build_record(args[0])
    own_slides = set(record.get("ownSlides") or [])
    OWN_SMALL = _own_small_boxes(record)
    # 빌드 기록의 테마 색(사용자 지정 테마 포함)을 표 셀 허용 색에 더함
    palette = PALETTE | {str(c).upper() for c in record.get("palette") or []}
    # 글자 단위 줄바꿈(meta.lineBreak=char)은 사용자가 단어 중간 줄바꿈을 허용한 덱이므로 어절 중간 줄바꿈 추정을 생략
    word_break = record.get("lineBreak", "word") != "char"
    W, H = inch(prs.slide_width), inch(prs.slide_height)
    sy = H / 7.5
    sx = W / 13.333  # 16:9 기준 대비 가로 배율
    fails, warns, headline_pts = [], [], []
    for n, slide in enumerate(prs.slides, start=1):
        rects, texts, icons, ink, ink_lines = [], [], [], [], []
        accent = 0
        for sh in slide.shapes:
            if sh.left is None: continue
            x, y, w, h = inch(sh.left), inch(sh.top), inch(sh.width), inch(sh.height)
            r = (x, y, x + w, y + h)
            is_band = y < RULE_Y * sy + 0.35 or y > NOTE_Y * sy - 0.05
            if x < EDGE - 0.02 or r[2] > W - EDGE + 0.02 or y < 0.2 or r[3] > H - 0.2:
                if not is_band: fails.append(f"[{n}] 가장자리 여백 침범 {sh.name} ({x:.2f},{y:.2f},{w:.2f},{h:.2f})")
            if sh.has_text_frame and sh.text_frame.text.strip():
                tf = sh.text_frame
                over = 0.0
                if FM and not is_band:
                    need, avail, wrap = overflow_estimate(sh)
                    if need > avail + max(0.15, avail * 0.12):  # 상자 높이의 12% 는 렌더러 행간 차이 허용
                        fails.append(f"[{n}] 텍스트 넘침 추정 {need:.2f}in > 상자 {avail:.2f}in '{tf.text[:15]}'")
                    over = max(0.0, need - avail)
                paras = [p for p in tf.paragraphs if p.text.strip()]
                small_done = False
                for p in tf.paragraphs:
                    prev_accent = False  # 같은 문단에서 이어진 강조색 조각은 1곳 (finalize 재저장이 "36억원" 을 "36" 과 "억원" 으로 나눔)
                    for run in p.runs:
                        sz = run.font.size.pt if run.font.size else None
                        # 구조 라벨(VISION, SCOPE 등 영문 대문자 단독)은 커스텀 슬라이드 원문 크기를 따르므로 제외
                        txt_all = tf.text.strip()
                        struct_label = bool(re.fullmatch(r"[A-Z][A-Z0-9&/. -]{1,13}", txt_all))
                        # ※ 로 시작하면 주석 표기가 이미 붙어 있으므로 용도 확인 대상이 아님
                        note_marked = txt_all.startswith("※") or bool(re.match(r"^\d+\)\s", txt_all))  # 각주 번호 1) 2) 포함
                        own_origin = n in own_slides or struct_label or note_marked or (round(x / sx, 2), round(y / sy, 2), round(w / sx, 2), round(h / sy, 2)) in OWN_SMALL
                        if sz and sz < BODY_MIN and not is_band and y < NOTE_Y * sy - 0.05 and not small_done and not own_origin:
                            small_done = True
                            # 본문보다 작은 글씨는 주석으로 읽히므로 ※ 표기를 확인
                            warns.append(f"[{n}] {sz}pt 텍스트 (본문 하한 {BODY_MIN}) '{run.text[:15]}' → 시각 검수에서 용도 확인")
                        col = run.font.color
                        try:
                            is_accent = bool(col and col.type is not None and str(col.rgb) == ACCENT)
                        except Exception:
                            is_accent = False
                        if is_accent and not prev_accent: accent += 1
                        if is_accent or run.text.strip(): prev_accent = is_accent  # 공백만 있는 조각은 이어짐을 끊지 않음
                if len(paras) > 1 and not is_band:
                    bulleted = any(p._p.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}buChar") is not None or p._p.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}buAutoNum") is not None for p in paras)
                    # 모든 줄이 가운데 정렬이면 목록이 아닌 라벨(역할과 이름, 제목과 부제)로 보고 제외
                    label_like = len(paras) <= 3 and all(p.alignment is not None and int(p.alignment) == 2 for p in paras)
                    # 각주(1), 2))와 ※ 주석은 번호나 기호가 불릿 역할을 하므로 제외
                    note_like = all(re.match(r"^\s*(\d+\)|※)", p.text or "") for p in paras if (p.text or "").strip())
                    # 표지 2줄 제목처럼 제목 크기 글은 목록이 아님
                    title_like = all(r.font.size is not None and r.font.size.pt >= TITLE_PT for p in paras for r in p.runs if r.text.strip())
                    # 모든 줄이 번호(1., 1-1.)로 시작하면 번호가 불릿을 대신하는 목록 (grid 칸 numbered)
                    enum_like = all(re.match(r"^\s*\d{1,2}(-\d{1,2})*[.)]\s", p.text or "") for p in paras)
                    if not bulleted and w > 2.5 and not label_like and not note_like and not title_like and not enum_like: warns.append(f"[{n}] 다중 줄 텍스트 불릿 없음 '{paras[0].text[:15]}'")
                # 넘친 높이만큼 상자를 늘려 인접 요소와의 겹침을 검사
                if not is_band:
                    texts.append(((r[0], r[1], r[2], r[3] + over), sh.name, tf.text[:15]))
                    # 실제 글자가 차지하는 영역 (아이콘 겹침 판정용)
                    ink_w = 0.0
                    for p in tf.paragraphs:
                        runs = para_runs(p)
                        if runs: ink_w = max(ink_w, para_width_in(runs))
                    # 정렬에 따라 글자가 놓이는 좌우 위치를 반영
                    # 상자 좌우 여백은 글자가 놓이지 않는 구간이므로 제외 (번호 배지 자리를 여백으로 확보한 장표 대응)
                    bp = tf._txBody.find(NSA + "bodyPr")
                    ins = lambda k, d: int(bp.get(k)) / 914400 if bp is not None and bp.get(k) else d
                    lIns, rIns = ins("lIns", 0.1), ins("rIns", 0.1)
                    inner_x, inner_w = x + lIns, max(0.05, w - lIns - rIns)
                    iw = min(inner_w, ink_w + 0.1)
                    al = {str(p.alignment) for p in tf.paragraphs if p.runs and p.alignment is not None}
                    if al == {"RIGHT (3)"}: ix0 = inner_x + inner_w - iw
                    elif al == {"CENTER (2)"}: ix0 = inner_x + (inner_w - iw) / 2
                    else: ix0 = inner_x
                    # 글자가 놓이는 세로 범위도 소요 높이와 세로 정렬로 한정 (상자 위아래 빈 공간 제외)
                    anchor = bp.get("anchor") if bp is not None else None
                    ih = min(h + over, (need if FM and not is_band else h) + 0.08)
                    if anchor == "b": iy0 = y + h + over - ih
                    elif anchor == "t": iy0 = y
                    else: iy0 = y + (h + over - ih) / 2
                    ink.append(((ix0, iy0, ix0 + iw, iy0 + ih), sh.name, tf.text[:15]))
                    # 줄 단위 글자 영역 (여러 줄 상자에서 긴 줄 때문에 생기는 오판을 막기 위해 줄마다 사각형을 따로 잡음)
                    lines_box, cur = [], iy0
                    for p in tf.paragraphs:
                        runs = para_runs(p)
                        if not runs: continue
                        pt = max(v[1] for v in runs)
                        lh = pt * 1.2 / 72
                        spc = p._p.find(NSA + "pPr/" + NSA + "spcBef/" + NSA + "spcPts")
                        cur += int(spc.get("val")) / 100 / 72 if spc is not None else 0
                        nline, last_w = wrap_lines(runs, inner_w)
                        pal = str(p.alignment) if p.alignment is not None else None
                        for k in range(nline):
                            # 마지막 줄 앞의 줄은 줄 폭을 채움
                            lw = max(0.05, min(inner_w, (inner_w if k < nline - 1 else last_w) + 0.1))
                            if pal == "RIGHT (3)": lx = inner_x + inner_w - lw
                            elif pal == "CENTER (2)": lx = inner_x + (inner_w - lw) / 2
                            else: lx = inner_x
                            lines_box.append((lx, cur, lx + lw, cur + lh))
                            cur += lh
                    ink_lines.append((lines_box or [(ix0, iy0, ix0 + iw, iy0 + ih)], sh.name, tf.text[:15]))
            elif sh.shape_type is not None and str(sh.shape_type).startswith("PICTURE") and not is_band:
                texts.append((r, sh.name, "[그림]"))
            elif sh.shape_type is not None and not is_band and 0.25 <= w <= 1.3 and 0.25 <= h <= 1.3 and 0.5 <= w / max(h, 0.01) <= 2.0 and has_fill(sh) and not is_white(sh):
                icons.append((r, sh.name))  # 아이콘 도형 (채움 있는 정사각형에 가까운 작은 도형. 연결선과 마커는 제외)
            elif sh.shape_type is not None and not is_band and w > 0.6 and h > 0.4:
                # 차트와 표는 자체 내용을 가지므로 빈 패널 판정 대상에서 제외
                if not (getattr(sh, "has_chart", False) or getattr(sh, "has_table", False)):
                    rects.append((r, sh.name))
        if accent > 1: fails.append(f"[{n}] 강조색 {accent}곳 (상한 1)")
        # 텍스트 상자 겹침
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i][0], texts[j][0]
                ix, iy = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
                inter = ix * iy
                small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                if small > 0 and inter / small > 0.2 and not contains(a, b) and not contains(b, a):
                    ratio = inter / small
                    pic = "[그림]" in (texts[i][2], texts[j][2])
                    # 실제 글자 영역끼리 겹치는지 확인 (상자만 겹치고 글자는 떨어진 경우를 제외)
                    ia = next((x[0] for x in ink if x[1] == texts[i][1] and x[2] == texts[i][2]), None)
                    ib = next((x[0] for x in ink if x[1] == texts[j][1] and x[2] == texts[j][2]), None)
                    hard = False
                    if ia and ib:
                        jx = max(0, min(ia[2], ib[2]) - max(ia[0], ib[0]))
                        jy = max(0, min(ia[3], ib[3]) - max(ia[1], ib[1]))
                        sm = min((ia[2] - ia[0]) * (ia[3] - ia[1]), (ib[2] - ib[0]) * (ib[3] - ib[1]))
                        hard = sm > 0 and jx * jy / sm > 0.3
                    msg = f"[{n}] {'그림과 텍스트' if pic else '텍스트'} 겹침 {texts[i][2]} / {texts[j][2]} ({ratio:.0%})"
                    (fails if pic or hard else warns).append(msg)
        # 라벨 상자가 내용 상자 안에 놓인 경우는 상자 겹침이 정상이므로 글자 영역으로만 판정
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i][0], texts[j][0]
                if not (contains(a, b) or contains(b, a)): continue
                la = next((x[0] for x in ink_lines if x[1] == texts[i][1] and x[2] == texts[i][2]), None)
                lb = next((x[0] for x in ink_lines if x[1] == texts[j][1] and x[2] == texts[j][2]), None)
                if not la or not lb: continue
                worst = 0.0
                for ia in la:
                    for ib in lb:
                        jx = max(0, min(ia[2], ib[2]) - max(ia[0], ib[0]))
                        jy = max(0, min(ia[3], ib[3]) - max(ia[1], ib[1]))
                        sm = min((ia[2] - ia[0]) * (ia[3] - ia[1]), (ib[2] - ib[0]) * (ib[3] - ib[1]))
                        if sm > 0: worst = max(worst, jx * jy / sm)
                if worst > LABEL_INK_RATIO:
                    warns.append(f"[{n}] 상자 안 글자 겹침 {texts[i][2]} / {texts[j][2]} ({worst:.0%})")
        # 표, 차트, 그림, 패널 상자의 상호 겹침 (텍스트 상자 검사가 놓치는 조합)
        boxes = []
        for sh in slide.shapes:
            if sh.top is None or sh.width is None: continue
            x, y = sh.left / 914400, sh.top / 914400
            w, h = sh.width / 914400, sh.height / 914400
            if w < 0.3 or h < 0.2 or y < RULE_Y * sy + 0.35 or y > NOTE_Y * sy - 0.05: continue
            if sh.has_table: boxes.append(((x, y, x + w, y + h), "표"))
            elif sh.has_chart: boxes.append(((x, y, x + w, y + h), "차트"))
            elif sh.shape_type is not None and str(sh.shape_type).startswith("PICTURE"): boxes.append(((x, y, x + w, y + h), "그림"))
            elif sh.has_text_frame and sh.text_frame.text.strip() and has_fill(sh) and not is_white(sh) and not is_pointed(sh):
                boxes.append(((x, y, x + w, y + h), f"상자 '{sh.text_frame.text.strip()[:10]}'"))
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i][0], boxes[j][0]
                ix, iy = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
                inter = ix * iy
                small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                # 표와 차트와 그림은 15%, 채움 상자끼리는 25% 초과부터 결함 (원본 장표의 맞물린 상자 허용)
                both_box = boxes[i][1].startswith("상자") and boxes[j][1].startswith("상자")
                lim = 0.25 if both_box else 0.15
                if small > 0 and inter / small > lim and not contains(a, b) and not contains(b, a):
                    fails.append(f"[{n}] 요소 겹침 {boxes[i][1]} / {boxes[j][1]} ({inter / small:.0%})")

        # 어절 중간 줄바꿈 추정: 상자 안쪽 폭보다 넓은 어절은 모든 렌더러에서 중간이 잘림 (글 상자와 표 셀)
        for sh in (slide.shapes if word_break else []):
            if sh.width is None: continue
            y = sh.top / 914400 if sh.top else 0
            if y < RULE_Y * sy + 0.35: continue
            hit = None
            if sh.has_table:
                colw = [c.width / 914400 for c in sh.table.columns]
                for r in sh.table.rows:
                    for j, c in enumerate(r.cells):
                        if c.is_spanned or not c.text.strip(): continue
                        inner = sum(colw[j:j + c.span_width]) - c.margin_left / 914400 - c.margin_right / 914400
                        hit = hit or too_wide_word(c.text_frame.paragraphs, inner)
            elif sh.has_text_frame and sh.text_frame.text.strip():
                bp = sh.text_frame._txBody.find(NSA + "bodyPr")
                if bp is not None and bp.get("wrap") == "none": continue
                if bp is not None and bp.get("vert") not in (None, "horz"): continue  # 세로쓰기(matrix 세로축 라벨 등)는 가로 폭으로 줄바꿈하지 않음
                ins = lambda k: int(bp.get(k)) / 914400 if bp is not None and bp.get(k) else 0.1
                hit = too_wide_word(sh.text_frame.paragraphs, sh.width / 914400 - ins("lIns") - ins("rIns"))
            if hit:
                warns.append(f"[{n}] 어절 중간 줄바꿈 추정 '{hit[0][:14]}' (어절 폭 {hit[1]:.2f}in > 안쪽 폭 {hit[2]:.2f}in)")

        # 테두리 상자 안 내용이 적어 빈 면적이 큰 경우
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip(): continue
            if sh.top is None or sh.height is None: continue
            y, hh = sh.top / 914400, sh.height / 914400
            ww = sh.width / 914400 if sh.width else 0
            if hh < 1.2 or ww < 1.5 or y < RULE_Y * sy + 0.35 or y > NOTE_Y * sy: continue
            if has_fill(sh) and not is_white(sh): continue  # 라벨 셀(채움 상자)은 제외
            # 테두리 없는 글 상자도 테두리 패널 안에 놓였으면 검사 대상 (패널 안이 휑하게 비는 경우)
            inside_panel = any(rr[0] <= x0 and rr[1] <= y and rr[2] >= x0 + ww and rr[3] >= y + hh and (rr[2] - rr[0]) * (rr[3] - rr[1]) > ww * hh
                               for rr, _ in rects) if (x0 := (sh.left / 914400 if sh.left is not None else 0)) is not None else False
            if not has_outline(sh) and not inside_panel: continue
            txt0 = sh.text_frame.text.strip()
            if len(txt0) < 8: continue
            if re.fullmatch(r"(시각자료|이미지|사진|산출물 화면|도식)", txt0): continue  # 자리 상자
            paras = [p for p in sh.text_frame.paragraphs if p.runs and "".join(r.text for r in p.runs).strip()]
            if len(paras) < 2 and hh < 1.5: continue  # 한 줄 라벨 상자(연결 구조 등)는 제외
            need, avail, _ = overflow_estimate(sh)
            if avail > 0 and need / avail < LIM.get("LIMIT", {}).get("boxFillMin", 0.45):
                warns.append(f"[{n}] 상자 내용 부족 {need / avail:.0%} 채움 '{sh.text_frame.text.strip()[:12]}' (항목 보강, 도식 교체, 상자 축소 중 선택)")

        # 본문 하단이 크게 비는 경우 (내용이 위로 몰림). 표지와 목차와 간지는 위쪽 정렬 설계이므로 제외
        has_headline = any(sh.has_text_frame and sh.text_frame.text.strip() and sh.top is not None and sh.width is not None
                           and 0.85 <= sh.top / 914400 <= 1.45 and sh.width / 914400 >= W * 0.6 for sh in slide.shapes)
        # 본문 밴드를 조판 기준과 맞춤 (검사 기준이 실제보다 넓으면 가운데 배치가 쏠림으로 잡힘)
        has_marker = any(sh.has_text_frame and sh.text_frame.text.strip() and sh.top is not None
                         and RULE_Y * sy + 0.05 <= sh.top / 914400 <= RULE_Y * sy + 0.45 for sh in slide.shapes)
        has_note_row = any(sh.has_text_frame and sh.text_frame.text.strip() and sh.top is not None and sh.left is not None
                           and NOTE_Y * sy - 0.06 <= sh.top / 914400 <= NOTE_Y * sy + 0.3
                           and sh.left / 914400 < W * 0.5 for sh in slide.shapes)
        band_top = (CONTENT_Y if has_marker else CONTENT_Y_NO_MARKER) * sy + BODY_PAD * sy
        band_bottom = (NOTE_Y - 0.12 if has_note_row else CONTENT_BOTTOM) * sy - 0.05
        band_left, band_right = EDGE, W - EDGE
        top_c, bot_c, left_c, right_c = band_bottom, band_top, band_right, band_left
        has_body = False
        for sh in slide.shapes:
            if sh.top is None or sh.height is None or sh.left is None or sh.width is None: continue
            y, hh = sh.top / 914400, sh.height / 914400
            x, ww = sh.left / 914400, sh.width / 914400
            if y + hh < band_top + 0.08 or y > band_bottom: continue  # 마커 밴드와 구분선은 제외
            if sh.has_text_frame and not sh.text_frame.text.strip() and not sh.has_table and not sh.has_chart: continue
            has_body = True
            top_c = min(top_c, max(y, band_top)); bot_c = max(bot_c, min(y + hh, band_bottom))
            left_c = min(left_c, max(x, band_left)); right_c = max(right_c, min(x + ww, band_right))
        band_h, band_w = band_bottom - band_top, band_right - band_left
        lim = LIM.get("LIMIT", {}).get("bandBottomGapMax", 0.3)
        if has_headline and has_body and band_h > 1.0:
            # 한쪽 여백만 크고 반대쪽이 작을 때만 쏠림으로 판정 (가운데 배치는 제외)
            pairs = ((("하단", (band_bottom - bot_c) / band_h), ("상단", (top_c - band_top) / band_h)),
                     (("우측", (band_right - right_c) / band_w), ("좌측", (left_c - band_left) / band_w)))
            for (n1, g1), (n2, g2) in pairs:
                big, small_gap = (n1, g1) if g1 >= g2 else (n2, g2), min(g1, g2)
                if big[1] > lim and small_gap < big[1] * 0.6:
                    warns.append(f"[{n}] 본문 {big[0]} 여백 {big[1]:.0%} (내용이 한쪽으로 몰림)")
            # 상자는 내용 높이에 맞춰 줄어들므로 가운데 배치여도 본문 높이가 크게 남으면 내용 부족
            cover = (bot_c - top_c) / band_h
            if cover < LIM.get("LIMIT", {}).get("bodyCoverMin", 0.7):
                warns.append(f"[{n}] 본문 세로 채움 {cover:.0%} (내용 보강이나 구성 교체)")

        # 헤드라인 글꼴 수집 (덱 전체 일관성 판정용)
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip(): continue
            y = sh.top / 914400 if sh.top else 0
            w = sh.width / 914400 if sh.width else 0
            if 0.85 <= y <= 1.45 and w >= W * 0.6:
                pts = [r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs if r.font.size]
                if pts: headline_pts.append((n, max(pts)))
                break

        # 정렬 일관성: 표는 열 단위, 나란한 상자는 같은 계층 단위로 정렬을 통일
        for sh in slide.shapes:
            if not sh.has_table: continue
            cols_align = {}
            for r_i, row in enumerate(sh.table.rows):
                if r_i == 0: continue  # 머리행은 가운데 정렬이 기본이므로 비교 대상 밖
                for c_i, cell in enumerate(row.cells):
                    if not cell.text.strip(): continue
                    if any(r.font.bold for p in cell.text_frame.paragraphs for r in p.runs): continue  # 머리행과 합계행은 제외
                    al = {p.alignment for p in cell.text_frame.paragraphs if p.alignment is not None}
                    if len(al) == 1: cols_align.setdefault(c_i, set()).add(next(iter(al)))
            odd = [c for c, a in cols_align.items() if len(a) > 1]
            if odd: warns.append(f"[{n}] 표 열 정렬 혼재 (열 {sorted(odd)})")

        rows_by_y = {}
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip() or sh.top is None: continue
            y = round(sh.top / 914400, 1); h = round(sh.height / 914400, 1)
            al = {p.alignment for p in sh.text_frame.paragraphs if p.alignment is not None}
            if len(al) == 1: rows_by_y.setdefault((y, h), []).append(next(iter(al)))
        for (y, h), als in rows_by_y.items():
            if len(als) >= 3 and len(set(als)) > 1 and h > 0.3:
                warns.append(f"[{n}] 나란한 상자 정렬 혼재 (y {y}in, {len(set(als))}종)")

        # 표 하단 이탈과 허용 밖 채움색
        for sh in slide.shapes:
            if not sh.has_table: continue
            top = sh.top / 914400 if sh.top else 0
            bottom = top + (sh.height / 914400 if sh.height else 0)
            if bottom > H - 0.05:
                fails.append(f"[{n}] 표가 슬라이드 밖으로 넘침 (하단 {bottom:.2f}in > 판정 기준 {H - 0.05:.2f}in, 행 {len(sh.table.rows)}개)")
            elif bottom > H - EDGE + 0.05:
                warns.append(f"[{n}] 표가 하단 여백 침범 (하단 {bottom:.2f}in > {H - EDGE:.2f}in)")
            for r in range(len(sh.table.rows)):
                for c in range(len(sh.table.columns)):
                    cell = sh.table.cell(r, c)
                    try:
                        if cell.fill.type != 1: continue
                        rgb = str(cell.fill.fore_color.rgb).upper()
                    except Exception:
                        continue
                    if rgb not in palette:
                        warns.append(f"[{n}] 표 셀 채움색 팔레트 밖 #{rgb} (행 {r + 1}, 열 {c + 1})")
                        break
                else:
                    continue
                break

        # 한 상자 안에서 같은 계층 문단의 글꼴이 다르면 항목 하나만 튀어 보임 (주석 줄은 제외)
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip(): continue
            y = sh.top / 914400 if sh.top else 0
            if y < RULE_Y * sy + 0.3: continue
            lv = {}
            for pa in sh.text_frame.paragraphs:  # 불릿이 붙은 문단만 비교 (제목 줄과 주석은 제외)
                txt = "".join(r.text for r in pa.runs).strip()
                if not txt or re.match(r"^\s*(※|\*|출처|자료|[Ss]ources?\s*[:：]|[Nn]otes?\s*[:：])", txt): continue
                xml = pa._p.xml
                if "buChar" not in xml and "buAutoNum" not in xml: continue
                sz = max((r.font.size.pt for r in pa.runs if r.font.size), default=None)
                if sz: lv.setdefault(pa.level, set()).add(sz)
            odd = [(l, sorted(v)) for l, v in lv.items() if len(v) > 1]
            if odd:
                warns.append(f"[{n}] 상자 안 글꼴 혼재 {odd[0][1]} '{sh.text_frame.text.strip()[:14]}' (같은 계층은 같은 크기로)")

        # 표 분류 열의 빈 셀: 병합 없이 비면 표가 끊겨 보임
        for sh in slide.shapes:
            if not sh.has_table: continue
            tbl = sh.table
            # 분류 열(1열)에서 값이 있는 행 뒤에 빈 행이 이어지면 병합 누락으로 추정
            # 다른 열에 값이 있는데 1열만 비어 있고 병합도 아니면 병합 누락으로 추정
            gap = 0
            for r in range(1, len(tbl.rows)):
                c0 = tbl.cell(r, 0)
                if c0.text.strip() or c0.is_spanned: continue
                # 견본 표처럼 마지막 열만 채워진 행은 제외
                vals = [tbl.cell(r, c).text.strip() for c in range(1, len(tbl.columns))]
                if sum(1 for v in vals if v) >= 2:
                    gap += 1
            if gap >= 2:
                warns.append(f"[{n}] 표 1열 빈 셀 {gap}개 (병합 누락 추정)")

        # 표 세로 정렬 혼재 (가로 정렬 혼재는 아래 열 단위 검사에서 판정)
        for sh in slide.shapes:
            if not sh.has_table: continue
            tbl = sh.table
            valigns = {str(tbl.cell(r, c).vertical_anchor) for r in range(len(tbl.rows)) for c in range(len(tbl.columns))
                       if tbl.cell(r, c).text.strip() and tbl.cell(r, c).vertical_anchor is not None}
            if len(valigns) > 1:
                warns.append(f"[{n}] 표 세로 정렬 혼재 {sorted(valigns)}")

        # 아이콘과 텍스트 겹침: 아이콘 도형이 텍스트 영역을 침범
        for ir, iname in icons:
            for tr, tname, ttext in ink:
                # 도형 위에 얹은 글상자(깔때기 띠의 단계명처럼 도형 안에 완전히 들어가는 글)는 의도한 배치이므로 제외
                if ir[0] - 0.01 <= tr[0] and ir[1] - 0.01 <= tr[1] and tr[2] <= ir[2] + 0.01 and tr[3] <= ir[3] + 0.01: continue
                ix = max(0, min(ir[2], tr[2]) - max(ir[0], tr[0]))
                iy = max(0, min(ir[3], tr[3]) - max(ir[1], tr[1]))
                area = (ir[2] - ir[0]) * (ir[3] - ir[1])
                if area > 0 and ix * iy / area > 0.25:
                    fails.append(f"[{n}] 아이콘과 텍스트 겹침 {iname} / '{ttext}' ({ix * iy / area:.0%})")
                    break

        # 빈 패널: 텍스트 없는 상자 안에 텍스트 상자가 하나도 없음
        for r, name in rects:
            if not any(contains(r, t[0]) or overlaps(r, t[0]) for t in texts):
                warns.append(f"[{n}] 빈 패널 {name} ({r[0]:.2f},{r[1]:.2f})")
    # 헤드라인 글꼴 일관성: 최빈 크기와 다른 슬라이드를 보고 (출력 전에 집계)
    if headline_pts:
        from collections import Counter
        mode_pt = Counter(pt for _, pt in headline_pts).most_common(1)[0][0]
        odd = [(n, pt) for n, pt in headline_pts if abs(pt - mode_pt) > 0.1]
        if odd and len(odd) <= len(headline_pts) / 2:
            warns.append(f"헤드라인 글꼴 불일치: 기준 {mode_pt:g}pt, 다른 슬라이드 {[f'{n}({pt:g}pt)' for n, pt in odd[:8]]} → 커스텀 슬라이드 재생이 아니면 헤드라인 크기를 18pt 로 맞출 것")

    for f in fails: print("FAIL", f)
    for w in warns: print("WARN", w)
    print(f"check_layout: FAIL {len(fails)} WARN {len(warns)} slides {len(prs.slides)}")
    # 경고도 기본은 실패로 처리. 사유를 적어 통과시키려면 --allow-warn "사유" 를 붙임
    allow = sys.argv[sys.argv.index("--allow-warn") + 1] if "--allow-warn" in sys.argv else None
    if fails:
        sys.exit(1)
    if warns and not allow:
        print("check_layout: WARN 이 남아 실패로 처리. 조치하거나 --allow-warn \"유지 사유\" 를 붙여 통과시킬 것")
        sys.exit(1)
    if warns and allow:
        print(f"check_layout: WARN {len(warns)}건 유지 (사유: {allow})")
    sys.exit(0)


def has_outline(sh):
    """테두리가 보이는 상자인지 (선 없음이면 False)"""
    try:
        return sh.line.fill.type not in (5, None) or sh.line.width is not None
    except Exception:
        return False


def has_fill(sh):
    """도형에 채움색이 있으면 True (선만 있는 상자는 제외)"""
    try:
        return sh.fill.type != 5  # 5 = MSO_FILL.BACKGROUND(채움 없음). None 은 테마 기본 채움
    except Exception:
        return False


def is_pointed(sh):
    """셰브론과 홈플레이트는 꼭짓점이 서로 물리도록 설계되므로 겹침 검사에서 제외"""
    try:
        return "CHEVRON" in str(sh.auto_shape_type) or "HOME_PLATE" in str(sh.auto_shape_type) or "PENTAGON" in str(sh.auto_shape_type)
    except Exception:
        return False


def is_white(sh):
    """흰색 채움 도형 (도넛 구멍 덮개 등)은 아이콘 판정에서 제외"""
    try:
        return sh.fill.type == 1 and str(sh.fill.fore_color.rgb) == "FFFFFF"
    except Exception:
        return False


def contains(a, b):
    return a[0] <= b[0] + 0.02 and a[1] <= b[1] + 0.02 and a[2] >= b[2] - 0.02 and a[3] >= b[3] - 0.02


def overlaps(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]) > 0.05 and min(a[3], b[3]) - max(a[1], b[1]) > 0.05


if __name__ == "__main__":
    main()
