#!/usr/bin/env python3
"""lint.py: storyboard.json 검사. FAIL 0건이 빌드 착수 조건.
사용: python3 lint.py <storyboard.json> [--layout 16:9|A4|10.83|4:3] [--ledger ledger.json] [--report out.json] [--allow-warn "유지 사유"]
검사 항목
- 스키마: id 고유, template 유효, 필수 필드, 사용자 지정 테마 색(meta.themeColors 의 base 와 색 키) 6자리 색상 코드 (FAIL)
- 테마 색 글자 대비: 직접 지정한 색 키가 그 위에 얹는 글자색(흰색 또는 본문 글자색)과 대비 하한 미달 (WARN, 규칙은 limits.json THEME_TEXT)
- 회사 사실 정보: 확인 표기와 자리 표기 잔존 (WARN, meta.final 이면 FAIL), 사실 정보 슬라이드의 factSource 부재 (WARN)
- 글자 수: 헤드라인 1줄 상한 50자(초과 WARN)와 2줄 상한 100자(초과 FAIL), 마커 30, 잔존 슬롯 {{ }} 와 [확인]. 판형(--layout 또는 meta.layout)의 1줄 상한(limits.json HEADLINE_LINE_CHARS, 16:9 상한을 헤드라인 폭 비율로 환산)이 50자보다 작으면 1줄 상한은 그 값, 2줄 상한은 그 2배
  글자 수는 나눔고딕 실측 폭을 한글 1자 폭으로 나눈 한글 환산 글자 수 (한글만 쓴 문구는 글자 수와 같고 영문과 공백은 폭만큼 적게 셈). 커스텀 슬라이드 슬롯 분량 비교도 같은 기준
- 문체: 헤드라인 문체(meta.headlineStyle: noun | polite), 본문 명사형(존댓말 종결 금지). 한글이 없는 헤드라인(영문 발표자료)은 문체 검사를 건너뜀
- 문장 규범: em dash, 대비 구문, 숫자 선언, 의미 공백, 과장, 메타 서술, 내부 어휘, 연결어 (FAIL) / 비선호 어휘 (WARN)
  출처 문자열(source, factSource)은 문헌 제목을 인용하므로 em dash 를 뺀 문장 규범, 비선호 어휘, 문체, RFP 워딩, 제도 워딩 검사에서 제외
- RFP 워딩: meta.rfp.wording[{standard, variants[]}] 변형 출현 FAIL
- 배점 귀속: meta.rfp.evalItems[{id, name, score, quantitative}] 비정량 전건 귀속 FAIL, 비중 편차 WARN
- 적용 범위: meta.kind 가 proposal 계열이거나 meta.rfp 가 있으면 제안 검사 전부 적용. 일반 기획 PPT 는 RFP·배점 검사를 건너뜀
- 모듈 미사용: meta.structure 가 plan 또는 sections 이면 모듈 개요와 Task 검사를 건너뛰고 RFP 항목 전수 대응만 검사
- Task 전수: meta.rfp.tasks 와 meta.rfp.moduleTasks 존재, RFP 과업 전건이 moduleTasks 에 배치, Task 전건이 슬라이드 1장 이상에 출현, 모듈마다 개요 슬라이드 1장과 Task 전건 표기 (FAIL). 모듈별 슬라이드 수와 Task 축약률 (WARN)
- Task 연번 결번: 모듈 안에서 슬라이드가 없는 Task 번호를 지목 (FAIL)
- 모듈 개요: 모듈당 고유 1장 (없거나 2장 이상이면 FAIL)
- Task 묶음: 한 슬라이드에 Task 5건 이상이면 FAIL, 3-4건이면 WARN
- 수행조직도(org)와 투입인력표(staff_card, 투입인력 표): 한쪽만 있으면 FAIL, 양방향 인력 일치, 모듈 상자 수와 설계 모듈 수 일치 (FAIL)
- 섹션대장 일치: ledger.slides[].id 와 storyboard 슬라이드 id 의 목록과 순서 일치 (FAIL). 나머지 필드는 대조하지 않음
- 제도 워딩: meta.track (rnd | mgmt | general) 과 다른 열의 용어 출현 WARN. 비R&D 에서 methods 예시 모듈명 문자 일치 WARN
- 번호와 기호 중복: section 이 secNo 를 반복하거나 불릿 슬롯 항목이 기호로 시작하면 WARN
- 커스텀 슬라이드 치환 분량: 치환 문구의 줄 수가 원문보다 늘고 상자 높이를 넘기면 WARN (meta.ownDeck 등록 시)
- 배경과 목적 근거: 근거 항목에 줄바꿈이 있으면 WARN (근거는 note 슬롯으로 옮겨 ※ 를 붙임)
- 배경과 목적 분량: 리드 4개 초과이거나 리드와 근거 합계 12개 초과면 WARN
- 표 빈 셀: 앞쪽 분류 열에 빈 셀이 2개 이상이고 merged 지정이 없으면 WARN
- 접두 중복: steps title 에 STEP 접두, process 모듈명에 M/Module 접두가 있으면 WARN
- 번호 표기: 번호 뒤에 공백이 없으면 WARN ("1.목차" → "1. 목차"), secNo 에 마침표가 없으면 WARN
- 주석 표기: 본문 항목이 ※ 나 "출처:", "자료:", "Source:", "Note:" 로 시작하면 WARN (note 계열 슬롯과 source 의 ※ 는 빌드가 붙이므로 검사하지 않음)
- 모듈 표기: 절 제목과 목차 항목이 "Module N." 형식이면 WARN ([Module N] 권장)
- 대상 지칭어: 지칭어 혼용, 지칭어 변경 후 과업 잔존, 제안 외 산출물의 과업 라벨 잔존 시 WARN, "본 기획" 표기 시 WARN
- 리더 호칭: 총괄 리더와 품질 리더의 호칭이 한 발표자료 안에서 섞이면 WARN
- 리듬: 같은 구조 4장 연속 WARN, free 8장 초과 WARN (composite 는 레시피나 블록 구성이 다르면 다른 구조로 셈)
- 덱 다양성: 본문 템플릿 종류가 본문 장수의 30% 미만이거나 한 템플릿이 40% 초과이거나 한 장이 단일 템플릿이면 WARN
- 불릿 편중: 불릿 패널 계열 템플릿이 본문의 50% 를 넘으면 WARN
- task_multi: meta.pageLimit 미지정 시 FAIL
- Task 다양성: 수행계획 슬라이드가 한 템플릿뿐이면 FAIL, 템플릿 종류가 슬라이드 수의 절반 미만이면 WARN
- 판형 전용 문구(byLayout): 판형(--layout 또는 meta.layout)과 일치하는 교체 값을 적용한 슬라이드를 검사. 판형 이름이나 경로 오류는 FAIL
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
BASE_LAYOUT = "16:9"  # 판형 미지정 시 기준 판형
FM_PATH = HERE.parent / "assets" / "font-metrics.json"
FM = json.load(open(FM_PATH, encoding="utf-8")) if FM_PATH.exists() else None  # 나눔고딕 실측 폭 (em). 없으면 추정 폭 사용
HANGUL_RE = re.compile(r"[가-힣]")


def char_em(ch, bold):
    """한 글자의 폭(em). atoms.js charEm 과 같은 규칙 (실측 표, 한글과 한자와 전각 기호는 한글 폭, 그 외는 other)"""
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
    """한글 환산 글자 수: 문구 폭을 한글 1자 폭으로 나눈 값. 한글만 쓴 문구는 글자 수와 같고 영문과 숫자와 공백은 폭만큼 적게 셈
    글자 수 상한을 영문 발표자료에도 같은 폭 기준으로 적용하기 위함 (영문 글자와 공백은 한글보다 폭이 좁아 같은 폭에 더 많이 들어감)"""
    unit = FM["bold" if bold else "regular"]["hangul"] if FM else 1.0
    return sum(char_em(ch, bold) for ch in str(txt)) / unit
# 인력 인식 직급 (자유 문장의 "성명 + 직급" 형식). 컨설팅사와 연구기관 직급의 한글 표기와 띄어쓰기 변형
# 일반 기업 직급과 학위는 목록에서 제외 ("서울대 박사" 의 학교명처럼 앞말을 성명으로 잡는 오탐 발생)
# 수행조직도의 인력 칸과 표의 성명 칸은 직급과 관계없이 앞의 성명을 읽음 (lint 의 lead_name)
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
    """판형별 헤드라인 1줄과 2줄 글자 수 상한. 1줄 50자와 2줄 100자를 기본으로 두고 판형의 1줄 수용 글자 수가 더 작으면 그 값을 따름"""
    cap = LIMITS.get("HEADLINE_LINE_CHARS", {}).get(layout)
    if not cap:
        return HL1, HL2
    return min(HL1, cap), min(HL2, 2 * cap)


def _luminance(hex6):
    """WCAG 상대 휘도"""
    c = [int(hex6[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _contrast(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def theme_contrast_warns(theme_colors):
    """직접 지정한 테마 색 키의 글자 대비 검사 (WARN). 규칙은 tokens.js 의 THEME_TEXT_RULES 사본(limits.json).
    기준 색(base) 계산값은 규칙을 충족하도록 만들어지므로 직접 지정한 키만 검사.
    브랜드 색을 그대로 써야 하면 --allow-warn 에 유지 사유를 적어 통과"""
    spec = LIMITS.get("THEME_TEXT") or {}
    norm = lambda v: str(v).replace("#", "").upper()
    if not all(re.fullmatch(r"[0-9A-F]{6}", norm(v)) for val in theme_colors.values() for v in (val if isinstance(val, list) else [val])):
        return []  # 형식 오류는 별도 FAIL 로 보고
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
            on = "흰" if rule["on"] == "white" else "본문"
            out.append(f"meta.themeColors.{rule['key']} #{fill} 위 {on} 글자 대비 {r:.2f} < {rule['min']}. {spec.get('HINT', '')}")
    return out


def path_parent(obj, p):
    """점 경로(배열은 0부터 번호)의 부모 객체와 마지막 키. 경로가 없으면 None"""
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
    """판형 전용 문구(byLayout)를 판형에 맞춰 적용한 슬라이드 사본 (build.js 와 같은 규칙)"""
    patches = sl.get("byLayout")
    if not patches: return sl
    out = copy.deepcopy(sl)
    out.pop("byLayout", None)
    known = LIMITS.get("LAYOUTS", {})
    for keys, patch in patches.items():
        lays = [k.strip() for k in keys.split(",")]
        bad = [k for k in lays if known and k not in known]
        if bad: fails.append(f"[{sl.get('id')}] byLayout 판형 {', '.join(bad)} 미정의")
        for p, v in patch.items():
            # 경로는 판형과 관계없이 모두 검사하여 다른 판형용 오기도 드러냄
            if path_parent(sl, p) is None:
                fails.append(f"[{sl.get('id')}] byLayout 경로 {p} 없음")
            elif layout in lays:
                parent, last = path_parent(out, p)
                parent[last] = v
    return out


TEMPLATES = {"cover", "contents", "divider", "end", "digest", "free", "purpose", "scope", "features", "strategy", "process", "module_overview", "task", "task_multi", "bullets", "table", "chart_text", "chart_two", "compare", "roadmap", "gantt", "org", "orgchart", "staff_card", "swot", "cards", "steps", "illustrative", "conclusion", "composite"}
BAND_TEMPLATES = {"cover", "contents", "divider", "end"}
OWN_ENV = "IEUM_DECK_OWN"  # 커스텀 슬라이드 경로 환경변수 (build.js 와 동일)
TEXT_BLOCKS = {"bullets", "text", "stack", "summary", "labeled"}  # 표, 차트, 도식이 없는 composite 블록
# composite 레시피 중 회사 사실 정보와 조직 인력 정보를 담는 레시피
FACT_RECIPES = {"company_profile", "finance_status", "record_cards", "infra_tiles", "pm_profile", "case_card"}
ORG_RECIPES = {"pm_profile", "collaboration_structure"}


def load_own(meta, story_path):
    """커스텀 슬라이드(own-deck.json). meta.ownDeck 또는 환경변수. 미등록이면 None"""
    p = meta.get("ownDeck") or os.environ.get(OWN_ENV)
    if not p:
        return None
    path = Path(p) if Path(p).is_absolute() else Path(story_path).resolve().parent / p
    return json.load(open(path, encoding="utf-8")) if path.exists() else None


def own_role(geo, role):
    """역할 이름에 대응하는 own 템플릿 이름 집합 (예: {'own:19'})"""
    return {f"own:{n}" for n in ((geo or {}).get("roles") or {}).get(role, [])}


def blocks_of(sl):
    regs = ((sl.get("slots") or {}).get("regions")) or []
    return [b for r in regs for b in (r.get("blocks") or ([r["block"]] if r.get("block") else []))]


def tpl_key(sl):
    """다양성 검사의 구조 단위. composite 는 레시피 이름, 없으면 격자와 블록 구성으로 구분"""
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
    (r"—|–", "em dash 사용"),
    (r"[가-힣A-Za-z]+(가|이) 아닌 ", "대비 구문(X가 아닌 Y)"),
    (r"(?<![\d~\-])\d+\s?대 (전략|방안|과제|축|원칙|목표|영역)", "숫자 선언(N대 X)"),
    (r"이러한 맥락에서|시사하는 바가 큼|주지하다시피|말할 것도 없이", "의미 공백 표현"),
    (r"획기적|혁신적인|압도적|매우 |매우$|탁월한", "과장 수식어"),
    (r"본 절에서는|앞서 제시한|앞에서 살펴본|다음 슬라이드에서", "메타 서술"),
    (r"배점|채점|방어 논리|결정 장소|귀속", "평가 내부 어휘"),
    (r"누락 없이 반영|빠짐없이 반영", "대응 선언"),
    (r"그리고 |그러나 |하지만 |그러므로 |그렇기 때문에|(?:^|\s)이는 ", "연결어"),  # "줄이는 ", "높이는 " 같은 어미는 제외
    (r"(하는|되는|인) 것을 목적$|것을 목표$|것으로 함$", "서술어를 자른 명사형 (문법 오류. '수립을 목적으로 추진' 형태로 재작성)"),
]
WARN_WORDS = ["맥락", "패러다임", "인사이트", "함의", "축", "층위", "정립", "선제", "선점", "게이트", "매핑", "컨틴전시", "딥다이브"]
POLITE_END = re.compile(r"(합니다|입니다|됩니다|습니다|십시오)\s*$")
# 회사 사실 정보 자리 표기. 사용자 확인 전에는 이 표기를 유지
FACT_PLACEHOLDERS = ["[회사 확인]", "[실적 확인]", "[인력 확인]", "[전문분야]", "[대표 실적]", "[N]명", "[기관명]", "[발주기관]", "[발주처]", "[과제명]", "[금액]"]
# 제도 워딩 표 (references/wording.md 와 동일). 열 밖 용어 출현 시 WARN
TRACK_TERMS = {
    "rnd": ["전략계획서", "중간평가 자체평가", "특정평가", "종료평가", "자체점검위원회", "성과관리·활용계획", "성과관리 활용계획", "대표성과 소개서", "효과성 분석", "사업기획점검", "사업추진심사", "설계적합성심사", "실태점검"],
    "mgmt": ["경영실적보고서", "경영평가단", "계량지표", "비계량지표", "경영평가 편람"],
    "general": [],
}
# 출처 문자열은 외부 문헌 제목과 자료명을 그대로 인용하므로 문체와 어휘 검사에서 제외 (자리 표기 검사는 유지)
CITATION_KEYS = ("source", "factSource")
# 출처 문자열에도 적용하는 문장 규범. 문장 부호는 인용 뜻을 바꾸지 않고 교체할 수 있음
CITATION_CHECKED = ("em dash 사용",)
# 비R&D 트랙에서 그대로 복제하면 결함인 methods 예시 모듈명
METHODS_EXAMPLE_MODULES = ["대내외 환경분석", "내부현황과 사례분석", "시사점과 전략체계", "실행계획", "정책과 환경 분석", "기존 사업과 사례 분석", "목표 체계와 논리모형", "타당성 확보", "현황 진단", "갭 분석", "개선안 도출", "환경분석", "현황분석", "목표모델 수립", "이행계획"]


def texts_of(sl):
    """슬라이드의 모든 문자열 (헤드라인 제외 본문)"""
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


def lint(story, ledger=None, story_path=".", layout=None):
    fails, warns = [], []
    meta = story.get("meta", {})
    # 판형은 build.js 와 같이 --layout 인자를 meta.layout 보다 우선
    layout = layout or meta.get("layout") or BASE_LAYOUT
    hl1, hl2 = headline_limits(layout)
    geo = load_own(meta, story_path)
    if (meta.get("ownDeck") or os.environ.get(OWN_ENV)) and geo is None:
        fails.append("커스텀 슬라이드 경로가 지정되었으나 파일 없음 (meta.ownDeck 또는 IEUM_DECK_OWN 확인)")
    own_n = {s["n"]: s for s in (geo or {}).get("slides", [])}
    # 사용자 지정 테마 색은 build.js 가 색상 코드로 읽으므로 형식을 먼저 확인 (base 는 테마 키 전체의 계산 입력)
    for key, val in (meta.get("themeColors") or {}).items():
        for v in (val if isinstance(val, list) else [val]):
            if not re.fullmatch(r"#?[0-9A-Fa-f]{6}", str(v)):
                fails.append(f"meta.themeColors.{key} 는 6자리 색상 코드 (예: 1B4332). 입력값: {v}")
    warns.extend(theme_contrast_warns(meta.get("themeColors") or {}))
    slides = [apply_layout_patch(s, layout, fails) for s in story.get("slides", [])]
    style = meta.get("headlineStyle", "noun")
    track = meta.get("track", "general")
    rfp = meta.get("rfp", {})
    ids = [s.get("id") for s in slides]
    for i in ids:
        if ids.count(i) > 1: fails.append(f"[{i}] id 중복")
    run_tpl, run_n = None, 0
    free_n = 0
    for s in slides:
        sid = s.get("id", "?")
        tpl = s.get("template") or s.get("type") or ""
        if not (tpl in TEMPLATES or re.match(r"^own:\d+$", tpl)):
            fails.append(f"[{sid}] 템플릿 {tpl} 미정의")
        elif tpl.startswith("own:") and int(tpl[4:]) not in own_n:
            fails.append(f"[{sid}] {tpl} 사용: 커스텀 슬라이드에 해당 번호 없음 (커스텀 슬라이드 미등록이면 파라메트릭 템플릿이나 composite 레시피로 교체)")
        key = tpl_key(s)
        if key == run_tpl: run_n += 1
        else: run_tpl, run_n = key, 1
        if run_n == L.get("sameTemplateRun", 3) + 1: warns.append(f"[{sid}] 같은 구조 {key} {run_n}장 연속 (리듬 단조)")
        if tpl == "free": free_n += 1
        hl = s.get("headline", "")
        # bandMode blank 는 밴드를 그리지 않으므로 헤드라인 자리가 없음
        if tpl not in BAND_TEMPLATES and not tpl.startswith("own:") and s.get("bandMode") != "blank" and not hl:
            fails.append(f"[{sid}] 헤드라인 없음")
        if tpl.startswith("own:") and not hl and (own_n.get(int(tpl[4:])) or {}).get("mode", "full") != "blank":
            warns.append(f"[{sid}] {tpl} 커스텀 슬라이드 헤드라인 원문 그대로 사용. headline 지정 권장")
        if hl:
            n_hl = han_len(hl)
            if n_hl > hl2: fails.append(f"[{sid}] 헤드라인 {n_hl:.0f}자(한글 환산) > 2줄 상한 {hl2}자")
            elif n_hl > hl1: warns.append(f"[{sid}] 헤드라인 {n_hl:.0f}자(한글 환산) > 1줄 상한 {hl1}자")
            polite = bool(POLITE_END.search(hl))
            if style == "noun" and polite: fails.append(f"[{sid}] 헤드라인 존댓말 종결 (문체 설정 noun)")
            if style == "polite" and not polite and HANGUL_RE.search(hl): fails.append(f"[{sid}] 헤드라인 명사형 종결 (문체 설정 polite)")
            if re.fullmatch(r"[가-힣A-Za-z ]{2,12}", hl.strip()) and " " not in hl.strip():
                warns.append(f"[{sid}] 헤드라인이 주제 라벨로 보임: {hl}")
        mk = s.get("marker")
        if isinstance(mk, str) and han_len(mk) > L.get("markerTitle", 30): fails.append(f"[{sid}] 마커 {han_len(mk):.0f}자(한글 환산) > {L.get('markerTitle', 30)}")
        for key, tx in texts_of(s) + [("headline", hl)]:
            if not isinstance(tx, str): continue
            if "{{" in tx: fails.append(f"[{sid}] 잔존 슬롯: {tx[:30]}")
            if "[확인" in tx:
                # 미확인 항목은 빌드 후에도 확인 표기를 남겨 두되 완료 보고 전에 해소
                # [회사 확인] 같은 사실 정보 자리 표기는 아래 FACT_PLACEHOLDERS 검사가 1건으로 집계
                (fails if meta.get("final") else warns).append(f"[{sid}] 확인 표기 잔존: {tx[:30]}")
            for ph in FACT_PLACEHOLDERS:
                if ph in tx:
                    (fails if meta.get("final") else warns).append(f"[{sid}] 사용자 확인 대기 항목 '{ph}': {tx[:30]}")
            cited = key in CITATION_KEYS
            for pat, name in FAIL_PATTERNS:
                if cited and name not in CITATION_CHECKED: continue
                if name.startswith("숫자 선언") and s.get("allowCount"): continue  # RFP 지정 개수는 allowCount: true 로 예외
                if re.search(pat, tx): fails.append(f"[{sid}] {name}: {tx[:40]}")
            if cited: continue
            for w in WARN_WORDS:
                if re.search(r"(?<![가-힣])" + w + r"(?![가-힣])", tx): warns.append(f"[{sid}] 비선호 어휘 '{w}': {tx[:30]}")
            if key != "headline" and tpl not in BAND_TEMPLATES and POLITE_END.search(tx): fails.append(f"[{sid}] 본문 존댓말 종결: {tx[:30]}")
            for wd in rfp.get("wording", []):
                for v in wd.get("variants", []):
                    if v and v in tx: fails.append(f"[{sid}] RFP 워딩 변형 '{v}' (표준 '{wd.get('standard')}')")
            for tr, terms in TRACK_TERMS.items():
                if tr != track:
                    for term in terms:
                        if term in tx: warns.append(f"[{sid}] 트랙 {track} 밖 제도 용어 '{term}': {tx[:30]}")
    # own 슬롯 텍스트 길이: 원문 대비 1.4배 초과는 형제 상자 전체가 축소되므로 경고
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
                if k.startswith("~"): warns.append(f"[{s.get('id')}] {tpl} 슬롯 키 '{k}' 에 맞는 원문 없음")
                continue
            n_o, n_v = han_len(orig, False), han_len(v, False)
            if n_o >= 6 and n_v > max(n_o * 1.4, n_o + 6): warns.append(f"[{s.get('id')}] {tpl} 슬롯 '{k}' {n_v:.0f}자 > 원문 {n_o:.0f}자 x1.4 (한글 환산, 형제 상자 축소 유발)")
    if free_n > L.get("freeSlidesMax", 8): warns.append(f"free 슬라이드 {free_n}장 > {L.get('freeSlidesMax', 8)}")
    # 배점 귀속
    items = rfp.get("evalItems", [])
    covered = {}
    for s in slides:
        for e in s.get("evalItems", []): covered.setdefault(e, []).append(s.get("id"))
    body_n = sum(1 for s in slides if (s.get("template") or "") not in BAND_TEMPLATES)
    total = sum(float(it.get("score", 0)) for it in items if not it.get("quantitative")) or 0
    for it in items:
        if it.get("quantitative"): continue
        sl = covered.get(it["id"], [])
        if not sl: fails.append(f"평가항목 {it['id']} {it.get('name', '')} 귀속 슬라이드 0장")
        elif total and body_n:
            sr, wr = float(it.get("score", 0)) / total, len(sl) / body_n
            if wr <= sr / 2 or wr >= sr * 2: warns.append(f"평가항목 {it['id']} 배점 비중 {sr:.0%} 대비 슬라이드 비중 {wr:.0%}")
    # Task 전수 대응
    tasks = rfp.get("tasks", [])
    mtasks = rfp.get("moduleTasks", [])
    proposal = str(meta.get("kind") or "").startswith("proposal") or bool(rfp)
    # 계획서와 RFP 장 구조를 그대로 쓰는 유형은 모듈과 Task 검사를 적용하지 않음
    module_free = str(meta.get("structure") or "") in ("plan", "sections") or str(meta.get("taskType") or "") in ("rnd_plan", "nonrnd_bid")
    if proposal and not tasks: fails.append("meta.rfp.tasks 없음: RFP 과업 세부내용 전건을 T1..Tn 으로 등재할 것")
    if proposal and not mtasks and not module_free:
        fails.append("meta.rfp.moduleTasks 없음: 모듈과 Task 설계를 M{n}-T{m} 으로 등재할 것")
    placed = set(t for m in mtasks for t in m.get("rfp", []))
    if module_free:
        # 모듈을 쓰지 않는 유형은 슬라이드의 rfpTasks 로 전수 대응을 확인
        on_slides = set(t for s in slides for t in s.get("rfpTasks", []))
        for t in tasks:
            if t["id"] not in on_slides:
                fails.append(f"RFP 항목 {t['id']} 대응 슬라이드 없음: {t.get('text', '')[:30]}")
    else:
        for t in tasks:
            if t["id"] not in placed: fails.append(f"RFP 과업 {t['id']} 모듈 Task 미배치: {t.get('text', '')[:30]}")
    OVERVIEW_TPL = {"module_overview"} | own_role(geo, "module_overview")
    appear, appear_all = {}, {}
    for s in slides:
        for t in s.get("moduleTasks", []):
            appear_all.setdefault(t, []).append(s.get("id"))
            # 모듈 개요 슬라이드는 Task 나열이므로 수행계획 슬라이드로 세지 않음
            if (s.get("template") or "") not in OVERVIEW_TPL: appear.setdefault(t, []).append(s.get("id"))
    mods = {}
    for m in mtasks:
        if m["id"] not in appear:
            where = " (모듈 개요에만 나열)" if m["id"] in appear_all else ""
            fails.append(f"Task {m['id']} {m.get('title', '')} 수행계획 슬라이드 미출현{where}")
        if track != "rnd" and any(m.get("title", "") == ex for ex in METHODS_EXAMPLE_MODULES) and not m.get("rfpNamed"):
            warns.append(f"비R&D 트랙에서 methods 예시 모듈명 '{m.get('title')}' 문자 일치 (RFP 명칭이면 rfpNamed: true)")
        mods.setdefault(str(m["id"]).split("-")[0], []).append(m)
    # 모듈 개요와 모듈별 분량
    for mod, items in (sorted(mods.items()) if not module_free else []):
        ov = [s for s in slides if (s.get("template") in OVERVIEW_TPL) and any(str(t).startswith(mod + "-") for t in s.get("moduleTasks", []))]
        if not ov: fails.append(f"모듈 {mod} 개요 슬라이드 없음 (module_overview 로 1장 배치)")
        elif len(ov) > 1: fails.append(f"모듈 {mod} 개요 슬라이드 {len(ov)}장 (모듈당 고유 1장)")
        elif len(ov[0].get("moduleTasks", [])) < len(items):
            fails.append(f"모듈 {mod} 개요 슬라이드에 Task {len(ov[0].get('moduleTasks', []))}건만 표기 (설계 {len(items)}건 전건 표기)")
        n_sl = len({sid for m in items for sid in appear.get(m["id"], [])})
        if n_sl < L.get("moduleSlidesMin", 2): warns.append(f"모듈 {mod} 슬라이드 {n_sl}장 (권장 하한 {L.get('moduleSlidesMin', 2)}장)")
        if n_sl > L.get("moduleSlidesMax", 8): warns.append(f"모듈 {mod} 슬라이드 {n_sl}장 (권장 상한 {L.get('moduleSlidesMax', 8)}장)")
    # 번호와 기호 중복: 밴드가 붙이는 번호를 텍스트에서 반복하면 두 번 표시됨
    for sl in slides:
        sec = str(sl.get("section") or "").strip()
        no = str(sl.get("secNo") or "").strip()
        if no and sec.startswith(no):
            warns.append(f"[{sl.get('id')}] 절 번호 중복 (secNo '{no}' 와 section '{sec[:16]}')")
        elif re.match(r"^\d+[.)]\s", sec) and no:
            warns.append(f"[{sl.get('id')}] 절 번호 중복 (section 이 번호로 시작: '{sec[:16]}')")
        for k, v in ((sl.get("slots") or {}).items() if isinstance(sl.get("slots"), dict) else []):
            items = v if isinstance(v, list) else None
            if not items: continue
            lead = [x for x in items if isinstance(x, str) and re.match(r"^\s*([-·•▪○□※*]|\d+[.)])\s", x)]
            if lead:
                warns.append(f"[{sl.get('id')}] 불릿 기호 중복 (슬롯 '{k}' 항목이 기호로 시작: '{lead[0][:16]}')")
                break

    # 모듈 절 제목 표기: 절 번호 뒤 마침표와 중복되지 않도록 [Module N] 형식
    for sl in slides:
        sec = str(sl.get("section") or "")
        if re.match(r"^Module\s*\d+\s*[.·]", sec):
            warns.append(f"[{sl.get('id')}] 모듈 절 제목 '{sec[:20]}' (권장 표기 [Module N] 모듈명)")
        for it in ((sl.get("slots") or {}).get("items") or []):
            if isinstance(it, str) and re.match(r"^Module\s*\d+\s*[.·]", it):
                warns.append(f"[{sl.get('id')}] 목차·간지 모듈 항목 '{it[:20]}' (권장 표기 [Module N] 모듈명)")
                break

    # 대상 지칭어 혼용: 한 발표자료 안에서는 하나로 통일
    SUBJ = ["본 과업", "본 연구", "본 과제", "본 사업", "본 프로젝트", "본 보고서"]
    found = Counter()
    for sl in slides:
        pool = [sl.get("headline") or ""] + [v for _, v in texts_of(sl)]
        for tx in pool:
            for w in SUBJ:
                if w in tx: found[w] += 1
    if len(found) > 1:
        warns.append(f"대상 지칭어 혼용 {dict(found)} (하나로 통일할 것)")
    # 리더 호칭 혼용: 과업마다 부르는 이름이 다르므로 한 발표자료 안에서는 하나로 통일
    LEADER = {
        "총괄": ["총괄책임자", "연구책임자", "과제책임자", "사업책임자", "총괄PM"],
        "품질": ["품질관리자", "품질책임자", "품질담당자"],
    }
    # 커스텀 슬라이드 원문에는 조사 대상 의미의 "연구책임자" 가 있으므로 수행조직과 책임자 프로필 슬라이드만 본다
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
            warns.append(f"{kind} 리더 호칭 혼용 {dict(hit)} (RFP 표기로 하나를 골라 통일할 것)")
    # 제안 외 산출물에 커스텀 슬라이드의 과업 라벨이 남은 경우
    if not proposal:
        for sl in slides:
            for k, v in texts_of(sl):
                if isinstance(v, str) and re.search(r"과업(의|\s|$)", v) and not re.search(r"과업지시서|과업 세부내용|과업 내용", v):
                    warns.append(f"[{sl.get('id')}] 제안 외 산출물에 '과업' 라벨 잔존 ('{v[:14]}') → 대상 지칭어로 치환")
                    break

    # 지칭어를 바꿨는데 본문 라벨에 과업이 남은 경우
    main = found.most_common(1)[0][0] if found else None
    if main and main != "본 과업":
        word = main.replace("본 ", "")
        for sl in slides:
            for k, v in texts_of(sl):
                if isinstance(v, str) and re.search(r"과업(의|\s|$)", v) and not re.search(r"과업지시서|과업 세부내용|과업 내용", v):
                    warns.append(f"[{sl.get('id')}] 본문 라벨에 '과업' 잔존 ('{v[:14]}') → '{word}' 로 치환 검토")
                    break

    for sl in slides:
        if "본 기획" in (sl.get("headline") or ""):
            warns.append(f"[{sl.get('id')}] '본 기획' 표기 (기획연구도 본 연구 또는 본 과업으로 지칭)")

    # 주석을 불릿 항목으로 넣은 경우: 주석 슬롯이나 source 로 옮길 것
    for sl in slides:
        for k, v in texts_of(sl):
            if k in ("note", "notes", "source", "caption", "footnotes"): continue  # 주석 슬롯은 정상
            if isinstance(v, str) and re.match(r"^\s*(※|출처\s*:|자료\s*:|[Ss]ources?\s*:|[Nn]otes?\s*:)", v):
                warns.append(f"[{sl.get('id')}] 본문 항목에 주석 표기 ('{v[:16]}') → note 슬롯이나 source 로 이동 권장")
                break

    # 표의 빈 셀: 병합 의도로 보이는 빈 셀이 merged 지정 없이 남으면 표가 깨져 보임
    for sl in slides:
        sd = sl.get("slots") or {}
        for key in ("rows", "table"):
            tb = sd.get(key)
            rows = tb.get("rows") if isinstance(tb, dict) else tb
            if not isinstance(rows, list) or len(rows) < 2: continue
            if sd.get("merged") or (isinstance(tb, dict) and tb.get("merged")): continue
            ncol = max((len(r) for r in rows if isinstance(r, list)), default=0)
            hit = False
            for c in range(min(ncol, 2)):  # 앞쪽 분류 열만 검사
                blanks = 0
                for r in rows:
                    if not isinstance(r, list) or c >= len(r): continue
                    if str(r[c]).strip() == "": blanks += 1
                if blanks >= 2:
                    warns.append(f"[{sl.get('id')}] 표 {c + 1}열에 빈 셀 {blanks}개 (병합 의도면 merged 로 지정, 아니면 값을 채울 것)")
                    hit = True
                    break
            if hit: break

    # 배경과 목적의 분량: 리드와 근거가 많으면 좌측 셰브론 안에서 넘침
    for sl in slides:
        if (sl.get("template") or "") != "purpose": continue
        leads = ((sl.get("slots") or {}).get("leads") or [])
        subs = sum(len([x for x in (l or {}).get("sub", []) if x]) for l in leads)
        if len(leads) > 4:
            warns.append(f"[{sl.get('id')}] 배경과 목적 리드 {len(leads)}개 (3-4개 권장)")
        elif len(leads) + subs > 12:
            warns.append(f"[{sl.get('id')}] 배경과 목적 항목 {len(leads) + subs}개 (리드와 근거 합계 12개 이하 권장)")

    # 커스텀 슬라이드 슬롯 치환 분량: 원문보다 크게 길어지면 상자를 넘침
    if geo:
        for sl in slides:
            tpl = str(sl.get("template") or "")
            if not tpl.startswith("own:"): continue
            own = own_n.get(int(tpl.split(":")[1]))
            if not own: continue
            atoms = {"".join(r["t"] for p in (a.get("paras") or []) for r in p["runs"]): a for a in own.get("atoms", [])}

            # 아이콘이 있는 장표는 글자 영역이 좁아지므로 폭을 보수적으로 잡음
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
                # 원문보다 줄이 늘고 상자 높이도 넘길 때만 보고
                paras_n = len(v.split("\n"))
                need = ln_new * (pt * 1.15 / 72) + paras_n * 0.04  # 줄 높이와 문단 간격을 합산
                # 빌더의 간격 축소 여지를 고려하여 상자 높이의 125% 를 넘을 때만 보고
                if ln_new > ln_src and need > a["h"] * 1.25:
                    over.append(f"{src[:10]}→{ln_new}줄")
            if over:
                warns.append(f"[{sl.get('id')}] {tpl} 치환 문구가 상자 용량 초과 {over[:3]} (글자 수를 줄이거나 항목 수를 줄일 것. 글꼴 축소로 대응하지 않음)")

    # 배경과 목적 장표의 근거 항목 줄바꿈: 근거가 항목 본문에 붙어 ※ 없이 조판됨 (시각 확인은 SKILL.md 시각 검수 절차가 담당)
    for sl in slides:
        if (sl.get("template") or "") != "purpose": continue
        leads = (sl.get("slots") or {}).get("leads") or []
        if any("\n" in str(x) for l in leads for x in ((l or {}).get("sub") or []) if isinstance(x, str)):
            warns.append(f"[{sl.get('id')}] 배경과 목적의 근거 항목에 줄바꿈 (근거는 note 슬롯으로 옮겨 ※ 를 붙일 것)")

    # 자동 접두 중복: steps 의 title 과 process 의 모듈명에 빌더가 붙이는 접두를 다시 쓰면 두 번 표시됨
    for sl in slides:
        sd = (sl.get("slots") or {})
        if sd.get("stepLabel") == "":
            pass  # 접두를 끈 경우 title 에 자체 번호를 쓸 수 있음
        else:
          for x in (sd.get("steps") or []):
            t = str((x or {}).get("title") or "")
            if re.match(r"^\s*(STEP|Step)\s*\d*[.)]?\s", t) or re.match(r"^\s*\d+[.)]\s", t):
                warns.append(f"[{sl.get('id')}] steps title 에 접두 중복 ('{t[:16]}') → 접두 없이 제목만 기재하거나 stepLabel 을 \"\" 로 지정")
                break
        for x in (sd.get("modules") or [] if (sl.get("template") or "") == "process" else []):
            t = str((x or {}).get("title") or "")
            if re.match(r"^\s*(M\d+|Module\s*\d+)[-.\s]", t):
                warns.append(f"[{sl.get('id')}] process 모듈명에 접두 중복 ('{t[:16]}') → id 필드로 분리")
                break

    # 절 번호 표기: 마침표 없이 숫자만 쓰면 제목과 붙어 보임
    for sl in slides:
        no = str(sl.get("secNo") or "").strip()
        if no and re.fullmatch(r"[0-9IVXivx①-⑮]+", no):
            warns.append(f"[{sl.get('id')}] 절 번호 '{no}' 에 마침표 없음 (빌더가 '{no.lstrip('0') or no}.' 로 보정)")

    # 번호와 제목 사이 공백 누락: "1.목차" 처럼 붙여 쓰면 읽기 나쁨
    for sl in slides:
        cands = [sl.get("section"), sl.get("marker"), sl.get("headline")]
        cands += [v for _, v in texts_of(sl) if isinstance(v, str)]
        for v in cands:
            # 날짜("2023. 2.)"), 소수, 버전 표기는 제외 (번호 뒤 닫는 괄호와 문장부호는 붙여 씀)
            m = re.search(r"(^|\s)(\d{1,2}|[IVX]+|[①-⑮])[.)](?![\d\s)\]}」』,.])\S", v.strip()) if isinstance(v, str) else None
            if m and not re.search(r"\d{4}\.\d|\d\.\d", v):
                # 판정한 위치 앞뒤를 보여 주어 긴 문구에서도 고칠 곳을 찾게 함
                s = v.strip()
                warns.append(f"[{sl.get('id')}] 번호 뒤 공백 없음 ('{s[max(0, m.start(2) - 8):m.end() + 8]}')")
                break

    # task_multi 는 분량 제한을 선언한 경우에만 허용 (묶음 카드 반복은 변별력 결함)
    for sl in slides:
        if (sl.get("template") or "") != "task_multi": continue
        if not meta.get("pageLimit"):
            fails.append(f"[{sl.get('id')}] task_multi 는 분량 제한 과업에서만 사용 (meta.pageLimit 를 지정하거나 Task 마다 개별 슬라이드로 분리)")

    # 본문 슬라이드 전체 다양성: 밴드 슬라이드를 뺀 본문에서 템플릿 종류가 적으면 단조로움
    BAND_TPL = ("cover", "contents", "divider", "end", "digest")
    body_slides = [s for s in slides if (s.get("template") or "") not in BAND_TPL]
    if len(body_slides) >= 8:
        kinds_all = len({tpl_key(s) for s in body_slides})
        need_all = max(3, int(len(body_slides) * L.get("deckVarietyRatio", 0.3)))
        if kinds_all < need_all:
            warns.append(f"본문 슬라이드 {len(body_slides)}장에 템플릿 {kinds_all}종 < 권장 {need_all}종 (같은 구조 반복은 단조로움)")
        top = Counter(tpl_key(s) for s in body_slides).most_common(1)[0]
        if top[1] > len(body_slides) * L.get("deckTemplateShareMax", 0.4):
            warns.append(f"템플릿 '{top[0]}' 이 본문 {top[1]}/{len(body_slides)}장 사용 (한 템플릿 편중)")
        # 불릿만으로 채운 슬라이드 비중: 표와 차트와 도식이 없는 장표가 절반을 넘으면 경고
        text_only_n = [s for s in body_slides if text_only(s)]
        if len(text_only_n) > len(body_slides) * L.get("bulletOnlyShareMax", 0.5):
            warns.append(f"불릿 패널만 쓴 슬라이드 {len(text_only_n)}/{len(body_slides)}장 (표, 차트, 도식으로 전환할 내용을 검토)")
        for ch in {s.get("chapter") for s in body_slides if s.get("chapter")}:
            cs = [s for s in body_slides if s.get("chapter") == ch]
            if len(cs) >= 5 and len({tpl_key(s) for s in cs}) <= 1:
                warns.append(f"장 '{ch}' 의 {len(cs)}장이 한 템플릿 (장 안에서도 구조를 바꿀 것)")

    # Task 슬라이드 다양성: 수행계획 슬라이드가 한 템플릿으로 반복되면 변별력 결함
    task_slides = [s for s in slides if s.get("moduleTasks") and (s.get("template") or "") not in OVERVIEW_TPL]
    if len(task_slides) >= 3:
        tpls = [tpl_key(s) for s in task_slides]
        kinds = len(set(tpls))
        need = max(2, int(len(task_slides) * L.get("taskVarietyRatio", 0.5)))
        if kinds == 1:
            fails.append(f"Task 슬라이드 {len(task_slides)}장이 모두 '{tpls[0]}' 한 구조 (Task 마다 내용에 맞는 템플릿이나 composite 레시피를 선택할 것)")
        elif kinds < need:
            warns.append(f"Task 슬라이드 템플릿 {kinds}종 < 권장 {need}종 (같은 구조 반복은 변별력 저하)")
        for mod, items in sorted(mods.items()):
            ms = [s for s in task_slides if any(str(t).startswith(mod + "-") for t in s.get("moduleTasks", []))]
            if len(ms) >= 3 and len({tpl_key(s) for s in ms}) == 1:
                warns.append(f"모듈 {mod} 의 Task 슬라이드 {len(ms)}장이 같은 템플릿 (모듈 안에서도 구조를 바꿀 것)")

    # Task 슬라이드 묶음 상한: 1장에 Task 1개가 기본, 분량 제한 시 3개까지
    for sl in slides:
        if (sl.get("template") or "") in OVERVIEW_TPL: continue
        n = len(sl.get("moduleTasks", []))
        if n > L.get("tasksPerSlideMax", 4):
            fails.append(f"[{sl.get('id')}] 한 슬라이드에 Task {n}건 (상한 {L.get('tasksPerSlideMax', 4)}건. 슬라이드를 분리할 것)")
        elif n >= 3:
            warns.append(f"[{sl.get('id')}] 한 슬라이드에 Task {n}건 (분량 여유가 있으면 Task 1건 단위로 분리 권장)")
    # Task 연번 결번: 같은 모듈 안에서 T1..Tn 중 슬라이드가 없는 번호를 지목
    for mod, items in sorted(mods.items()):
        nums = []
        for m in items:
            mm = re.search(r"-T(\d+)$", str(m["id"]))
            if mm: nums.append((int(mm.group(1)), m))
        nums.sort()
        for n, m in nums:
            if m["id"] not in appear:
                fails.append(f"{mod}-T{n} '{m.get('title', '')}' 수행계획 슬라이드 결번 (앞뒤 Task 는 존재)")
        seq = [n for n, _ in nums]
        if seq and sorted(seq) != list(range(1, len(seq) + 1)):
            warns.append(f"모듈 {mod} Task 번호 불연속 {seq} (T1 부터 연속 부여 권장)")
    # RFP 과업 대비 Task 축약률
    if tasks and mtasks and len(mtasks) < len(tasks) * 0.6:
        warns.append(f"RFP 과업 {len(tasks)}건 대비 설계 Task {len(mtasks)}건 (통합 사유를 00_strategy.md 에 기록)")
    # 회사 사실 정보 슬라이드는 사용자 확인 근거를 기록
    FACT_TPL = {"staff_card", "features"} | own_role(geo, "company_fact") | own_role(geo, "people_table") | own_role(geo, "pm_profile")
    for sl in slides:
        tpl = sl.get("template") or ""
        if tpl not in FACT_TPL and (sl.get("slots") or {}).get("recipe") not in FACT_RECIPES: continue
        if not sl.get("factSource"):
            warns.append(f"[{sl.get('id')}] 회사 사실 정보 슬라이드에 factSource 없음 (사용자 제공 자료명이나 확인 일자를 기재)")

    # 수행조직도(org)와 투입인력표(staff_card, 투입인력 표)의 정합
    # 인력 인식 형식 1 (인력 칸): 수행조직도의 pm, qa, 팀원 칸, 머리 행에 성명 열이 있는 표의 성명 칸, 라벨이 성명인 행, staff_card 의 name
    #   칸 값 앞의 성명을 직급과 관계없이 읽음 ("김수연 부사장" → 김수연). 두 슬라이드가 같은 기준으로 성명을 읽어야 명단 비교가 성립
    # 인력 인식 형식 2 (자유 문장): "[인력A]" 와 "성명 + 컨설팅 직급" 문자열
    # 영문 성명: 대문자로 시작하는 2-3어절("Jane Kim"). 인력 칸은 앞 성명, 자유 문장은 "Jane Kim, Senior Consultant" 처럼 쉼표 뒤 직급이 붙은 경우만 읽음
    NOT_NAME = r"(?!총괄|품질|자문|담당|참여|연구|프로젝|분야|전문|외부|내부|전담|현장|미정)"
    ROLE_EN = "|".join(map(re.escape, sorted(STAFF_TITLES_EN, key=len, reverse=True)))
    ROLE = "|".join(map(re.escape, sorted(STAFF_TITLES_KO, key=len, reverse=True))) + "|(?i:" + ROLE_EN + ")"
    LATIN_NAME = r"[A-Z][A-Za-z'’.-]+(?:\s[A-Z][A-Za-z'’.-]+){1,2}?"
    NAME = re.compile(r"\[인력[A-Z0-9]*\]|(?<![가-힣])" + NOT_NAME + r"[가-힣]{2,4}(?=\s+(?:" + ROLE + r")(?![가-힣A-Za-z]))"
                      + r"|(?<![A-Za-z])" + LATIN_NAME + r"(?=,\s*(?:" + ROLE_EN + r")\b)")
    LEAD_NAME = re.compile(r"^\s*(\[인력[A-Z0-9]*\]|" + NOT_NAME + r"[가-힣]{2,4})(?=\s|\(|$)")
    LEAD_NAME_EN = re.compile(r"^\s*(" + LATIN_NAME + r")(?=\s*(?:,|\(|$)|\s+(?:" + ROLE_EN + r")\b)")
    # 영문 직급 자체나 직급 낱말로 끝나는 문구("Business Analyst")는 성명으로 보지 않음
    EN_TITLE_TAIL = re.compile(r"\b(?:" + "|".join(sorted({t.split()[-1] for t in STAFF_TITLES_EN})) + r")$")
    NAME_HEAD = re.compile(r"^(성명|이름|name)$", re.I)
    # 띄어 쓴 직급의 앞말(선임 컨설턴트의 선임, 고문 컨설턴트의 고문)이 성명으로 잡히지 않도록 제외
    TITLE_WORDS = {w for t in STAFF_TITLES_KO for w in t.split()} | {"선임", "수석", "책임", "주임", "전임", "시니어", "초빙", "겸임", "고문"}

    def lead_name(v):
        """인력 칸 값의 앞 성명. 병합 정보가 있는 표 셀 사전은 text 를 읽음. 성명이 없으면 None"""
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
                if "role" in v: out.add(lead_name(v.get("name")))  # staff_card 인력
                if NAME_HEAD.match(str(v.get("label", "")).strip()): out.add(lead_name(v.get("text")))  # labeled 블록의 성명 행
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
    if org_sl and not staff_sl: fails.append("수행조직도만 있고 투입인력 슬라이드 없음 (조직도와 투입인력표는 한 세트)")
    if staff_sl and not org_sl: fails.append("투입인력 슬라이드만 있고 수행조직도 없음 (조직도와 투입인력표는 한 세트)")
    if org_sl and staff_sl:
        org_names = set().union(*[names_of(s) for s in org_sl])
        staff_names = set().union(*[names_of(s) for s in staff_sl])
        if org_names and staff_names:
            # 두 슬라이드의 인력 집합은 같은 정보의 다른 표현이므로 완전 일치
            miss = staff_names - org_names
            if miss: fails.append(f"투입인력표의 {sorted(miss)} 이(가) 수행조직도에 미표기 (두 슬라이드의 인력은 완전 일치)")
            extra = org_names - staff_names
            if extra: fails.append(f"수행조직도의 {sorted(extra)} 이(가) 투입인력표에 미표기 (두 슬라이드의 인력은 완전 일치)")
        elif not staff_names:
            warns.append("투입인력 슬라이드에서 인력 항목을 찾지 못함 ([인력A] 형식이나 성명과 직급 형식으로 기재)")
        for st in staff_sl:
            if (st.get("template") or "") not in PEOPLE_OWN: continue
            filled = {int(m.group(1)) for k in (st.get("slots") or {}) for m in [re.match(r"tb1\.r(\d+)c\d+$", k)] if m and str((st.get("slots") or {})[k]).strip()}
            if filled and max(filled) < 11 and len(filled) < max(filled):
                warns.append(f"[{st.get('id')}] 투입인력 표에 중간 빈 행 존재 (행 {sorted(set(range(1, max(filled) + 1)) - filled)})")
        teams = [t for s in org_sl for t in ((s.get("slots") or {}).get("teams") or [])]
        org_mod = set()
        for s in org_sl:
            for t in ((s.get("slots") or {}).get("teams") or []): org_mod.add(str(t.get("name", "")))
            for k, v in (s.get("slots") or {}).items():
                if isinstance(v, str) and re.match(r"^\s*Module\s*\d", v): org_mod.add(v.strip())
        if org_mod and len(org_mod) < len(mods):
            fails.append(f"수행조직도 모듈 상자 {len(org_mod)}개 < 설계 모듈 {len(mods)}개 (모듈 전건을 상자로 표기)")
        if teams and len(teams) > 8: warns.append(f"수행조직도 모듈 상자 {len(teams)}개 (2행 배치 상한 8개)")
    # 섹션대장
    if ledger is not None:
        lids = [x.get("id") for x in ledger.get("slides", [])]
        if lids != ids:
            fails.append(f"섹션대장 슬라이드 목록 불일치: 대장 {len(lids)}장, storyboard {len(ids)}장, 차이 {sorted(set(lids) ^ set(ids))[:6]}")
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
    # 경고도 기본은 실패로 처리. 사유를 적어 통과시키려면 --allow-warn "사유" 를 붙임
    allow = args[args.index("--allow-warn") + 1] if "--allow-warn" in args else None
    if fails:
        sys.exit(1)
    if warns and not allow:
        print("lint: WARN 이 남아 실패로 처리. 조치하거나 --allow-warn \"유지 사유\" 를 붙여 통과시킬 것")
        sys.exit(1)
    if warns and allow:
        print(f"lint: WARN {len(warns)}건 유지 (사유: {allow})")
    sys.exit(0)


if __name__ == "__main__":
    main()
