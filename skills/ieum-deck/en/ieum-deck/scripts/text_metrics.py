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


# Breaks inside a word (follows LibreOffice 24.2 editeng ImpBreakLine and i18npool BreakIterator_CJK, BreakIterator_Unicode)
# Besides spaces, the break point is chosen from the first character that passes the line width (m), and the script of the character right before m picks the rule
#   Asian script (ko-KR): a hanging character moves the break one character on and hangs past the margin at the paragraph end. The break is then pulled back
#                         over no-line-start and no-line-end characters. Without a pull-back, a Hangul m breaks at the first character of its Hangul run. Otherwise it breaks at m
#   Latin (en-US): the last position at or before m where a line may break (latin_break_ok). Never right after a slash
# LibreOffice does not read the eaLnBrk="0" that finalize writes (the attribute is commented out in the oox import), so the forbidden character rules always apply
# Why: rendering the two sample decks in A4, 10.83 and 4:3 gives 128 breaks inside words ('60|분', '○|○억원', '가|정)', '3-|5개'). 16:9 gives none.
#      A simulation of these rules (Latin rule taken verbatim from LibreOffice line.txt) reproduces 123 of the 128 at the same position (the other 5 are edge cases at 99.8% of the line width or more).
#      On 490 probe text boxes (115 words with the line end placed at every character position) it matches 484 (the other 6 come from the probe layout and the widths of ₩ and ↑).
#      This calculation matches the simulation in 98,710 of 98,720 line counts (3,448 sample paragraphs at 40 widths each) and places 112 of the 117 rendered breaks inside words narrower than the line at the same position
# Limits: when a word starts with a no-line-start character (a formula symbol such as ' / '), LibreOffice breaks inside the previous word. This calculation breaks between the words.
#         Asian script characters in runs tagged with a language other than ko-KR follow the default East Asian locale of the environment (zh-CN) (finalize tags every run that contains Hangul ko-KR)
# No-line-start characters (LibreOffice ko_KR locale data ForbiddenLineBeginCharacters as is, including the space)
NO_LINE_START = frozenset("!%),.:;?]}¢￠'\"′″℃>〉＞》」』】〕！％），．：；？］｝｡｣､･ ﾞﾟ、。’”°")
# No-line-end characters (ko_KR ForbiddenLineEndCharacters)
NO_LINE_END = frozenset("$(¥£[\\{￡￥'\"<＜《「『【〔＄（［｛₩￦｢‘“〈")
# Hanging characters (ko_KR LineBreakHangingCharacters). finalize writes hangingPunct="1" on every paragraph
HANGING = frozenset("!,.:;?、。！，．：；？")
# Character classes of the Latin rule (the UAX #14 classes used by LibreOffice line.txt that appear in business documents). Characters not listed are AL (letters, ○ ① · and so on)
LB_CLASS = {**dict.fromkeys("([{〈《「『【〔（［｛", "OP"), **dict.fromkeys(")]}", "CP"), **dict.fromkeys("〉》」』】〕）］｝，．：；、。", "CL"),
            **dict.fromkeys("'\"“”‘’", "QU"), **dict.fromkeys(",.:;", "IS"), **dict.fromkeys("!?！？", "EX"), "/": "SY", "-": "HY",
            **dict.fromkeys("|–", "BA"), **dict.fromkeys("%℃°‰′″％", "PO"), **dict.fromkeys("$₩+±£¥＄￦", "PR"), "…": "IN",
            **dict.fromkeys("0123456789", "NU")}


def is_hangul(ch):
    """Hangul range LibreOffice uses to keep Hangul words whole: syllables, jamo, compatibility jamo, extended jamo"""
    c = ord(ch)
    return 0xAC00 <= c <= 0xD7AF or 0x1100 <= c <= 0x11FF or 0xA960 <= c <= 0xA97F or 0xD7B0 <= c <= 0xD7FF or 0x3130 <= c <= 0x318F


def lb_class(ch):
    """Character class of the Latin rule. Hangul is H, Hanja is ID"""
    if is_hangul(ch): return "H"
    if is_hanja(ord(ch)): return "ID"
    return LB_CLASS.get(ch, "AL")


def latin_break_ok(a, b):
    """Whether the Latin rule allows a line break between characters a and b. Summary of the LibreOffice line.txt pair rules
    (never before closing marks and commas, after opening marks and quotes, or between letters and digits. Allowed between a digit and Hangul, after a hyphen and between Hangul syllables)"""
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
    """Break position of the Asian script rule (characters of the word kept on the line). 0 moves the whole word to the next line. The word length means a punctuation mark at the paragraph end hangs past the margin"""
    s = m
    if text[m] in HANGING:
        if para_end and m == len(text) - 1: return len(text)
        s = m + 1
    # The character after the word is a space, and the space is a no-line-start character too (when the comma of '기준, 끝' overflows: '기|준,')
    while s > 0 and (s == len(text) or text[s] in NO_LINE_START or text[s - 1] in NO_LINE_END): s -= 1
    if s == m and is_hangul(text[m]):
        while s > 0 and is_hangul(text[s - 1]): s -= 1
    return s


def latin_break(text, m):
    """Break position of the Latin rule (characters of the word kept on the line). 0 moves the whole word to the next line"""
    s = m - 1 if text[m - 1] == "/" else m
    while s > 0 and not latin_break_ok(text[s - 1], text[s]): s -= 1
    return 0 if s > 0 and text[s - 1] == "/" else s


def word_scripts(word, prev):
    """Script of each character of the word. A weak character takes the script of the character before it (prev is the script of the character before the word. WEAK at the paragraph start, judged Latin)"""
    out, cur = [], prev
    for ch, _ in word:
        cur = script_of(ord(ch)) or cur or LATIN
        out.append(cur)
    return out


def overflow_at(word, scripts, prev, x, cap):
    """Position of the first character that passes the line width (cap) in a word starting at x (em). Adds the gap before a character that changes the script. The word length when no character passes"""
    for i, (_, w) in enumerate(word):
        if (scripts[i - 1] if i else prev) not in (WEAK, scripts[i]): x += GAP_EM
        x += w
        if x > cap: return i
    return len(word)


def break_in_word(word, prev, x, cap, para_end):
    """Position where LibreOffice breaks a word caught at the line end (characters of the word kept on the line), and the script of each character. 0 moves the whole word to the next line"""
    scripts = word_scripts(word, prev)
    m = overflow_at(word, scripts, prev, x, cap)
    if m in (0, len(word)): return 0, scripts
    text = "".join(ch for ch, _ in word)
    return (ko_break(text, m, para_end) if scripts[m - 1] == ASIAN else latin_break(text, m)), scripts




# Why word wrapping: ceil(width ÷ line width) ignores the space left at line ends, so it counts too few lines (the direction that misses overflow)
#     Paragraphs whose line count differs from the render among the 7,337 text box paragraphs above: ceil 122 (all under), word wrapping 41
#     (the 41 are 18 inner text areas of diamonds, chevrons and ellipses and 23 edge cases with text at 99.5% of the line width or more, the same differences as the build estimate)
def wrap_paragraph(runs, width_in):
    """Line count, width (inches) of the last line and breaks inside words [(word, characters kept on the upper line)] of a paragraph at width_in. Same calculation as the build's estimateLines
    Lines break at spaces, and a word caught at the line end is split by the LibreOffice rule (break_in_word). A word wider than the line breaks in the middle (such words are left out of the list)
    The space and the script boundary gap are added only when a word joins the previous word on the same line (a trailing space and gap do not count toward the line width)"""
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
            if cut == len(word):  # A punctuation mark at the paragraph end hangs past the margin, so no line is added
                cur += need
                last = end
                continue
            n += 1
            if cut:
                if em <= cap: splits.append(("".join(ch for ch, _ in word), cut))
                cur = span_em(word[cut:], scripts[cut - 1])[0]  # The script boundary gap at the split stays at the end of the upper line
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
    """Number of lines a paragraph takes at width_in and the width (inches) of its last line (see wrap_paragraph)"""
    n, last_w, _ = wrap_paragraph(runs, width_in)
    return n, last_w
