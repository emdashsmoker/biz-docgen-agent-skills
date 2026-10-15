#!/usr/bin/env python3
"""lint.py: storyboard.json checks. Zero FAILs is the condition for starting the build.
Usage: python3 lint.py <storyboard.json> [--layout 16:9|A4|10.83|4:3] [--ledger ledger.json] [--report out.json] [--allow-warn "reason for keeping"]
The text checks target Korean deck text, and their word lists and patterns are Korean
Checks
- Schema: unique id, valid template, required fields, custom theme colors (base and color keys of meta.themeColors) as 6-digit color codes (FAIL)
- Deck labels: template or block names, slot names, value types (string, list of the set length, object keys), language tag format and em dashes in meta.labels (FAIL). A format string missing {n} or {t} is a WARN. Defaults and key lists are in assets/labels.json
- Theme color text contrast: a directly set color key below the contrast minimum against the text color on it (white or body text color) (WARN, rules in limits.json THEME_TEXT)
- Company facts: remaining check markers and placeholders (WARN, FAIL with meta.final), missing factSource on fact slides (WARN)
- Character counts: headline 1-line limit 50 (WARN above) and 2-line limit 100 (FAIL above), marker 30, leftover slots {{ }} and [확인]. If the 1-line limit of the page size (--layout or meta.layout, limits.json HEADLINE_LINE_CHARS, the 16:9 limit scaled by the headline width ratio) is below 50, the 1-line limit is that value and the 2-line limit is double it
  Characters are Hangul-equivalent characters: the measured NanumGothic width divided by the width of one Hangul syllable (text written only in Hangul counts as its character count; Latin letters and spaces count less, by their width). The custom slide slot volume comparison uses the same measure
- Style: headline style (meta.headlineStyle: noun | polite), noun-ending body text (no polite endings). Headlines without Hangul (English decks) skip the style check
- Sentence norms: em dash, contrast constructions, number declarations, empty filler, exaggeration, meta narration, internal vocabulary, connectives (FAIL) / discouraged vocabulary (WARN)
  Source strings (source, factSource) quote document titles, so they skip sentence norms other than em dash, discouraged vocabulary, style, RFP wording and institutional wording checks
- RFP wording: appearance of variants from meta.rfp.wording[{standard, variants[]}] is a FAIL
- Score attribution: every non-quantitative item of meta.rfp.evalItems[{id, name, score, quantitative}] attributed (FAIL), share deviation (WARN)
- Scope: if meta.kind is a proposal kind or meta.rfp exists, all proposal checks apply. General planning PPTs skip the RFP and score checks
- No modules: if meta.structure is plan or sections, the module overview and Task checks are skipped and only full RFP item coverage is checked
- Task coverage: meta.rfp.tasks and meta.rfp.moduleTasks exist, every RFP work item is placed in moduleTasks, every Task appears on at least 1 slide, each module has 1 overview slide listing all its Tasks (FAIL). Slide count per module and Task compression ratio (WARN)
- Missing Task numbers: names Task numbers without a slide inside a module (FAIL)
- Module overview: exactly 1 per module (FAIL if none or 2 or more)
- Task bundles: 5 or more Tasks on one slide is a FAIL, 3-4 is a WARN
- Project organization chart (org) and staffing table (staff_card, 투입인력 table): FAIL if only one exists, staff consistency both ways, module box count equal to the designed module count (FAIL)
- Section ledger match: ledger.slides[].id matches the list and order of storyboard slide ids (FAIL). Other fields are not compared
- Institutional wording: terms from a column other than meta.track (rnd | mgmt | general) WARN. Outside R&D, a literal match with a methods sample module name WARNs
- Duplicate numbers and symbols: WARN if section repeats secNo or a bullet slot item starts with a symbol
- Custom slide substitution volume: WARN if substituted text has more lines than the original and exceeds the box height (when meta.ownDeck is registered)
- Background and purpose evidence: WARN if an evidence item has a line break (move evidence to the note slot to get ※)
- Background and purpose volume: WARN over 4 leads or over 12 leads and evidence items combined
- Empty table cells: WARN if a leading category column has 2 or more empty cells without merged
- Duplicate prefixes: WARN for a STEP prefix in steps titles or an M/Module prefix in process module names
- Number notation: WARN without a space after the number ("1.목차" → "1. 목차"), WARN if secNo has no period
- Note notation: WARN if a body item starts with ※, "출처:", "자료:", "Source:", "Note:" or a token added with meta.labels.notation.source (※ on note-type slots and source is added by the build, so they are not checked)
- Module notation: WARN if section titles and contents items use the "Module N." format ([Module N] recommended)
- Subject term: WARN for mixed subject terms, 과업 left after changing the subject term, engagement labels left in non-proposal outputs, and "본 기획"
- Leader titles: WARN if the titles of the overall leader and quality leader are mixed within one deck
- Rhythm: WARN for 4 slides in a row with the same structure, WARN for more than 8 free slides (composite counts as a different structure when its recipe or block layout differs)
- Deck variety: WARN if body template kinds are under 30% of the body slide count, one template exceeds 40%, or one chapter uses a single template
- Bullet skew: WARN if bullet panel templates exceed 50% of the body
- task_multi: FAIL without meta.pageLimit
- Task variety: FAIL if execution plan slides use only one template, WARN if template kinds are under half the slide count
- Page-size-specific text (byLayout): checks slides with the replacement values for the page size (--layout or meta.layout) applied. Page size name or path errors are FAILs
"""
import copy
import json
import os
import re
from collections import Counter
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIMITS = json.load(open(HERE / "limits.json", encoding="utf-8")) if (HERE / "limits.json").exists() else {"LIMIT": {}}
L = LIMITS.get("LIMIT", {})
HL1, HL2 = L.get("headlineOneLine", 60), L.get("headlineTwoLine", 100)
BASE_LAYOUT = "16:9"  # Base page size when none is set
FM_PATH = HERE.parent / "assets" / "font-metrics.json"
FM = json.load(open(FM_PATH, encoding="utf-8")) if FM_PATH.exists() else None  # measured NanumGothic widths (em). Estimated widths are used without it
HANGUL_RE = re.compile(r"[가-힣]")
# Defaults of the fixed template and block labels (the same table as labels.js of build.js). Used to validate the keys of meta.labels
LABEL_DEFAULTS = json.load(open(HERE.parent / "assets" / "labels.json", encoding="utf-8"))
LANG_TAG_RE = re.compile(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*")  # language tag (e.g. en-US, ko-KR)


def char_em(ch, bold):
    """Width of one character (em). Same rules as atoms.js charEm (measured table; Hangul, Hanja and full-width symbols take the Hangul width; the rest take other)"""
    c = ord(ch)
    wide_symbol = 0x2190 <= c <= 0x21FF or 0x2500 <= c <= 0x27BF or c == 0x203B
    hanja = 0x4E00 <= c <= 0x9FFF or 0x3400 <= c <= 0x4DBF or 0xF900 <= c <= 0xFAFF
    if FM:
        m = FM["bold" if bold else "regular"]
        if ch in m: return m[ch]
        if 0xAC00 <= c <= 0xD7A3 or hanja or wide_symbol: return m["hangul"]
        if 0x3000 <= c <= 0x303F: return m["cjkpunct"]
        if 0xFF00 <= c <= 0xFFEF: return m["fullwidth"]
        if 0x2460 <= c <= 0x24FF: return m["enclosed"]
        return m["other"]
    if ch == " ": return 0.3
    wide = 0xAC00 <= c <= 0xD7A3 or 0x3000 <= c <= 0x303F or 0xFF00 <= c <= 0xFFEF or 0x2460 <= c <= 0x24FF or 0x3130 <= c <= 0x318F or hanja or wide_symbol
    return 1.0 if wide else 0.55


def han_len(txt, bold=True):
    """Hangul-equivalent character count: text width divided by the width of one Hangul syllable. Text written only in Hangul equals its character count; Latin letters, digits and spaces count less, by their width
    Applies the character limits to English decks on the same width basis (Latin letters and spaces are narrower than Hangul, so more of them fit in the same width)"""
    unit = FM["bold" if bold else "regular"]["hangul"] if FM else 1.0
    return sum(char_em(ch, bold) for ch in str(txt)) / unit
# Job titles for recognizing staff ("name + title" in free text). Korean spellings and spacing variants of consulting firm and research institute titles
# General corporate titles and degrees are left out (they cause false hits that take the preceding word as a name, like the school name in "서울대 박사")
# Staff cells of the organization chart and name cells of tables read the preceding name regardless of title (lead_name in lint)
STAFF_TITLES_KO = [
    "파트너", "시니어 파트너", "시니어파트너", "매니징 파트너", "매니징파트너", "어소시에이트 파트너", "어소시에이트파트너", "수석파트너",
    "디렉터", "매니징 디렉터", "매니징디렉터", "시니어 디렉터", "시니어디렉터", "어소시에이트 디렉터", "어소시에이트디렉터",
    "시니어 매니저", "시니어매니저", "매니저", "수석매니저", "책임매니저", "선임매니저", "인게이지먼트 매니저", "프로젝트 매니저",
    "수석컨설턴트", "수석 컨설턴트", "책임컨설턴트", "책임 컨설턴트", "선임컨설턴트", "선임 컨설턴트", "주임컨설턴트", "주임 컨설턴트", "전임컨설턴트", "전임 컨설턴트",
    "시니어 컨설턴트", "시니어컨설턴트", "컨설턴트", "어소시에이트", "시니어 어소시에이트", "애널리스트", "비즈니스 애널리스트", "리서치 애널리스트",
    "위원", "수석위원", "수석 위원", "책임위원", "책임 위원", "선임위원", "선임 위원", "주임위원", "주임 위원", "전임위원", "전임 위원",
    "전문위원", "수석전문위원", "책임전문위원", "자문위원",
    "수석연구원", "수석 연구원", "책임연구원", "책임 연구원", "선임연구원", "선임 연구원", "전임연구원", "전임 연구원", "주임연구원", "주임 연구원", "전문연구원", "연구원", "연구위원", "선임연구위원", "부연구위원", "초빙연구위원",
]
STAFF_TITLES_EN = [
    "Partner", "Senior Partner", "Managing Partner", "Associate Partner", "Principal",
    "Director", "Managing Director", "Senior Director", "Executive Director", "Associate Director",
    "Senior Manager", "Manager", "Engagement Manager", "Project Manager",
    "Senior Consultant", "Consultant", "Senior Associate", "Associate", "Analyst", "Business Analyst", "Research Analyst",
    "Senior Researcher", "Researcher", "Research Fellow",
]


def headline_limits(layout):
    """Headline 1-line and 2-line character limits per page size. 50 for 1 line and 100 for 2 lines by default, or the page size's characters per line if smaller"""
    cap = LIMITS.get("HEADLINE_LINE_CHARS", {}).get(layout)
    if not cap:
        return HL1, HL2
    return min(HL1, cap), min(HL2, 2 * cap)


def _luminance(hex6):
    """WCAG relative luminance"""
    c = [int(hex6[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _contrast(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def theme_contrast_warns(theme_colors):
    """Text contrast check for directly set theme color keys (WARN). The rules are the THEME_TEXT_RULES copy from tokens.js (limits.json).
    Values computed from the base color are built to meet the rules, so only directly set keys are checked.
    If a brand color must be used as is, pass with a reason for keeping in --allow-warn"""
    spec = LIMITS.get("THEME_TEXT") or {}
    norm = lambda v: str(v).replace("#", "").upper()
    if not all(re.fullmatch(r"[0-9A-F]{6}", norm(v)) for val in theme_colors.values() for v in (val if isinstance(val, list) else [val])):
        return []  # Format errors are reported as a separate FAIL
    text = {"white": "FFFFFF", "textDark": norm(theme_colors.get("textDark", spec.get("TEXT_DARK", "333333")))}
    out = []
    for rule in spec.get("RULES", []):
        key, _, idx = rule["key"].partition(".")
        val = theme_colors.get(key)
        if val is None:
            continue
        fill = norm(val[int(idx)]) if idx and isinstance(val, list) and int(idx) < len(val) else (norm(val) if not idx and not isinstance(val, list) else None)
        if not fill:
            continue
        r = _contrast(fill, text[rule["on"]])
        if r < rule["min"]:
            on = "white" if rule["on"] == "white" else "body"
            out.append(f"meta.themeColors.{rule['key']} #{fill} contrast with {on} text {r:.2f} < {rule['min']}. {spec.get('HINT', '')}")
    return out


def path_parent(obj, p):
    """Parent object and last key of a dot path (arrays numbered from 0). None if the path is missing"""
    segs = p.split(".")
    cur = obj
    for k in segs[:-1]:
        if isinstance(cur, list) and k.isdigit() and int(k) < len(cur): cur = cur[int(k)]
        elif isinstance(cur, dict) and k in cur: cur = cur[k]
        else: return None
    last = segs[-1]
    if isinstance(cur, list) and last.isdigit() and int(last) < len(cur): return cur, int(last)
    if isinstance(cur, dict): return cur, last
    return None


def apply_layout_patch(sl, layout, fails):
    """Slide copy with page-size-specific text (byLayout) applied for the page size (same rules as build.js)"""
    patches = sl.get("byLayout")
    if not patches: return sl
    out = copy.deepcopy(sl)
    out.pop("byLayout", None)
    known = LIMITS.get("LAYOUTS", {})
    for keys, patch in patches.items():
        lays = [k.strip() for k in keys.split(",")]
        bad = [k for k in lays if known and k not in known]
        if bad: fails.append(f"[{sl.get('id')}] byLayout page size {', '.join(bad)} is undefined")
        for p, v in patch.items():
            # Check every path regardless of page size so typos for other page sizes also surface
            if path_parent(sl, p) is None:
                fails.append(f"[{sl.get('id')}] byLayout path {p} not found")
            elif layout in lays:
                parent, last = path_parent(out, p)
                parent[last] = v
    return out


TEMPLATES = {"cover", "contents", "divider", "end", "digest", "free", "purpose", "scope", "features", "strategy", "process", "module_overview", "task", "task_multi", "bullets", "table", "chart_text", "chart_two", "compare", "roadmap", "gantt", "org", "orgchart", "staff_card", "swot", "cards", "steps", "illustrative", "conclusion", "composite"}
BAND_TEMPLATES = {"cover", "contents", "divider", "end"}
OWN_ENV = "IEUM_DECK_OWN"  # Custom slide path environment variable (same as build.js)
TEXT_BLOCKS = {"bullets", "text", "stack", "summary", "labeled"}  # composite blocks without tables, charts or diagrams
# composite recipes that hold company facts and organization and staff information
FACT_RECIPES = {"company_profile", "finance_status", "record_cards", "infra_tiles", "pm_profile", "case_card"}
ORG_RECIPES = {"pm_profile", "collaboration_structure"}


def load_own(meta, story_path):
    """Custom slides (own-deck.json). meta.ownDeck or the environment variable. None if not registered"""
    p = meta.get("ownDeck") or os.environ.get(OWN_ENV)
    if not p:
        return None
    path = Path(p) if Path(p).is_absolute() else Path(story_path).resolve().parent / p
    return json.load(open(path, encoding="utf-8")) if path.exists() else None


def own_role(geo, role):
    """Set of own template names matching a role name (e.g. {'own:19'})"""
    return {f"own:{n}" for n in ((geo or {}).get("roles") or {}).get(role, [])}


def blocks_of(sl):
    regs = ((sl.get("slots") or {}).get("regions")) or []
    return [b for r in regs for b in (r.get("blocks") or ([r["block"]] if r.get("block") else []))]


def tpl_key(sl):
    """Structure unit of the variety check. composite is told apart by recipe name, otherwise by grid and block layout"""
    tpl = sl.get("template") or sl.get("type") or ""
    if tpl != "composite":
        return tpl
    sd = sl.get("slots") or {}
    if sd.get("recipe"):
        return "composite:" + sd["recipe"]
    rows = sd.get("rows") or [{"cols": sd.get("cols") or []}]
    grid = "/".join(str(len(r.get("cols") or [1])) for r in rows)
    return "composite:" + grid + ":" + "+".join(b.get("kind", "?") for b in blocks_of(sl))


def text_only(sl):
    tpl = sl.get("template") or ""
    if tpl in ("bullets", "cards", "task_multi", "conclusion"):
        return True
    if tpl == "composite":
        kinds = {b.get("kind") for b in blocks_of(sl)}
        return bool(kinds) and kinds <= TEXT_BLOCKS
    return False

FAIL_PATTERNS = [
    (r"—|–", "em dash used"),
    (r"[가-힣A-Za-z]+(가|이) 아닌 ", "contrast construction (X가 아닌 Y)"),
    (r"(?<![\d~\-])\d+\s?대 (전략|방안|과제|축|원칙|목표|영역)", "number declaration (N대 X)"),
    (r"이러한 맥락에서|시사하는 바가 큼|주지하다시피|말할 것도 없이", "empty filler expression"),
    (r"획기적|혁신적인|압도적|매우 |매우$|탁월한", "exaggerating modifier"),
    (r"본 절에서는|앞서 제시한|앞에서 살펴본|다음 슬라이드에서", "meta narration"),
    (r"배점|채점|방어 논리|결정 장소|귀속", "internal evaluation vocabulary"),
    (r"누락 없이 반영|빠짐없이 반영", "coverage declaration"),
    (r"그리고 |그러나 |하지만 |그러므로 |그렇기 때문에|(?:^|\s)이는 ", "connective"),  # endings such as "줄이는 ", "높이는 " are excluded
    (r"(하는|되는|인) 것을 목적$|것을 목표$|것으로 함$", "noun form with the predicate cut off (grammar error. Rewrite in the '수립을 목적으로 추진' form)"),
]
WARN_WORDS = ["맥락", "패러다임", "인사이트", "함의", "축", "층위", "정립", "선제", "선점", "게이트", "매핑", "컨틴전시", "딥다이브"]
POLITE_END = re.compile(r"(합니다|입니다|됩니다|습니다|십시오)\s*$")
# Company fact placeholders. Kept until the user confirms
FACT_PLACEHOLDERS = ["[회사 확인]", "[실적 확인]", "[인력 확인]", "[전문분야]", "[대표 실적]", "[N]명", "[기관명]", "[발주기관]", "[발주처]", "[과제명]", "[금액]"]
# Institutional wording table (same as references/wording.md). Terms outside the column WARN
TRACK_TERMS = {
    "rnd": ["전략계획서", "중간평가 자체평가", "특정평가", "종료평가", "자체점검위원회", "성과관리·활용계획", "성과관리 활용계획", "대표성과 소개서", "효과성 분석", "사업기획점검", "사업추진심사", "설계적합성심사", "실태점검"],
    "mgmt": ["경영실적보고서", "경영평가단", "계량지표", "비계량지표", "경영평가 편람"],
    "general": [],
}
# Source strings quote external document titles and material names as is, so they are excluded from style and vocabulary checks (placeholder checks stay)
CITATION_KEYS = ("source", "factSource")
# Sentence norms that also apply to source strings. Punctuation can be replaced without changing what is quoted
CITATION_CHECKED = ("em dash used",)
# methods sample module names that are a defect when copied as is in non-R&D tracks
METHODS_EXAMPLE_MODULES = ["대내외 환경분석", "내부현황과 사례분석", "시사점과 전략체계", "실행계획", "정책과 환경 분석", "기존 사업과 사례 분석", "목표 체계와 논리모형", "타당성 확보", "현황 진단", "갭 분석", "개선안 도출", "환경분석", "현황분석", "목표모델 수립", "이행계획"]


def texts_of(sl):
    """Every string of the slide (body text, headline excluded)"""
    out = []
    def walk(v, key=None):
        if isinstance(v, str):
            out.append((key, v))
        elif isinstance(v, list):
            for x in v: walk(x, key)
        elif isinstance(v, dict):
            for k, x in v.items():
                if k in ("id", "template", "type", "chapter", "section", "secNo", "tracker", "notes", "digest", "rfpTasks", "moduleTasks", "evalItems", "bandMode", "kind", "dir", "src", "image", "logo", "photo", "fill", "line", "color", "align"):
                    continue
                walk(x, k)
    walk({k: v for k, v in sl.items() if k != "headline"})
    return out


def label_checks(labels):
    """Checks meta.labels. Returns (fails, warns). Names missing from the default table (assets/labels.json) and type errors are FAILs because the label would not apply"""
    fails, warns = [], []
    if labels is None:
        return fails, warns
    if not isinstance(labels, dict):
        return [f"meta.labels must be an object of the form {{template or block: {{slot: label}}}}. Input: {str(labels)[:40]}"], warns
    groups = ", ".join(LABEL_DEFAULTS)
    for g, slots in labels.items():
        if g not in LABEL_DEFAULTS:
            why = "template without label slots" if g in TEMPLATES else "unknown template or block name"
            fails.append(f"meta.labels.{g}: {why}. Allowed names: {groups}")
            continue
        known = LABEL_DEFAULTS[g]
        if not isinstance(slots, dict):
            fails.append(f"meta.labels.{g} must be an object of the form {{slot: label}}. Slots: {', '.join(known)}")
            continue
        for k, v in slots.items():
            path = f"meta.labels.{g}.{k}"
            if k not in known:
                nested = [x for x in known if x.startswith(k + ".")]
                hint = f" (write nested slots as dotted keys: {', '.join(nested)})" if nested else ""
                fails.append(f"{path}: unknown slot{hint}. Slots of {g}: {', '.join(known)}")
                continue
            d = known[k]
            texts = []
            if g == "notation":
                if not (isinstance(v, list) and all(isinstance(x, str) and x.strip() for x in v)):
                    fails.append(f"{path} must be a list of strings (e.g. [\"Fuente\", \"Nota\"])")
                    continue
                texts = v
                for x in v:
                    if re.search(r"[:：]\s*$", x): warns.append(f"{path}: drop the colon at the end of token '{x}' (the build recognizes the 'token:' form)")
            elif isinstance(d, list):
                if not (isinstance(v, list) and len(v) == len(d) and all(isinstance(x, str) and x.strip() for x in v)):
                    fails.append(f"{path} must be a list of {len(d)} strings (default {d})")
                    continue
                texts = v
            elif isinstance(d, dict):
                if not isinstance(v, dict):
                    fails.append(f"{path} must be an object of the form {{key: label}}. Keys: {', '.join(d)}")
                    continue
                for sk, sv in v.items():
                    if sk not in d: fails.append(f"{path}.{sk}: unknown key. Keys: {', '.join(d)}")
                    elif not isinstance(sv, str) or not sv.strip(): fails.append(f"{path}.{sk} must be a non-empty string")
                    else: texts.append(sv)
            elif not isinstance(v, str):
                fails.append(f"{path} must be a string. Input: {str(v)[:30]}")
                continue
            elif g == "language":
                if not LANG_TAG_RE.fullmatch(v): fails.append(f"{path} must be a language tag (e.g. en-US, ko-KR). Input: {v}")
                continue
            elif not v.strip() and not (g == "steps" and k == "stepLabel"):
                fails.append(f"{path}: empty label (omit the key to keep the default; only steps.stepLabel takes an empty string, to drop the prefix)")
                continue
            else:
                texts = [v]
                for tok in ("{n}", "{t}"):
                    if tok in d and tok not in v: warns.append(f"{path}: format string without {tok} (default '{d}'; the number or title will not show)")
            for tx in texts:
                if re.search(r"—|–", tx): fails.append(f"{path}: em dash used ({tx[:30]})")
    return fails, warns


def lint(story, ledger=None, story_path=".", layout=None):
    fails, warns = [], []
    meta = story.get("meta", {})
    # As in build.js, the --layout argument takes priority over meta.layout
    layout = layout or meta.get("layout") or BASE_LAYOUT
    hl1, hl2 = headline_limits(layout)
    geo = load_own(meta, story_path)
    if (meta.get("ownDeck") or os.environ.get(OWN_ENV)) and geo is None:
        fails.append("A custom slide path is set but the file is missing (check meta.ownDeck or IEUM_DECK_OWN)")
    own_n = {s["n"]: s for s in (geo or {}).get("slides", [])}
    # build.js reads custom theme colors as color codes, so check the format first (base is the input for computing all theme keys)
    for key, val in (meta.get("themeColors") or {}).items():
        for v in (val if isinstance(val, list) else [val]):
            if not re.fullmatch(r"#?[0-9A-Fa-f]{6}", str(v)):
                fails.append(f"meta.themeColors.{key} must be a 6-digit color code (e.g. 1B4332). Input: {v}")
    warns.extend(theme_contrast_warns(meta.get("themeColors") or {}))
    lf, lw = label_checks(meta.get("labels"))
    fails.extend(lf); warns.extend(lw)
    slides = [apply_layout_patch(s, layout, fails) for s in story.get("slides", [])]
    style = meta.get("headlineStyle", "noun")
    track = meta.get("track", "general")
    rfp = meta.get("rfp", {})
    ids = [s.get("id") for s in slides]
    for i in ids:
        if ids.count(i) > 1: fails.append(f"[{i}] duplicate id")
    run_tpl, run_n = None, 0
    free_n = 0
    for s in slides:
        sid = s.get("id", "?")
        tpl = s.get("template") or s.get("type") or ""
        if not (tpl in TEMPLATES or re.match(r"^own:\d+$", tpl)):
            fails.append(f"[{sid}] template {tpl} is undefined")
        elif tpl.startswith("own:") and int(tpl[4:]) not in own_n:
            fails.append(f"[{sid}] {tpl} used: no such number among the custom slides (without registered custom slides, replace it with a parametric template or composite recipe)")
        key = tpl_key(s)
        if key == run_tpl: run_n += 1
        else: run_tpl, run_n = key, 1
        if run_n == L.get("sameTemplateRun", 3) + 1: warns.append(f"[{sid}] same structure {key} {run_n} slides in a row (monotonous rhythm)")
        if tpl == "free": free_n += 1
        hl = s.get("headline", "")
        # bandMode blank draws no band, so there is no headline position
        if tpl not in BAND_TEMPLATES and not tpl.startswith("own:") and s.get("bandMode") != "blank" and not hl:
            fails.append(f"[{sid}] no headline")
        if tpl.startswith("own:") and not hl and (own_n.get(int(tpl[4:])) or {}).get("mode", "full") != "blank":
            warns.append(f"[{sid}] {tpl} uses the custom slide's original headline as is. Setting headline is recommended")
        if hl:
            n_hl = han_len(hl)
            if n_hl > hl2: fails.append(f"[{sid}] headline {n_hl:.0f} chars (Hangul equivalent) > 2-line limit {hl2}")
            elif n_hl > hl1: warns.append(f"[{sid}] headline {n_hl:.0f} chars (Hangul equivalent) > 1-line limit {hl1}")
            polite = bool(POLITE_END.search(hl))
            if style == "noun" and polite: fails.append(f"[{sid}] headline has a polite ending (style setting noun)")
            if style == "polite" and not polite and HANGUL_RE.search(hl): fails.append(f"[{sid}] headline has a noun ending (style setting polite)")
            if re.fullmatch(r"[가-힣A-Za-z ]{2,12}", hl.strip()) and " " not in hl.strip():
                warns.append(f"[{sid}] headline looks like a topic label: {hl}")
        mk = s.get("marker")
        if isinstance(mk, str) and han_len(mk) > L.get("markerTitle", 30): fails.append(f"[{sid}] marker {han_len(mk):.0f} chars (Hangul equivalent) > {L.get('markerTitle', 30)}")
        for key, tx in texts_of(s) + [("headline", hl)]:
            if not isinstance(tx, str): continue
            if "{{" in tx: fails.append(f"[{sid}] leftover slot: {tx[:30]}")
            if "[확인" in tx:
                # Unconfirmed items keep the check marker after the build, but it must be resolved before the completion report
                # Fact placeholders such as [회사 확인] are counted once by the FACT_PLACEHOLDERS check below
                (fails if meta.get("final") else warns).append(f"[{sid}] check marker left: {tx[:30]}")
            for ph in FACT_PLACEHOLDERS:
                if ph in tx:
                    (fails if meta.get("final") else warns).append(f"[{sid}] item awaiting user confirmation '{ph}': {tx[:30]}")
            cited = key in CITATION_KEYS
            for pat, name in FAIL_PATTERNS:
                if cited and name not in CITATION_CHECKED: continue
                if name.startswith("number declaration") and s.get("allowCount"): continue  # Counts set by the RFP are exempt with allowCount: true
                if re.search(pat, tx): fails.append(f"[{sid}] {name}: {tx[:40]}")
            if cited: continue
            for w in WARN_WORDS:
                if re.search(r"(?<![가-힣])" + w + r"(?![가-힣])", tx): warns.append(f"[{sid}] discouraged word '{w}': {tx[:30]}")
            if key != "headline" and tpl not in BAND_TEMPLATES and POLITE_END.search(tx): fails.append(f"[{sid}] polite ending in body text: {tx[:30]}")
            for wd in rfp.get("wording", []):
                for v in wd.get("variants", []):
                    if v and v in tx: fails.append(f"[{sid}] RFP wording variant '{v}' (standard '{wd.get('standard')}')")
            for tr, terms in TRACK_TERMS.items():
                if tr != track:
                    for term in terms:
                        if term in tx: warns.append(f"[{sid}] institutional term outside track {track} '{term}': {tx[:30]}")
    # own slot text length: over 1.4x the original shrinks all sibling boxes, so warn
    for s in slides:
        tpl = s.get("template") or ""
        if not tpl.startswith("own:") or not isinstance(s.get("slots"), dict): continue
        if not geo: break
        n = int(tpl[4:])
        if n not in own_n: continue
        atoms = own_n[n]["atoms"]
        texts = ["\n".join("".join(r["t"] for r in p["runs"]) for p in a["paras"]) for a in atoms if a["kind"] not in ("image", "chart", "table") and a.get("paras")]
        norm = lambda v: re.sub(r"\s+", "", str(v))
        for k, v in s["slots"].items():
            if not isinstance(v, str) or not v: continue
            orig = None
            if k.startswith("~"): orig = next((t for t in texts if norm(t).startswith(norm(k[1:]))), None)
            elif re.fullmatch(r"t\d+", k) and int(k[1:]) <= len(texts): orig = texts[int(k[1:]) - 1]
            if orig is None:
                if k.startswith("~"): warns.append(f"[{s.get('id')}] {tpl} no original text matches slot key '{k}'")
                continue
            n_o, n_v = han_len(orig, False), han_len(v, False)
            if n_o >= 6 and n_v > max(n_o * 1.4, n_o + 6): warns.append(f"[{s.get('id')}] {tpl} slot '{k}' {n_v:.0f} chars > original {n_o:.0f} chars x1.4 (Hangul equivalent, shrinks sibling boxes)")
    if free_n > L.get("freeSlidesMax", 8): warns.append(f"free slides {free_n} > {L.get('freeSlidesMax', 8)}")
    # Score attribution
    items = rfp.get("evalItems", [])
    covered = {}
    for s in slides:
        for e in s.get("evalItems", []): covered.setdefault(e, []).append(s.get("id"))
    body_n = sum(1 for s in slides if (s.get("template") or "") not in BAND_TEMPLATES)
    total = sum(float(it.get("score", 0)) for it in items if not it.get("quantitative")) or 0
    for it in items:
        if it.get("quantitative"): continue
        sl = covered.get(it["id"], [])
        if not sl: fails.append(f"evaluation item {it['id']} {it.get('name', '')} has 0 attributed slides")
        elif total and body_n:
            sr, wr = float(it.get("score", 0)) / total, len(sl) / body_n
            if wr <= sr / 2 or wr >= sr * 2: warns.append(f"evaluation item {it['id']} weight share {sr:.0%} against slide share {wr:.0%}")
    # Full Task coverage
    tasks = rfp.get("tasks", [])
    mtasks = rfp.get("moduleTasks", [])
    proposal = str(meta.get("kind") or "").startswith("proposal") or bool(rfp)
    # Types that use the plan or RFP chapter structure as is skip the module and Task checks
    module_free = str(meta.get("structure") or "") in ("plan", "sections") or str(meta.get("taskType") or "") in ("rnd_plan", "nonrnd_bid")
    if proposal and not tasks: fails.append("meta.rfp.tasks missing: list every RFP work item as T1..Tn")
    if proposal and not mtasks and not module_free:
        fails.append("meta.rfp.moduleTasks missing: list the module and Task design as M{n}-T{m}")
    placed = set(t for m in mtasks for t in m.get("rfp", []))
    if module_free:
        # Types without modules check full coverage through the slides' rfpTasks
        on_slides = set(t for s in slides for t in s.get("rfpTasks", []))
        for t in tasks:
            if t["id"] not in on_slides:
                fails.append(f"RFP item {t['id']} has no matching slide: {t.get('text', '')[:30]}")
    else:
        for t in tasks:
            if t["id"] not in placed: fails.append(f"RFP work item {t['id']} not placed in a module Task: {t.get('text', '')[:30]}")
    OVERVIEW_TPL = {"module_overview"} | own_role(geo, "module_overview")
    appear, appear_all = {}, {}
    for s in slides:
        for t in s.get("moduleTasks", []):
            appear_all.setdefault(t, []).append(s.get("id"))
            # Module overview slides list Tasks, so they do not count as execution plan slides
            if (s.get("template") or "") not in OVERVIEW_TPL: appear.setdefault(t, []).append(s.get("id"))
    mods = {}
    for m in mtasks:
        if m["id"] not in appear:
            where = " (listed only in the module overview)" if m["id"] in appear_all else ""
            fails.append(f"Task {m['id']} {m.get('title', '')} does not appear on an execution plan slide{where}")
        if track != "rnd" and any(m.get("title", "") == ex for ex in METHODS_EXAMPLE_MODULES) and not m.get("rfpNamed"):
            warns.append(f"methods sample module name '{m.get('title')}' matched literally in a non-R&D track (if it is the RFP name, set rfpNamed: true)")
        mods.setdefault(str(m["id"]).split("-")[0], []).append(m)
    # Module overview and volume per module
    for mod, items in (sorted(mods.items()) if not module_free else []):
        ov = [s for s in slides if (s.get("template") in OVERVIEW_TPL) and any(str(t).startswith(mod + "-") for t in s.get("moduleTasks", []))]
        if not ov: fails.append(f"module {mod} has no overview slide (place 1 with module_overview)")
        elif len(ov) > 1: fails.append(f"module {mod} has {len(ov)} overview slides (exactly 1 per module)")
        elif len(ov[0].get("moduleTasks", [])) < len(items):
            fails.append(f"module {mod} overview slide lists only {len(ov[0].get('moduleTasks', []))} Tasks (list all {len(items)} designed)")
        n_sl = len({sid for m in items for sid in appear.get(m["id"], [])})
        if n_sl < L.get("moduleSlidesMin", 2): warns.append(f"module {mod} has {n_sl} slides (recommended minimum {L.get('moduleSlidesMin', 2)})")
        if n_sl > L.get("moduleSlidesMax", 8): warns.append(f"module {mod} has {n_sl} slides (recommended maximum {L.get('moduleSlidesMax', 8)})")
    # Duplicate numbers and symbols: repeating in the text a number the band adds shows it twice
    for sl in slides:
        sec = str(sl.get("section") or "").strip()
        no = str(sl.get("secNo") or "").strip()
        if no and sec.startswith(no):
            warns.append(f"[{sl.get('id')}] duplicate section number (secNo '{no}' and section '{sec[:16]}')")
        elif re.match(r"^\d+[.)]\s", sec) and no:
            warns.append(f"[{sl.get('id')}] duplicate section number (section starts with a number: '{sec[:16]}')")
        for k, v in ((sl.get("slots") or {}).items() if isinstance(sl.get("slots"), dict) else []):
            items = v if isinstance(v, list) else None
            if not items: continue
            lead = [x for x in items if isinstance(x, str) and re.match(r"^\s*([-·•▪○□※*]|\d+[.)])\s", x)]
            if lead:
                warns.append(f"[{sl.get('id')}] duplicate bullet symbol (slot '{k}' item starts with a symbol: '{lead[0][:16]}')")
                break

    # Module section title notation: the [Module N] format avoids clashing with the period after the section number
    for sl in slides:
        sec = str(sl.get("section") or "")
        if re.match(r"^Module\s*\d+\s*[.·]", sec):
            warns.append(f"[{sl.get('id')}] module section title '{sec[:20]}' (recommended notation [Module N] module name)")
        for it in ((sl.get("slots") or {}).get("items") or []):
            if isinstance(it, str) and re.match(r"^Module\s*\d+\s*[.·]", it):
                warns.append(f"[{sl.get('id')}] contents or divider module item '{it[:20]}' (recommended notation [Module N] module name)")
                break

    # Mixed subject terms: use one within a deck
    SUBJ = ["본 과업", "본 연구", "본 과제", "본 사업", "본 프로젝트", "본 보고서"]
    found = Counter()
    for sl in slides:
        pool = [sl.get("headline") or ""] + [v for _, v in texts_of(sl)]
        for tx in pool:
            for w in SUBJ:
                if w in tx: found[w] += 1
    if len(found) > 1:
        warns.append(f"mixed subject terms {dict(found)} (use one)")
    # Mixed leader titles: engagements name leaders differently, so use one title within a deck
    LEADER = {
        "overall": ["총괄책임자", "연구책임자", "과제책임자", "사업책임자", "총괄PM"],
        "quality": ["품질관리자", "품질책임자", "품질담당자"],
    }
    # Custom slide source text uses "연구책임자" in the sense of a survey target, so only project organization and lead profile slides are checked
    ORG_T = {"org", "orgchart", "staff_card"} | own_role(geo, "org_project") | own_role(geo, "people_table") | own_role(geo, "pm_profile") | own_role(geo, "collaboration")
    org_slides = [sl for sl in slides if (sl.get("template") or "") in ORG_T or ((sl.get("slots") or {}).get("recipe") in ORG_RECIPES)]
    for kind, names in LEADER.items():
        hit = Counter()
        for sl in org_slides:
            pool = [sl.get("headline") or "", sl.get("section") or "", sl.get("marker") or ""] + [v for _, v in texts_of(sl)]
            for tx in pool:
                for w2 in names:
                    if w2 in tx: hit[w2] += 1
        if len(hit) > 1:
            warns.append(f"mixed {kind} leader titles {dict(hit)} (pick one following the RFP spelling)")
    # Custom slide engagement labels left in a non-proposal output
    if not proposal:
        for sl in slides:
            for k, v in texts_of(sl):
                if isinstance(v, str) and re.search(r"과업(의|\s|$)", v) and not re.search(r"과업지시서|과업 세부내용|과업 내용", v):
                    warns.append(f"[{sl.get('id')}] '과업' label left in a non-proposal output ('{v[:14]}') → replace with the subject term")
                    break

    # 과업 left in body labels after the subject term changed
    main = found.most_common(1)[0][0] if found else None
    if main and main != "본 과업":
        word = main.replace("본 ", "")
        for sl in slides:
            for k, v in texts_of(sl):
                if isinstance(v, str) and re.search(r"과업(의|\s|$)", v) and not re.search(r"과업지시서|과업 세부내용|과업 내용", v):
                    warns.append(f"[{sl.get('id')}] '과업' left in a body label ('{v[:14]}') → consider replacing it with '{word}'")
                    break

    for sl in slides:
        if "본 기획" in (sl.get("headline") or ""):
            warns.append(f"[{sl.get('id')}] '본 기획' notation (planning research also uses 본 연구 or 본 과업)")

    # Notes entered as bullet items: move them to a note slot or source
    # Tokens added with meta.labels.notation.source ("token:") count as note notation too (same rule as build.js)
    lab = meta.get("labels") if isinstance(meta.get("labels"), dict) else {}
    src = lab["notation"].get("source") if isinstance(lab.get("notation"), dict) else None
    extra = [str(t).strip() for t in src if str(t).strip()] if isinstance(src, list) else []
    extra_note = re.compile(r"^\s*(?:" + "|".join(re.escape(t) for t in extra) + r")\s*[:：]") if extra else None
    for sl in slides:
        for k, v in texts_of(sl):
            if k in ("note", "notes", "source", "caption", "footnotes"): continue  # Note slots are fine
            if isinstance(v, str) and (re.match(r"^\s*(※|출처\s*:|자료\s*:|[Ss]ources?\s*:|[Nn]otes?\s*:)", v) or (extra_note and extra_note.match(v))):
                warns.append(f"[{sl.get('id')}] note mark in a body item ('{v[:16]}') → moving it to a note slot or source is recommended")
                break

    # Empty table cells: cells that look meant for merging but lack merged make the table look broken
    for sl in slides:
        sd = sl.get("slots") or {}
        for key in ("rows", "table"):
            tb = sd.get(key)
            rows = tb.get("rows") if isinstance(tb, dict) else tb
            if not isinstance(rows, list) or len(rows) < 2: continue
            if sd.get("merged") or (isinstance(tb, dict) and tb.get("merged")): continue
            ncol = max((len(r) for r in rows if isinstance(r, list)), default=0)
            hit = False
            for c in range(min(ncol, 2)):  # Check only the leading category columns
                blanks = 0
                for r in rows:
                    if not isinstance(r, list) or c >= len(r): continue
                    if str(r[c]).strip() == "": blanks += 1
                if blanks >= 2:
                    warns.append(f"[{sl.get('id')}] {blanks} empty cells in table column {c + 1} (set merged if a merge is meant, otherwise fill the values)")
                    hit = True
                    break
            if hit: break

    # Background and purpose volume: many leads and evidence items overflow the left chevrons
    for sl in slides:
        if (sl.get("template") or "") != "purpose": continue
        leads = ((sl.get("slots") or {}).get("leads") or [])
        subs = sum(len([x for x in (l or {}).get("sub", []) if x]) for l in leads)
        if len(leads) > 4:
            warns.append(f"[{sl.get('id')}] background and purpose has {len(leads)} leads (3-4 recommended)")
        elif len(leads) + subs > 12:
            warns.append(f"[{sl.get('id')}] background and purpose has {len(leads) + subs} items (12 or fewer leads and evidence combined recommended)")

    # Custom slide slot substitution volume: text much longer than the original overflows the box
    if geo:
        for sl in slides:
            tpl = str(sl.get("template") or "")
            if not tpl.startswith("own:"): continue
            own = own_n.get(int(tpl.split(":")[1]))
            if not own: continue
            atoms = {"".join(r["t"] for p in (a.get("paras") or []) for r in p["runs"]): a for a in own.get("atoms", [])}

            # Slides with icons have a narrower text area, so the width is taken conservatively
            icon_slide = any(a.get("kind") == "image" for a in own.get("atoms", []))

            def para_pt(a):
                sizes = [r.get("sz") for p in (a.get("paras") or []) for r in p.get("runs", []) if r.get("sz")]
                return max(sizes) if sizes else 12.0

            def wrapped(txt, w_in, pt=12.0):
                w_in = w_in * (0.75 if icon_slide else 1.0)
                em = sum(1.0 if "\uac00" <= c <= "\ud7a3" or "\u4e00" <= c <= "\u9fff" or "\u3400" <= c <= "\u4dbf" or "\uf900" <= c <= "\ufaff" or "\u2190" <= c <= "\u21ff" or "\u2500" <= c <= "\u27bf" or c == "\u203b" else 0.55 for c in txt)
                per = max(0.1, (w_in - 0.5)) / (pt / 72)
                return max(1, int(em / per) + (1 if em % per > 0.1 else 0))

            over = []
            for k, v in (sl.get("slots") or {}).items():
                if not isinstance(v, str) or not k.startswith("~"): continue
                src = k[1:]
                a = atoms.get(src) or next((x for t, x in atoms.items() if t.startswith(src)), None)
                if not a: continue
                pt = para_pt(a)
                ln_src = sum(wrapped(x, a["w"], pt) for x in src.split("\n"))
                ln_new = sum(wrapped(x, a["w"], pt) for x in v.split("\n"))
                # Report only when the text has more lines than the original and also exceeds the box height
                paras_n = len(v.split("\n"))
                need = ln_new * (pt * 1.15 / 72) + paras_n * 0.04  # Sum of line heights and paragraph spacing
                # Considering the builder's room to cut spacing, report only above 125% of the box height
                if ln_new > ln_src and need > a["h"] * 1.25:
                    over.append(f"{src[:10]}→{ln_new} lines")
            if over:
                warns.append(f"[{sl.get('id')}] {tpl} substituted text exceeds box capacity {over[:3]} (cut characters or items. Font shrinking is not used)")

    # Line breaks in background and purpose evidence items: evidence sticks to the item text and is typeset without ※ (visual checks belong to the SKILL.md visual review)
    for sl in slides:
        if (sl.get("template") or "") != "purpose": continue
        leads = (sl.get("slots") or {}).get("leads") or []
        if any("\n" in str(x) for l in leads for x in ((l or {}).get("sub") or []) if isinstance(x, str)):
            warns.append(f"[{sl.get('id')}] line break in a background and purpose evidence item (move evidence to the note slot to get ※)")

    # Duplicate automatic prefixes: repeating the prefix the builder adds in steps titles and process module names shows it twice
    for sl in slides:
        sd = (sl.get("slots") or {})
        if sd.get("stepLabel") == "":
            pass  # With the prefix off, titles may carry their own numbers
        else:
          for x in (sd.get("steps") or []):
            t = str((x or {}).get("title") or "")
            if re.match(r"^\s*(STEP|Step)\s*\d*[.)]?\s", t) or re.match(r"^\s*\d+[.)]\s", t):
                warns.append(f"[{sl.get('id')}] duplicate prefix in a steps title ('{t[:16]}') → write only the title without the prefix, or set stepLabel to \"\"")
                break
        for x in (sd.get("modules") or [] if (sl.get("template") or "") == "process" else []):
            t = str((x or {}).get("title") or "")
            if re.match(r"^\s*(M\d+|Module\s*\d+)[-.\s]", t):
                warns.append(f"[{sl.get('id')}] duplicate prefix in a process module name ('{t[:16]}') → move it to the id field")
                break

    # Section number notation: a bare number without a period looks attached to the title
    for sl in slides:
        no = str(sl.get("secNo") or "").strip()
        if no and re.fullmatch(r"[0-9IVXivx①-⑮]+", no):
            warns.append(f"[{sl.get('id')}] section number '{no}' has no period (the builder corrects it to '{no.lstrip('0') or no}.')")

    # Missing space between number and title: attached forms such as "1.목차" read poorly
    for sl in slides:
        cands = [sl.get("section"), sl.get("marker"), sl.get("headline")]
        cands += [v for _, v in texts_of(sl) if isinstance(v, str)]
        for v in cands:
            # Dates ("2023. 2.)"), decimals and version numbers are excluded (closing brackets and punctuation after a number are written attached)
            m = re.search(r"(^|\s)(\d{1,2}|[IVX]+|[①-⑮])[.)](?![\d\s)\]}」』,.])\S", v.strip()) if isinstance(v, str) else None
            if m and not re.search(r"\d{4}\.\d|\d\.\d", v):
                # Show the text around the flagged spot so it can be found in long text
                s = v.strip()
                warns.append(f"[{sl.get('id')}] no space after the number ('{s[max(0, m.start(2) - 8):m.end() + 8]}')")
                break

    # task_multi is allowed only when a page limit is declared (repeated bundle cards are a distinctiveness defect)
    for sl in slides:
        if (sl.get("template") or "") != "task_multi": continue
        if not meta.get("pageLimit"):
            fails.append(f"[{sl.get('id')}] task_multi is only for engagements with a page limit (set meta.pageLimit or split into one slide per Task)")

    # Variety across all body slides: few template kinds in the body (band slides excluded) feel monotonous
    BAND_TPL = ("cover", "contents", "divider", "end", "digest")
    body_slides = [s for s in slides if (s.get("template") or "") not in BAND_TPL]
    if len(body_slides) >= 8:
        kinds_all = len({tpl_key(s) for s in body_slides})
        need_all = max(3, int(len(body_slides) * L.get("deckVarietyRatio", 0.3)))
        if kinds_all < need_all:
            warns.append(f"{len(body_slides)} body slides use {kinds_all} template kinds < recommended {need_all} (repeating one structure is monotonous)")
        top = Counter(tpl_key(s) for s in body_slides).most_common(1)[0]
        if top[1] > len(body_slides) * L.get("deckTemplateShareMax", 0.4):
            warns.append(f"template '{top[0]}' is used on {top[1]}/{len(body_slides)} body slides (skewed to one template)")
        # Share of slides filled only with bullets: warn when slides without tables, charts or diagrams exceed half
        text_only_n = [s for s in body_slides if text_only(s)]
        if len(text_only_n) > len(body_slides) * L.get("bulletOnlyShareMax", 0.5):
            warns.append(f"{len(text_only_n)}/{len(body_slides)} slides use only bullet panels (review content that could become tables, charts or diagrams)")
        for ch in {s.get("chapter") for s in body_slides if s.get("chapter")}:
            cs = [s for s in body_slides if s.get("chapter") == ch]
            if len(cs) >= 5 and len({tpl_key(s) for s in cs}) <= 1:
                warns.append(f"all {len(cs)} slides of chapter '{ch}' use one template (vary the structure within the chapter too)")

    # Task slide variety: execution plan slides repeating one template are a distinctiveness defect
    task_slides = [s for s in slides if s.get("moduleTasks") and (s.get("template") or "") not in OVERVIEW_TPL]
    if len(task_slides) >= 3:
        tpls = [tpl_key(s) for s in task_slides]
        kinds = len(set(tpls))
        need = max(2, int(len(task_slides) * L.get("taskVarietyRatio", 0.5)))
        if kinds == 1:
            fails.append(f"all {len(task_slides)} Task slides use the single structure '{tpls[0]}' (choose a template or composite recipe that fits each Task)")
        elif kinds < need:
            warns.append(f"Task slides use {kinds} template kinds < recommended {need} (repeating one structure weakens distinctiveness)")
        for mod, items in sorted(mods.items()):
            ms = [s for s in task_slides if any(str(t).startswith(mod + "-") for t in s.get("moduleTasks", []))]
            if len(ms) >= 3 and len({tpl_key(s) for s in ms}) == 1:
                warns.append(f"all {len(ms)} Task slides of module {mod} use the same template (vary the structure within the module too)")

    # Task bundle limit per slide: 1 Task per slide by default, up to 3 under a page limit
    for sl in slides:
        if (sl.get("template") or "") in OVERVIEW_TPL: continue
        n = len(sl.get("moduleTasks", []))
        if n > L.get("tasksPerSlideMax", 4):
            fails.append(f"[{sl.get('id')}] {n} Tasks on one slide (limit {L.get('tasksPerSlideMax', 4)}. Split the slide)")
        elif n >= 3:
            warns.append(f"[{sl.get('id')}] {n} Tasks on one slide (if volume allows, splitting into one Task per slide is recommended)")
    # Missing Task numbers: names the numbers among T1..Tn in a module that have no slide
    for mod, items in sorted(mods.items()):
        nums = []
        for m in items:
            mm = re.search(r"-T(\d+)$", str(m["id"]))
            if mm: nums.append((int(mm.group(1)), m))
        nums.sort()
        for n, m in nums:
            if m["id"] not in appear:
                fails.append(f"{mod}-T{n} '{m.get('title', '')}' has no execution plan slide (neighboring Tasks exist)")
        seq = [n for n, _ in nums]
        if seq and sorted(seq) != list(range(1, len(seq) + 1)):
            warns.append(f"module {mod} Task numbers are not consecutive {seq} (numbering from T1 in sequence is recommended)")
    # Task compression ratio against RFP work items
    if tasks and mtasks and len(mtasks) < len(tasks) * 0.6:
        warns.append(f"{len(mtasks)} designed Tasks against {len(tasks)} RFP work items (record the merging reason in 00_strategy.md)")
    # Company fact slides record the basis of user confirmation
    FACT_TPL = {"staff_card", "features"} | own_role(geo, "company_fact") | own_role(geo, "people_table") | own_role(geo, "pm_profile")
    for sl in slides:
        tpl = sl.get("template") or ""
        if tpl not in FACT_TPL and (sl.get("slots") or {}).get("recipe") not in FACT_RECIPES: continue
        if not sl.get("factSource"):
            warns.append(f"[{sl.get('id')}] company fact slide without factSource (give the name of the user-provided material or the confirmation date)")

    # Consistency of the project organization chart (org) and the staffing table (staff_card, 투입인력 table)
    # Staff recognition form 1 (staff cells): pm, qa and team member cells of the organization chart, name cells of tables with a 성명 column in the header row, rows labeled 성명, staff_card name
    #   Reads the name before the cell value regardless of title ("김수연 부사장" → 김수연). Both slides must read names by the same criterion for the roster comparison to hold
    # Staff recognition form 2 (free text): "[인력A]" and "name + consulting title" strings
    # English names: 2-3 words starting with a capital ("Jane Kim"). Staff cells read the leading name; free text reads a name only when a title follows a comma, as in "Jane Kim, Senior Consultant"
    NOT_NAME = r"(?!총괄|품질|자문|담당|참여|연구|프로젝|분야|전문|외부|내부|전담|현장|미정)"
    ROLE_EN = "|".join(map(re.escape, sorted(STAFF_TITLES_EN, key=len, reverse=True)))
    ROLE = "|".join(map(re.escape, sorted(STAFF_TITLES_KO, key=len, reverse=True))) + "|(?i:" + ROLE_EN + ")"
    LATIN_NAME = r"[A-Z][A-Za-z'’.-]+(?:\s[A-Z][A-Za-z'’.-]+){1,2}?"
    NAME = re.compile(r"\[인력[A-Z0-9]*\]|(?<![가-힣])" + NOT_NAME + r"[가-힣]{2,4}(?=\s+(?:" + ROLE + r")(?![가-힣A-Za-z]))"
                      + r"|(?<![A-Za-z])" + LATIN_NAME + r"(?=,\s*(?:" + ROLE_EN + r")\b)")
    LEAD_NAME = re.compile(r"^\s*(\[인력[A-Z0-9]*\]|" + NOT_NAME + r"[가-힣]{2,4})(?=\s|\(|$)")
    LEAD_NAME_EN = re.compile(r"^\s*(" + LATIN_NAME + r")(?=\s*(?:,|\(|$)|\s+(?:" + ROLE_EN + r")\b)")
    # An English title itself, or a phrase ending in a title word ("Business Analyst"), is not a name
    EN_TITLE_TAIL = re.compile(r"\b(?:" + "|".join(sorted({t.split()[-1] for t in STAFF_TITLES_EN})) + r")$")
    NAME_HEAD = re.compile(r"^(성명|이름|name)$", re.I)
    # Exclude the first word of spaced titles (선임 in 선임 컨설턴트, 고문 in 고문 컨설턴트) so it is not taken as a name
    TITLE_WORDS = {w for t in STAFF_TITLES_KO for w in t.split()} | {"선임", "수석", "책임", "주임", "전임", "시니어", "초빙", "겸임", "고문"}

    def lead_name(v):
        """Leading name of a staff cell value. For table cell dicts with merge info, reads text. None without a name"""
        text = v.get("text") if isinstance(v, dict) else v
        m = (LEAD_NAME.match(text) or LEAD_NAME_EN.match(text)) if isinstance(text, str) else None
        return m.group(1) if m else None

    def names_of(sl):
        out = set()
        def walk(v):
            if isinstance(v, str):
                out.update(NAME.findall(v))
            elif isinstance(v, list):
                for x in v: walk(x)
            elif isinstance(v, dict):
                head, rows = v.get("head"), v.get("rows")
                if isinstance(head, list) and isinstance(rows, list):
                    cols = [i for i, h in enumerate(head) if NAME_HEAD.match(str(h).strip())]
                    for r in rows:
                        for i in cols:
                            if isinstance(r, list) and i < len(r): out.add(lead_name(r[i]))
                if "role" in v: out.add(lead_name(v.get("name")))  # staff_card staff
                if NAME_HEAD.match(str(v.get("label", "")).strip()): out.add(lead_name(v.get("text")))  # 성명 row of a labeled block
                for x in v.values(): walk(x)
        slots = sl.get("slots") or {}
        if (sl.get("template") or "") == "org":
            members = [m for t in (slots.get("teams") or []) for m in (t.get("members") or [])]
            out.update(lead_name(x) for x in [slots.get("pm"), slots.get("qa"), *members])
        walk(slots)
        walk(sl.get("blocks") or [])
        return {x for x in out if x and not ROLE_LABEL.match(x) and x not in TITLE_WORDS and not EN_TITLE_TAIL.search(x)}

    ROLE_LABEL = re.compile(r"^(총괄책임자|품질관리자|자문위원회|품질관리|발주기관|발주처|프로젝트)")

    PEOPLE_OWN = own_role(geo, "people_table")

    def is_staff(sl):
        tpl = sl.get("template") or ""
        if tpl == "staff_card" or tpl in PEOPLE_OWN: return True
        txt = str(sl.get("marker", "")) + str(sl.get("section", "")) + str(sl.get("headline", ""))
        return tpl in ("table", "composite") and re.search(r"투입\s?인력|인력 계획|참여인력|(?i:staffing|project staff|key staff|staff plan)", txt)

    org_sl = [s for s in slides if (s.get("template") or "") in ({"org"} | own_role(geo, "org_project"))]
    staff_sl = [s for s in slides if is_staff(s)]
    if org_sl and not staff_sl: fails.append("project organization chart without a staffing slide (the chart and the staffing table are one set)")
    if staff_sl and not org_sl: fails.append("staffing slide without a project organization chart (the chart and the staffing table are one set)")
    if org_sl and staff_sl:
        org_names = set().union(*[names_of(s) for s in org_sl])
        staff_names = set().union(*[names_of(s) for s in staff_sl])
        if org_names and staff_names:
            # The staff sets of the two slides express the same information, so they match exactly
            miss = staff_names - org_names
            if miss: fails.append(f"{sorted(miss)} in the staffing table missing from the organization chart (staff on the two slides must match exactly)")
            extra = org_names - staff_names
            if extra: fails.append(f"{sorted(extra)} in the organization chart missing from the staffing table (staff on the two slides must match exactly)")
        elif not staff_names:
            warns.append("no staff entries found on the staffing slide (write them as [인력A] or name and title)")
        for st in staff_sl:
            if (st.get("template") or "") not in PEOPLE_OWN: continue
            filled = {int(m.group(1)) for k in (st.get("slots") or {}) for m in [re.match(r"tb1\.r(\d+)c\d+$", k)] if m and str((st.get("slots") or {})[k]).strip()}
            if filled and max(filled) < 11 and len(filled) < max(filled):
                warns.append(f"[{st.get('id')}] empty middle rows in the staffing table (rows {sorted(set(range(1, max(filled) + 1)) - filled)})")
        teams = [t for s in org_sl for t in ((s.get("slots") or {}).get("teams") or [])]
        org_mod = set()
        for s in org_sl:
            for t in ((s.get("slots") or {}).get("teams") or []): org_mod.add(str(t.get("name", "")))
            for k, v in (s.get("slots") or {}).items():
                if isinstance(v, str) and re.match(r"^\s*Module\s*\d", v): org_mod.add(v.strip())
        if org_mod and len(org_mod) < len(mods):
            fails.append(f"organization chart has {len(org_mod)} module boxes < {len(mods)} designed modules (show every module as a box)")
        if teams and len(teams) > 8: warns.append(f"organization chart has {len(teams)} module boxes (2-row layout limit 8)")
    # Section ledger
    if ledger is not None:
        lids = [x.get("id") for x in ledger.get("slides", [])]
        if lids != ids:
            fails.append(f"section ledger slide list mismatch: ledger {len(lids)}, storyboard {len(ids)}, difference {sorted(set(lids) ^ set(ids))[:6]}")
    return fails, warns


def main():
    args = sys.argv[1:]
    if not args: raise SystemExit(__doc__)
    story = json.load(open(args[0], encoding="utf-8"))
    ledger = json.load(open(args[args.index("--ledger") + 1], encoding="utf-8")) if "--ledger" in args else None
    layout = args[args.index("--layout") + 1] if "--layout" in args else None
    fails, warns = lint(story, ledger, args[0], layout)
    for f in fails: print("FAIL", f)
    for w in warns: print("WARN", w)
    print(f"lint: FAIL {len(fails)} WARN {len(warns)} slides {len(story.get('slides', []))}")
    if "--report" in args:
        json.dump({"fails": fails, "warns": warns}, open(args[args.index("--report") + 1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # Warnings also fail by default. To pass with a stated reason, add --allow-warn "reason"
    allow = args[args.index("--allow-warn") + 1] if "--allow-warn" in args else None
    if fails:
        sys.exit(1)
    if warns and not allow:
        print("lint: failing because WARNs remain. Fix them or pass with --allow-warn \"reason for keeping\"")
        sys.exit(1)
    if warns and allow:
        print(f"lint: {len(warns)} WARNs kept (reason: {allow})")
    sys.exit(0)


if __name__ == "__main__":
    main()
