#!/usr/bin/env python3
"""text_metrics.py: 나눔고딕 글 폭과 줄 수 추정 (check_layout.py 와 lint.py 가 공유)
빌드(atoms.js 의 charEm, scriptOf, spanEm, textEm, estimateLines)와 같은 규칙. 상수는 빌드가 limits.json 에 기록한 tokens.js METRIC
Why: 검수 도구마다 폭 계산이 따로 있으면 빌드와 어긋나는 지점이 생김. 한 곳에서 관리하여 빌드 규칙 변경을 함께 반영
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIM = json.load(open(HERE / "limits.json", encoding="utf-8")) if (HERE / "limits.json").exists() else {}
FM_PATH = HERE.parent / "assets" / "font-metrics.json"
FM = json.load(open(FM_PATH, encoding="utf-8")) if FM_PATH.exists() else None  # 나눔고딕 실측 폭 (em). 없으면 tokens.js 근사 폭

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


# 어절 안 줄바꿈 (LibreOffice 24.2 editeng ImpBreakLine 과 i18npool BreakIterator_CJK, BreakIterator_Unicode 를 따름)
# 공백 외에도 줄 폭을 처음 넘는 글자(m)에서 끊을 위치를 정하며, m 바로 앞 글자의 계열로 규칙이 갈림
#   한글 계열(ko-KR): 걸침 문자는 한 글자 뒤로 옮겨 문단 끝이면 줄 밖에 걸치고, 줄 첫머리 금지 문자와 줄 끝 금지 문자를 피해 앞으로 당김.
#                     당기지 않았고 m 이 한글이면 그 한글 묶음의 첫 글자에서 나눔. 그 밖에는 m 에서 나눔
#   라틴(en-US): m 이하에서 줄을 바꿀 수 있는 마지막 글자 사이 (latin_break_ok). 빗금 바로 뒤는 제외
# finalize 가 기록하는 eaLnBrk="0" 은 LibreOffice 가 읽지 않으므로 금지 문자 규칙은 늘 적용됨 (oox 가져오기에서 주석 처리된 속성)
# Why: 견본 2종을 A4, 10.83, 4:3 으로 렌더하면 어절 안 줄바꿈 128건('60|분', '○|○억원', '가|정)', '3-|5개'). 16:9 는 0건.
#      이 규칙의 모의 계산(라틴 규칙은 LibreOffice line.txt 그대로)이 128건 중 123건을 같은 위치에서 재현 (5건은 줄 폭의 99.8% 이상인 경계).
#      확인 문안 490개(어절 115종의 글자 위치마다 줄 끝을 둔 글 상자)에서 484개 일치 (6개는 문안 배치와 ₩ ↑ 글자 폭 문제).
#      이 계산은 모의 계산과 줄 수 98,710/98,720 일치 (견본 문단 3,448개를 40개 폭으로), 렌더 어절 안 줄바꿈 117건(줄 폭보다 좁은 어절) 중 112건을 같은 위치로 추정
# 한계: 어절 첫 글자가 줄 첫머리 금지 문자인 경우(' / ' 같은 수식 기호) LibreOffice 는 앞 어절 안에서 나눔. 이 계산은 어절 사이에서 나눔.
#       ko-KR 이외 언어로 기록된 run 의 한글 계열 글자는 실행 환경 기본 동아시아 로캘(zh-CN) 목록을 따름 (finalize 는 한글이 든 run 을 모두 ko-KR 로 기록)
# 줄 첫머리 금지 문자 (LibreOffice ko_KR 로캘 자료 ForbiddenLineBeginCharacters 그대로이며 공백 포함)
NO_LINE_START = frozenset("!%),.:;?]}¢￠'\"′″℃>〉＞》」』】〕！％），．：；？］｝｡｣､･ ﾞﾟ、。’”°")
# 줄 끝 금지 문자 (ko_KR ForbiddenLineEndCharacters)
NO_LINE_END = frozenset("$(¥£[\\{￡￥'\"<＜《「『【〔＄（［｛₩￦｢‘“〈")
# 걸침 문자 (ko_KR LineBreakHangingCharacters). finalize 가 모든 문단에 hangingPunct="1" 을 기록
HANGING = frozenset("!,.:;?、。！，．：；？")
# 라틴 규칙의 글자 분류 (LibreOffice line.txt 가 쓰는 UAX #14 분류 중 업무 문서에 나오는 것). 목록에 없는 글자는 AL (영문자, ○ ① · 등)
LB_CLASS = {**dict.fromkeys("([{〈《「『【〔（［｛", "OP"), **dict.fromkeys(")]}", "CP"), **dict.fromkeys("〉》」』】〕）］｝，．：；、。", "CL"),
            **dict.fromkeys("'\"“”‘’", "QU"), **dict.fromkeys(",.:;", "IS"), **dict.fromkeys("!?！？", "EX"), "/": "SY", "-": "HY",
            **dict.fromkeys("|–", "BA"), **dict.fromkeys("%℃°‰′″％", "PO"), **dict.fromkeys("$₩+±£¥＄￦", "PR"), "…": "IN",
            **dict.fromkeys("0123456789", "NU")}


def is_hangul(ch):
    """LibreOffice 가 한글 어절 보호에 쓰는 한글 범위: 음절, 자모, 호환 자모, 확장 자모"""
    c = ord(ch)
    return 0xAC00 <= c <= 0xD7AF or 0x1100 <= c <= 0x11FF or 0xA960 <= c <= 0xA97F or 0xD7B0 <= c <= 0xD7FF or 0x3130 <= c <= 0x318F


def lb_class(ch):
    """라틴 규칙의 글자 분류. 한글은 H, 한자는 ID"""
    if is_hangul(ch): return "H"
    if is_hanja(ord(ch)): return "ID"
    return LB_CLASS.get(ch, "AL")


def latin_break_ok(a, b):
    """라틴 규칙에서 글자 a 와 b 사이에서 줄을 바꿀 수 있는지. LibreOffice line.txt 짝 규칙 요약
    (닫는 기호와 쉼표 앞, 여는 기호와 따옴표 뒤, 영문자와 숫자 사이는 불가. 숫자와 한글, 하이픈 뒤, 한글과 한글 사이는 가능)"""
    x, y = lb_class(a), lb_class(b)
    if y in ("CP", "CL", "IS", "EX", "SY", "QU", "HY", "BA") or x in ("OP", "QU"): return False
    if x == "PR": return y not in ("NU", "AL", "H", "ID")
    if y == "PR": return x not in ("AL", "NU")
    if y == "PO": return x not in ("NU", "H", "ID", "IS", "PO", "SY")
    if y == "IN": return x not in ("AL", "NU", "H", "ID", "IN", "EX")
    if x in ("AL", "NU") and y in ("AL", "NU", "OP"): return False
    if x in ("CP", "IS", "PO") and y in ("AL", "NU"): return False
    return True


def ko_break(text, m, para_end):
    """한글 계열 규칙의 나눔 위치 (어절 안 글자 수). 0 이면 어절 전체가 다음 줄, 어절 길이면 문단 끝 문장부호가 줄 밖에 걸침"""
    s = m
    if text[m] in HANGING:
        if para_end and m == len(text) - 1: return len(text)
        s = m + 1
    # 어절 끝 다음 글자는 공백이며 공백도 줄 첫머리 금지 문자 ('기준, 끝' 의 쉼표가 넘치면 '기|준,')
    while s > 0 and (s == len(text) or text[s] in NO_LINE_START or text[s - 1] in NO_LINE_END): s -= 1
    if s == m and is_hangul(text[m]):
        while s > 0 and is_hangul(text[s - 1]): s -= 1
    return s


def latin_break(text, m):
    """라틴 규칙의 나눔 위치 (어절 안 글자 수). 0 이면 어절 전체가 다음 줄"""
    s = m - 1 if text[m - 1] == "/" else m
    while s > 0 and not latin_break_ok(text[s - 1], text[s]): s -= 1
    return 0 if s > 0 and text[s - 1] == "/" else s


def word_scripts(word, prev):
    """어절 글자별 계열. 약한 문자는 앞 글자 계열 (prev 는 어절 앞 글자의 계열, 문단 첫머리는 WEAK 이며 라틴으로 판정)"""
    out, cur = [], prev
    for ch, _ in word:
        cur = script_of(ord(ch)) or cur or LATIN
        out.append(cur)
    return out


def overflow_at(word, scripts, prev, x, cap):
    """x(em)에서 시작하는 어절에서 줄 폭(cap)을 처음 넘는 글자 위치. 계열이 바뀌는 글자 앞에 간격을 더함. 넘는 글자가 없으면 어절 길이"""
    for i, (_, w) in enumerate(word):
        if (scripts[i - 1] if i else prev) not in (WEAK, scripts[i]): x += GAP_EM
        x += w
        if x > cap: return i
    return len(word)


def break_in_word(word, prev, x, cap, para_end):
    """줄 끝에 걸린 어절을 LibreOffice 가 나누는 위치 (어절 안 글자 수)와 글자별 계열. 0 이면 어절 전체가 다음 줄"""
    scripts = word_scripts(word, prev)
    m = overflow_at(word, scripts, prev, x, cap)
    if m in (0, len(word)): return 0, scripts
    text = "".join(ch for ch, _ in word)
    return (ko_break(text, m, para_end) if scripts[m - 1] == ASIAN else latin_break(text, m)), scripts


# Why 어절 단위 줄바꿈: 폭 ÷ 줄 폭 올림은 줄 끝에 남는 빈 공간을 세지 않아 줄 수를 적게 셈 (넘침을 놓치는 방향)
#     위 렌더의 글 상자 문단 7,337개에서 렌더와 줄 수가 다른 문단: 올림 122개(모두 과소), 어절 단위 41개
#     (41개는 마름모, 셰브론, 타원의 안쪽 글 영역 18개와 문구 폭이 줄 폭의 99.5% 이상인 경계 23개로 빌드 추정과 같은 차이)
def wrap_paragraph(runs, width_in):
    """width_in 폭에서 문단이 차지하는 줄 수, 마지막 줄 폭(인치), 어절 안 줄바꿈 목록 [(어절, 윗줄에 남는 글자 수)]. 빌드의 estimateLines 와 같은 계산
    공백에서 줄을 바꾸고 줄 끝에 걸린 어절은 LibreOffice 규칙(break_in_word)으로 나눔. 줄 폭보다 넓은 어절은 중간에서 나눔 (이 어절은 목록에서 제외)
    앞 어절과 같은 줄에 이을 때만 공백과 계열 경계 간격을 더함 (줄 끝 공백과 간격은 줄 폭에 들지 않음)"""
    ref = max(pt for _, pt, _ in runs)
    cap = width_in * 72 / ref * LINE_SAFETY
    cur, n, last, splits = 0.0, 1, WEAK, []
    words = words_of(glyphs(runs, ref))
    for i, (word, space) in enumerate(words):
        em, first, end = span_em(word, last)
        gap = GAP_EM if first and last and first != last else 0
        need = em + (space + gap if cur > 0 else 0)
        if cur > 0 and cur + need > cap:
            cut, scripts = break_in_word(word, last, cur + space, cap, i == len(words) - 1)
            if cut == len(word):  # 문단 끝 문장부호가 줄 밖에 걸쳐 줄이 늘지 않음
                cur += need
                last = end
                continue
            n += 1
            if cut:
                if em <= cap: splits.append(("".join(ch for ch, _ in word), cut))
                cur = span_em(word[cut:], scripts[cut - 1])[0]  # 나눈 자리의 계열 경계 간격은 윗줄 끝에 남음
            else:
                cur = em
        else:
            cur += need
        if cur > cap:
            n += math.floor(cur / cap)
            cur = cur % cap
        last = end
    return n, cur * ref / 72, splits


def wrap_lines(runs, width_in):
    """width_in 폭에서 문단이 차지하는 줄 수와 마지막 줄 폭(인치) (wrap_paragraph 참고)"""
    n, last_w, _ = wrap_paragraph(runs, width_in)
    return n, last_w
