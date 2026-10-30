#!/usr/bin/env python3
"""text_metrics.py: NanumGothic text width and line count estimates (shared by check_layout.py and lint.py)
Same rules as the build (charEm, scriptOf, spanEm, textEm, estimateLines in atoms.js). Constants are tokens.js METRIC as written to limits.json by the build
Why: when each checker keeps its own width calculation, some of them drift from the build. Keeping one copy carries build rule changes to every checker
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIM = json.load(open(HERE / "limits.json", encoding="utf-8")) if (HERE / "limits.json").exists() else {}
FM_PATH = HERE.parent / "assets" / "font-metrics.json"
FM = json.load(open(FM_PATH, encoding="utf-8")) if FM_PATH.exists() else None  # Measured NanumGothic widths (em). Without them, tokens.js approximations

# Text width model: same rules as the build (charEm, scriptOf, spanEm, textEm, estimateLines in atoms.js). Constants are tokens.js METRIC, which the build writes to limits.json
# Why: a check that measures widths differently from the build reports overflow for boxes the build sized correctly. The previous approximation (Hangul 1.0em, unmeasured characters 0.55em, no script boundary gap)
#      counted lines differently from the render for 319 of 7,337 text box paragraphs of the two sample decks rendered in 4 page sizes (16:9, A4, 10.83, 4:3),
#      and in 43 of 46 overflow FAILs the rendered text stayed within 0.02 inch of the box.
#      With this model 41 paragraphs differ, and 7 of the 10 overflow FAILs do not overflow in the render (all 7 match the rendered line count; the gap comes from the box inset and line height calculation)
METRIC = LIM.get("METRIC", {})
# The script boundary gap (em) is a measured NanumGothic value, so it applies only with the measured width file (the SAFETY factor absorbs the gap for approximate widths)
GAP_EM = METRIC.get("SCRIPT_GAP_EM", 0.227) if FM else 0.0
LINE_SAFETY = METRIC.get("SAFETY_LINES", 0.995) if FM else METRIC.get("SAFETY", 0.92)  # Margin for line count estimates
# Approximate widths (em) without the measured width file: Hangul class and full-width symbols, other characters, space
EM_HANGUL, EM_LATIN, EM_SPACE = METRIC.get("EM_HANGUL", 1.0), METRIC.get("EM_LATIN", 0.55), METRIC.get("EM_SPACE", 0.3)
WEAK, LATIN, ASIAN = 0, 1, 2  # Character script classes


def is_hanja(c):
    """Hanja code ranges: unified ideographs, extension A, compatibility ideographs (the range Korean input methods use for homographs)"""
    return 0x4E00 <= c <= 0x9FFF or 0x3400 <= c <= 0x4DBF or 0xF900 <= c <= 0xFAFF


def is_wide_symbol(c):
    """Full-width symbols: arrows, box drawing, shapes (○ ● ◐ □ ■), misc symbols, ※"""
    return 0x2190 <= c <= 0x21FF or 0x2500 <= c <= 0x27BF or c == 0x203B


def is_hangul_jamo(c):
    """Hangul compatibility jamo (ㄱ, ㅏ, ㆍ)"""
    return 0x3130 <= c <= 0x318F


def char_em(ch, bold):
    """Character width (em). Looks up measured keys (ASCII and × ÷ ± · 〉 … “ ” ‘ ’), then the Hangul syllable, CJK punctuation, full-width and enclosed classes
    Hanja, full-width symbols, Hangul compatibility jamo and Roman numerals (Ⅰ-Ⅹ, ⅰ-ⅹ) take the Hangul width, everything else other. Without the measured width file, the tokens.js approximate widths"""
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
    """Character script class. Spaces and control characters are weak, up to Latin-1 is Latin, Hangul syllables, compatibility jamo, CJK punctuation, full-width forms and Hanja are Asian, other symbols are weak"""
    if c <= 0x20 or c == 0xA0: return WEAK
    if c <= 0xFF: return LATIN
    if 0xAC00 <= c <= 0xD7A3 or is_hangul_jamo(c) or 0x3000 <= c <= 0x303F or 0xFF00 <= c <= 0xFFEF or is_hanja(c): return ASIAN
    return WEAK


def glyphs(runs, ref_pt):
    """Expands runs (text, size pt, bold) into per-character (character, width em) pairs. Runs of another size convert to em of ref_pt (the same size gives a factor of 1, so the values equal the build calculation)"""
    return [(ch, char_em(ch, bold) * (pt / ref_pt)) for txt, pt, bold in runs for ch in txt]


def span_em(gl, prev=WEAK):
    """Width (em) of a character list and the scripts of its first and last characters. prev is the script of the character right before it (WEAK at the start of a paragraph)
    A weak character takes the script of the previous character, Latin at the start of a paragraph. A gap is added between characters wherever the script changes (the caller judges the gap between the preceding character and the first character)"""
    em, cur, first = 0.0, prev, WEAK
    for ch, w in gl:
        sc = script_of(ord(ch)) or cur or LATIN
        if first and sc != cur: em += GAP_EM
        em += w
        if not first: first = sc
        cur = sc
    return em, first, cur


def text_width_in(txt, pt, bold):
    """Width (inches) of one-line text. Equals the build's textEm × pt / 72 (text running from the start of a paragraph, including script boundary gaps)"""
    return span_em(glyphs([(txt, pt, bold)], pt))[0] * pt / 72


def para_width_in(runs):
    """Width (inches) of a paragraph set on one line. Scripts carry across run boundaries (includes the gap between '36' and '억원', which finalize splits for the accent color)"""
    ref = max(pt for _, pt, _ in runs)
    return span_em(glyphs(runs, ref))[0] * ref / 72


def words_of(gl):
    """Splits a character list into space-delimited words. List of (word characters, width em of the preceding space); consecutive spaces give empty words (same as the build's split(" "))"""
    out, word, space = [], [], 0.0
    for ch, w in gl:
        if ch == " ":
            out.append((word, space))
            word, space = [], w
        else:
            word.append((ch, w))
    out.append((word, space))
    return out


# Why word wrapping: ceil(width ÷ line width) ignores the space left at line ends, so it counts too few lines (the direction that misses overflow)
#     Paragraphs whose line count differs from the render among the 7,337 text box paragraphs above: ceil 122 (all under), word wrapping 41
#     (the 41 are 18 inner text areas of diamonds, chevrons and ellipses and 23 edge cases with text at 99.5% of the line width or more, the same differences as the build estimate)
def wrap_lines(runs, width_in):
    """Number of lines a paragraph takes at width_in and the width (inches) of its last line. Same word wrapping as the build's estimateLines
    Lines break at spaces and a word wider than the line breaks in the middle. The space and the script boundary gap are added only when a word joins the previous word on the same line (a trailing space and gap do not count toward the line width)"""
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
