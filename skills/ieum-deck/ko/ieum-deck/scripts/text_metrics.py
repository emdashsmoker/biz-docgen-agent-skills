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
