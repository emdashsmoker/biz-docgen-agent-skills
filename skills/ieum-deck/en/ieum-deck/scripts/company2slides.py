#!/usr/bin/env python3
"""company2slides.py: company profile (assets/company.md) → storyboard fragment of common company slides (assets/common-slides.json)

WHY: The bidder status and project management parts of a proposal stay nearly the same across engagements.
     Keeping company information in one file and regenerating the slides keeps the same facts in the same wording in every proposal.

Generated slides (parametric templates and composite recipes only)
- Ⅱ. 제안업체 현황 (bidder status): general status (company_profile), organization (bullets), financial status (finance_status), track record (table)
- Ⅳ. 사업관리부문 (project management): copies the 9 management recipes from the recipe samples (assets/recipe-demos.json)
  If company.md has a management methodology phrase, it becomes the headline of that slide
- Bidder status headlines are written from table values. If the headline section of company.md has a phrase, that phrase is used

Usage: python3 scripts/company2slides.py [company.md] [common-slides.json]
- Prints the count of unreplaced placeholders ([회사 확인], etc.) after running
- Adjust slide id, chapter and secNo to the storyboard table of contents
"""
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
DEFAULT_SRC = ASSETS / "company.md"
DEFAULT_DST = ASSETS / "common-slides.json"
RECIPE_DEMOS = ASSETS / "recipe-demos.json"

PLACEHOLDER = "[회사 확인]"
PLACEHOLDER_RE = re.compile(r"\[[^\]]*\]")  # Bracketed placeholders such as [회사 확인], [발주기관], [연도 1]
FACT_SOURCE = "회사 프로필 (사용자 제공 자료)"
CH_COMPANY = "Ⅱ. 제안업체 현황"
CH_MGMT = "Ⅳ. 사업관리부문"
HISTORY_ROWS_MAX = 8      # Rows shown in the history table of the general status slide
RECORD_ROWS_PER_SLIDE = 16  # Same value as tableRowsPerSlide in scripts/limits.json
HEADLINE_FIELDS = 2       # Number of business areas used in the headline
# Key in the headline section of company.md → common part slide id. A phrase there replaces the default headline built from table values
HEADLINE_KEYS = {"C01": "일반 현황", "C02": "조직", "C03": "경영 상태", "C04": "수행 실적"}
THOUSAND_WON_PER_EOK = 100_000  # KRW 100 million (1억원) = 100,000 thousand won
# Units added to basic information values. Added only to number-only values and placeholders (keeps the unit notation of the table and headline the same)
FIELD_UNITS = {"설립연도": "년", "임직원 수": "명"}
BARE_VALUE_RE = re.compile(r"[\d,]+|\[[^\]]*\]")
# Column alignment of the form tables (storyboard align). Quantity columns (months, contract amount, yearly amounts) are right-aligned, identifier columns (year, serial number, period) and short text columns are centered
# The user can rename header cells in company.md (e.g. "계약금액 (지분)"), so alignment follows column order, not header names
HISTORY_ALIGN = ["center", "center"]  # 연도, 내용
RECORD_ALIGN = ["center", "center", "center", "center", "right", "right"]  # 연번, 발주기관, 과제명, 기간, 개월, 계약금액
FINANCE_LABEL_ALIGN, FINANCE_VALUE_ALIGN = "center", "right"  # 구분 column, yearly amount columns

# Management part: (section title, [(recipe, management methodology phrase key)]). Section titles follow the usual evaluation item names of public RFPs
MGMT_SECTIONS = [
    ("사업관리 방법론", [("progress_control", "진도"), ("quality_plan", "품질"), ("report_plan", "보고"), ("deliverable_plan", "산출물")]),
    ("기밀보안 및 비상대책", [("security_plan", "보안"), ("privacy_plan", "개인정보")]),
    ("안전관리 및 보건관리 계획", [("emergency_plan", "비상")]),
    ("추가제안 및 사후지원계획", [("aftercare", "사후지원"), ("additional_offer", "추가제안")]),
]


def parse_tables(md):
    """Returns the first table under each ## title as {first word of title: row list (header row included)}"""
    out, key, rows, ended = {}, None, [], False
    for line in md.splitlines() + ["## _end"]:
        s = line.strip()
        if s.startswith("## "):
            if key and rows:
                out.setdefault(key, rows)
            key, rows, ended = s[3:].split()[0], [], False
        elif s.startswith("|") and not ended:
            if not re.match(r"^\|?\s*:?-{2,}", s):  # Skip separator rows
                rows.append([c.strip() for c in s.strip("|").split("|")])
        elif rows:
            ended = True  # After the first table ends, other tables under the same title are not read
    return out


def josa(word, with_final, without_final):
    """Attaches the Korean particle matching whether the last syllable has a final consonant. Non-Hangul counts as no final consonant"""
    last = word[-1] if word else ""
    has_final = "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 != 0
    return word + (with_final if has_final else without_final)


# Management methodology phrase format. The parenthesized key format is the default, and the colon key format of the older template is also read
PHRASE_RES = (re.compile(r"^-\s*\(([^)]+)\)\s*(.+)$"), re.compile(r"^-\s*([^:：()]+)\s*[:：]\s*(.+)$"))


def parse_phrases(md, title):
    """Returns the '- (key) phrase' or '- key: phrase' list under the ## title section as {key: phrase} (lines with an empty phrase are skipped)"""
    out, inside = {}, False
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("## "):
            inside = s[3:].startswith(title)
            continue
        m = next(filter(None, (r.match(s) for r in PHRASE_RES)), None) if inside else None
        if m:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def to_number(text):
    try:
        return float(text.replace(",", ""))
    except (AttributeError, ValueError):
        return None


def field_value(basic, key):
    """Basic information value. Values that already carry a unit or description (e.g. 2015년 3월, 약 40명) stay as is"""
    value = basic.get(key) or PLACEHOLDER
    unit = FIELD_UNITS.get(key, "")
    return f"{value}{unit}" if unit and BARE_VALUE_RE.fullmatch(value) else value


def profile_slide(company, basic, history):
    fields = [f.strip() for f in basic.get("사업 분야", PLACEHOLDER).split(",") if f.strip()]
    head = fields[:HEADLINE_FIELDS] or [PLACEHOLDER]
    field_text = " ".join([josa(f, "과", "와") for f in head[:-1]] + head[-1:])
    labels = ["대표자", "설립연도", "임직원 수", "주소", "사업 분야", "인증"]
    rows = [{"label": k, "text": field_value(basic, k)} for k in labels]
    hist = [r[:2] for r in history[:HISTORY_ROWS_MAX]] or [[PLACEHOLDER, PLACEHOLDER]]
    return {
        "id": "C01", "template": "composite", "secNo": "1.", "section": "일반 현황", "chapter": CH_COMPANY,
        "headline": f"{josa(company, '은', '는')} {field_value(basic, '설립연도')} 설립 이후 {field_text} 과업을 수행한 전문 기업",
        "marker": "제안사 개요", "factSource": FACT_SOURCE,
        "slots": {"recipe": "company_profile", "cols": [1, 1.2], "regions": [
            {"title": "기본 정보", "block": {"kind": "labeled", "rows": rows}},
            {"title": "주요 연혁", "block": {"kind": "table", "head": ["연도", "내용"], "rows": hist, "align": HISTORY_ALIGN}},
        ]},
    }


def org_slide(company, basic, org):
    depts = {}
    for r in org:
        depts.setdefault(r[0], []).append(f"{r[1]}: {r[2]}")
    first = next(iter(depts), PLACEHOLDER)
    staff = field_value(basic, "임직원 수")
    # With placeholders left in the division or team cells, the organization size cannot be counted, so write placeholders instead of counts (a placeholder row does not count as 1 division and 1 team)
    unknown = not org or any(PLACEHOLDER_RE.search(r[0]) or PLACEHOLDER_RE.search(r[1]) for r in org)
    n_dept, n_team = (PLACEHOLDER, PLACEHOLDER) if unknown else (len(depts), len(org))
    return {
        "id": "C02", "template": "bullets", "secNo": "2.", "section": "조직 및 인원 현황", "chapter": CH_COMPANY,
        "headline": f"{josa(company, '은', '는')} {n_dept}개 본부 {n_team}개 팀 {staff}으로 구성",
        "marker": "조직 구성 및 팀별 전문성", "factSource": FACT_SOURCE,
        "slots": {"panels": [{"head": k, "items": v} for k, v in depts.items()], "point": f"본 과업에는 {first} 중심으로 전담 인력 투입"},
    }


def to_eok(thousand_won):
    """Converts an amount in thousand won to 억원 notation (shortens the headline). Under 100억원, one decimal place"""
    eok = thousand_won / THOUSAND_WON_PER_EOK
    return f"{eok:,.0f}억원" if eok >= 100 or eok == int(eok) else f"{eok:,.1f}억원"


def finance_headline(company, fin):
    years = fin[0][1:] if fin else []
    sales = next((r[1:] for r in fin[1:] if r and r[0] == "매출액"), [])
    a, b = (to_number(sales[0]), to_number(sales[-1])) if sales else (None, None)
    if a is None or b is None or not years:
        return f"{josa(company, '은', '는')} 최근 3개년 매출액과 자본총계를 공개 재무제표 기준으로 제시"
    trend = "증가" if b > a else "감소" if b < a else "유지"
    return f"{company}의 매출액은 {years[0]}년 {to_eok(a)}에서 {years[-1]}년 {to_eok(b)}으로 {trend}"


def finance_slide(company, fin):
    head = ["구분"] + [f"{h}년" if h.isdigit() else h for h in (fin[0][1:] if fin else [])]
    return {
        "id": "C03", "template": "composite", "secNo": "3.", "section": "제안업체 경영상태", "chapter": CH_COMPANY,
        "headline": finance_headline(company, fin), "marker": "제안사 경영 상태", "factSource": FACT_SOURCE,
        "slots": {"recipe": "finance_status", "cols": [1.6, 1], "regions": [
            {"title": "재무 현황 (단위 천원)", "block": {"kind": "table", "head": head, "rows": [r[: len(head)] for r in fin[1:]],
                                                     "align": [FINANCE_LABEL_ALIGN] + [FINANCE_VALUE_ALIGN] * (len(head) - 1)}},
            {"title": "신용평가등급", "block": {"kind": "image", "label": "신용평가등급 확인서", "caption": "신용평가기관 발급 확인서 (사용자 제공)"}},
        ]},
    }


def record_slides(company, rec):
    head, body = (rec[0], rec[1:]) if rec else (["연번", "발주기관", "과제명", "기간", "개월", "계약금액"], [])
    # Past the limit, fix the slide count first and spread rows evenly so the last slide is not left nearly empty
    n_slides = max(1, -(-len(body) // RECORD_ROWS_PER_SLIDE))
    size = max(1, -(-len(body) // n_slides))
    chunks = [body[i:i + size] for i in range(0, len(body), size)] or [[]]
    # With a column count different from the form, column order no longer tells the meaning, so align is left out (builder default alignment)
    align = {"align": RECORD_ALIGN} if len(head) == len(RECORD_ALIGN) else {}
    slides = []
    for k, rows in enumerate(chunks):
        suffix = "" if len(chunks) == 1 else f" ({k + 1}/{len(chunks)})"
        slides.append({
            "id": f"C04{chr(ord('a') + k) if len(chunks) > 1 else ''}", "template": "table", "secNo": "4.", "section": "유사분야 수행실적", "chapter": CH_COMPANY,
            "headline": f"{josa(company, '은', '는')} 유사 분야 과업 {len(body)}건을 수행하여 과업 수행 경험을 축적",
            "marker": f"유사 분야 수행 실적{suffix}", "factSource": FACT_SOURCE,
            "slots": {"head": head, "rows": rows, **align},
        })
    return slides


def mgmt_slides(phrases, demos, start):
    by_recipe = {s["slots"].get("recipe"): s for s in demos["slides"] if s.get("template") == "composite"}
    slides, n = [], start
    for sec_no, (section, items) in enumerate(MGMT_SECTIONS, start=1):
        for recipe, key in items:
            if recipe not in by_recipe:
                raise SystemExit(f"No sample for recipe {recipe} in {RECIPE_DEMOS.name}")
            src = copy.deepcopy(by_recipe[recipe])
            slides.append({
                "id": f"C{n:02d}", "template": "composite", "secNo": f"{sec_no}.", "section": section, "chapter": CH_MGMT,
                "headline": phrases.get(key, src["headline"]), "marker": src.get("marker", ""), "slots": src["slots"],
                **{k: src[k] for k in ("source", "footnotes") if k in src},
            })
            n += 1
    return slides


def count_placeholders(value):
    """Count of placeholders inside string values. Counting on the JSON-serialized string would also catch array brackets, so this walks the values"""
    if isinstance(value, str):
        return len(PLACEHOLDER_RE.findall(value))
    if isinstance(value, dict):
        return sum(count_placeholders(v) for v in value.values())
    if isinstance(value, list):
        return sum(count_placeholders(v) for v in value)
    return 0


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_DST
    md = src.read_text(encoding="utf-8")
    tb = parse_tables(md)
    basic = {r[0]: r[1] for r in tb.get("기본", [])[1:] if len(r) > 1}
    company = basic.get("회사명") or "제안사"
    slides = [
        profile_slide(company, basic, tb.get("연혁", [])[1:]),
        org_slide(company, basic, [r for r in tb.get("조직", [])[1:] if len(r) >= 3]),
        finance_slide(company, tb.get("재무", [])),
        *record_slides(company, tb.get("실적", [])),
    ]
    heads = parse_phrases(md, "헤드라인")
    for s in slides:
        key = HEADLINE_KEYS.get(s["id"][:3])  # Several track record slides split into C04a, C04b, so match by the first 3 characters
        if heads.get(key):
            s["headline"] = heads[key]
    demos = json.loads(RECIPE_DEMOS.read_text(encoding="utf-8"))
    slides += mgmt_slides(parse_phrases(md, "관리 방법론"), demos, start=5)
    dst.write_text(json.dumps({"company": company, "slides": slides}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{dst} slides={len(slides)} unreplaced_placeholders={count_placeholders(slides)}")


if __name__ == "__main__":
    main()
