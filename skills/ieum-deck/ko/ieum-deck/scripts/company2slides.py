#!/usr/bin/env python3
"""company2slides.py: 회사 프로필(assets/company.md) → 회사 공통 슬라이드 storyboard 조각(assets/common-slides.json)

WHY: 제안서의 제안업체 현황과 사업관리 부문은 과업이 바뀌어도 내용이 거의 같다.
     회사 정보를 한 파일에서 관리하고 슬라이드를 재생성해야 제안서마다 같은 사실을 같은 표현으로 유지한다.

생성 슬라이드 (파라메트릭 템플릿과 composite 레시피만 사용)
- Ⅱ. 제안업체 현황: 일반 현황(company_profile), 조직 구성(bullets), 경영 상태(finance_status), 수행 실적(table)
- Ⅳ. 사업관리부문: 레시피 견본(assets/recipe-demos.json)의 관리 레시피 9종을 복제
  company.md 관리 방법론 문구가 있으면 해당 슬라이드의 헤드라인으로 사용
- 제안업체 현황 슬라이드의 헤드라인은 표 값으로 작성. company.md 헤드라인 절에 문구가 있으면 그 문구를 사용

사용: python3 scripts/company2slides.py [company.md] [common-slides.json]
- 실행 후 미치환 자리 표기([회사 확인] 등) 건수를 출력
- 슬라이드 id, chapter, secNo 는 storyboard 목차에 맞게 조정
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
PLACEHOLDER_RE = re.compile(r"\[[^\]]*\]")  # [회사 확인], [발주기관], [연도 1] 등 대괄호 자리 표기
FACT_SOURCE = "회사 프로필 (사용자 제공 자료)"
CH_COMPANY = "Ⅱ. 제안업체 현황"
CH_MGMT = "Ⅳ. 사업관리부문"
HISTORY_ROWS_MAX = 8      # 일반 현황 연혁 표 표시 행 수
RECORD_ROWS_PER_SLIDE = 16  # scripts/limits.json tableRowsPerSlide 와 같은 값
HEADLINE_FIELDS = 2       # 헤드라인에 쓰는 사업 분야 개수
# company.md 헤드라인 절의 키 → 공통 파트 슬라이드 id. 문구가 있으면 표 값으로 만든 기본 헤드라인 대신 사용
HEADLINE_KEYS = {"C01": "일반 현황", "C02": "조직", "C03": "경영 상태", "C04": "수행 실적"}
THOUSAND_WON_PER_EOK = 100_000  # 1억원 = 10만 천원
# 기본 정보 값에 붙이는 단위. 숫자만 적은 값과 자리 표기에만 붙임 (표와 헤드라인의 단위 표기를 같게 유지)
FIELD_UNITS = {"설립연도": "년", "임직원 수": "명"}
BARE_VALUE_RE = re.compile(r"[\d,]+|\[[^\]]*\]")

# 관리 부문: (절 제목, [(레시피, 관리 방법론 문구 키)]). 절 제목은 공공 제안요청서의 평가항목 명칭 관행을 따름
MGMT_SECTIONS = [
    ("사업관리 방법론", [("progress_control", "진도"), ("quality_plan", "품질"), ("report_plan", "보고"), ("deliverable_plan", "산출물")]),
    ("기밀보안 및 비상대책", [("security_plan", "보안"), ("privacy_plan", "개인정보")]),
    ("안전관리 및 보건관리 계획", [("emergency_plan", "비상")]),
    ("추가제안 및 사후지원계획", [("aftercare", "사후지원"), ("additional_offer", "추가제안")]),
]


def parse_tables(md):
    """## 제목 아래 첫 표를 {제목 첫 낱말: 행 목록(머리 행 포함)} 으로 반환"""
    out, key, rows, ended = {}, None, [], False
    for line in md.splitlines() + ["## _end"]:
        s = line.strip()
        if s.startswith("## "):
            if key and rows:
                out.setdefault(key, rows)
            key, rows, ended = s[3:].split()[0], [], False
        elif s.startswith("|") and not ended:
            if not re.match(r"^\|?\s*:?-{2,}", s):  # 구분 행 제외
                rows.append([c.strip() for c in s.strip("|").split("|")])
        elif rows:
            ended = True  # 첫 표가 끝나면 같은 제목 아래의 다른 표는 읽지 않음
    return out


def josa(word, with_final, without_final):
    """받침 유무에 맞는 조사를 붙임. 한글이 아니면 받침 없음으로 처리"""
    last = word[-1] if word else ""
    has_final = "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 != 0
    return word + (with_final if has_final else without_final)


# 관리 방법론 문구 형식. 괄호 키 형식이 기본이며 이전 양식의 콜론 키 형식도 읽음
PHRASE_RES = (re.compile(r"^-\s*\(([^)]+)\)\s*(.+)$"), re.compile(r"^-\s*([^:：()]+)\s*[:：]\s*(.+)$"))


def parse_phrases(md, title):
    """## title 절 아래 '- (키) 문구' 또는 '- 키: 문구' 목록을 {키: 문구} 로 반환 (문구가 빈 줄은 제외)"""
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
    """기본 정보 값. 단위나 설명이 이미 있는 값(예: 2015년 3월, 약 40명)은 그대로 사용"""
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
            {"title": "주요 연혁", "block": {"kind": "table", "head": ["연도", "내용"], "rows": hist}},
        ]},
    }


def org_slide(company, basic, org):
    depts = {}
    for r in org:
        depts.setdefault(r[0], []).append(f"{r[1]}: {r[2]}")
    first = next(iter(depts), PLACEHOLDER)
    staff = field_value(basic, "임직원 수")
    # 본부나 팀 칸에 자리 표기가 남아 있으면 조직 규모를 셀 수 없으므로 수 대신 자리 표기를 씀 (자리 표기 행을 1개 본부 1개 팀으로 세지 않음)
    unknown = not org or any(PLACEHOLDER_RE.search(r[0]) or PLACEHOLDER_RE.search(r[1]) for r in org)
    n_dept, n_team = (PLACEHOLDER, PLACEHOLDER) if unknown else (len(depts), len(org))
    return {
        "id": "C02", "template": "bullets", "secNo": "2.", "section": "조직 및 인원 현황", "chapter": CH_COMPANY,
        "headline": f"{josa(company, '은', '는')} {n_dept}개 본부 {n_team}개 팀 {staff}으로 구성",
        "marker": "조직 구성 및 팀별 전문성", "factSource": FACT_SOURCE,
        "slots": {"panels": [{"head": k, "items": v} for k, v in depts.items()], "point": f"본 과업에는 {first} 중심으로 전담 인력 투입"},
    }


def to_eok(thousand_won):
    """천원 단위 금액을 억원 표기로 변환 (헤드라인 길이 단축). 100억원 미만은 소수 첫째 자리까지"""
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
            {"title": "재무 현황 (단위 천원)", "block": {"kind": "table", "head": head, "rows": [r[: len(head)] for r in fin[1:]]}},
            {"title": "신용평가등급", "block": {"kind": "image", "label": "신용평가등급 확인서", "caption": "신용평가기관 발급 확인서 (사용자 제공)"}},
        ]},
    }


def record_slides(company, rec):
    head, body = (rec[0], rec[1:]) if rec else (["연번", "발주기관", "과제명", "기간", "개월", "계약금액"], [])
    # 상한을 넘으면 장 수를 먼저 정하고 행을 고르게 나누어 마지막 장만 비는 현상을 막음
    n_slides = max(1, -(-len(body) // RECORD_ROWS_PER_SLIDE))
    size = max(1, -(-len(body) // n_slides))
    chunks = [body[i:i + size] for i in range(0, len(body), size)] or [[]]
    slides = []
    for k, rows in enumerate(chunks):
        suffix = "" if len(chunks) == 1 else f" ({k + 1}/{len(chunks)})"
        slides.append({
            "id": f"C04{chr(ord('a') + k) if len(chunks) > 1 else ''}", "template": "table", "secNo": "4.", "section": "유사분야 수행실적", "chapter": CH_COMPANY,
            "headline": f"{josa(company, '은', '는')} 유사 분야 과업 {len(body)}건을 수행하여 과업 수행 경험을 축적",
            "marker": f"유사 분야 수행 실적{suffix}", "factSource": FACT_SOURCE,
            "slots": {"head": head, "rows": rows},
        })
    return slides


def mgmt_slides(phrases, demos, start):
    by_recipe = {s["slots"].get("recipe"): s for s in demos["slides"] if s.get("template") == "composite"}
    slides, n = [], start
    for sec_no, (section, items) in enumerate(MGMT_SECTIONS, start=1):
        for recipe, key in items:
            if recipe not in by_recipe:
                raise SystemExit(f"{RECIPE_DEMOS.name} 에 레시피 {recipe} 견본 없음")
            src = copy.deepcopy(by_recipe[recipe])
            slides.append({
                "id": f"C{n:02d}", "template": "composite", "secNo": f"{sec_no}.", "section": section, "chapter": CH_MGMT,
                "headline": phrases.get(key, src["headline"]), "marker": src.get("marker", ""), "slots": src["slots"],
                **{k: src[k] for k in ("source", "footnotes") if k in src},
            })
            n += 1
    return slides


def count_placeholders(value):
    """문자열 값 안의 자리 표기 건수. JSON 직렬화 문자열로 세면 배열 괄호까지 자리 표기로 잡히므로 값을 순회하여 셈"""
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
        key = HEADLINE_KEYS.get(s["id"][:3])  # 실적이 여러 장이면 C04a, C04b 로 나뉘므로 앞 3자로 대응
        if heads.get(key):
            s["headline"] = heads[key]
    demos = json.loads(RECIPE_DEMOS.read_text(encoding="utf-8"))
    slides += mgmt_slides(parse_phrases(md, "관리 방법론"), demos, start=5)
    dst.write_text(json.dumps({"company": company, "slides": slides}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{dst} slides={len(slides)} 미치환 자리 표기={count_placeholders(slides)}건")


if __name__ == "__main__":
    main()
