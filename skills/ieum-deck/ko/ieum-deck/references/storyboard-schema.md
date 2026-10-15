# storyboard.json 스키마

- 모델이 작성하는 중간 산출물은 storyboard 하나
- build.js 는 같은 storyboard 에서 항상 같은 PPTX 를 조판
- 색상과 서체는 `meta.theme`, `meta.themeColors`, `scripts/tokens.js` 가 정함
- 빌드 착수 조건은 lint.py 종료 코드 0 (WARN 이 남으면 실패)

## meta

| 필드 | 설명 |
|---|---|
| title, author, company | 파일 메타. company 는 회사명 텍스트. 로고가 없으면 표지와 종료 슬라이드에 회사명을 표시 |
| kind | proposal_new, proposal_convert, general(보고회 발표자료, 일반 기획 PPT), report(보고서형 PPT), brief(브리핑 덱). proposal 로 시작하는 값이나 rfp 가 있으면 lint 가 RFP 검사와 배점 검사를 수행 |
| layout | 16:9(기본), A4, 10.83, 4:3. 16:9 보다 좁은 판형은 상자 문구를 본문 폭 비율(A4 87.7%, 10.83 81.2%, 4:3 75.0%)만큼 줄여 작성 |
| headlineStyle | noun(명사형, 기본), polite(존댓말) |
| marker | 마커 도형 모양. square(기본), bar, triangle |
| pointLabel | 수행 Point 밴드의 라벨 문구 (기본 "수행 Point"). 슬라이드별 지정도 가능 |
| labels | 템플릿과 블록의 고정 라벨, 언어 태그, 추가 주석 토큰을 덱 단위로 지정하는 객체. 형식은 {템플릿 또는 블록: {슬롯: 라벨}} (아래 meta.labels 절). 생략하면 한국어 기본 라벨 |
| theme | navy(기본), mono. 사용자 지정 색은 themeColors 로 지정 |
| themeColors | 사용자 지정 테마 색. base 에 기준 색 6자리 색상 코드를 쓰면 빌드가 textMuted 를 뺀 테마 색 전체를 계산 (예: {"base": "1B4332"}). 색 키를 함께 쓰면 기재한 키가 계산값보다 우선 (색 키 목록과 대비 하한은 아래 themeColors 색 키 절). navyRamp 를 쓰지 않으면 차트 계열 색은 최종 navy, navyPastel, navyPastel2 와 계산한 4번째 색으로 구성. 형식 오류는 lint FAIL 과 빌드 오류, 대비 하한 미달은 lint WARN |
| track | 워딩 트랙. rnd, mgmt, general |
| final | true 이면 남은 자리 표기를 lint FAIL 로 검사 (완료 보고 직전에 지정) |
| ownDeck | 커스텀 슬라이드 own-deck.json 경로. storyboard 파일 기준 상대 경로 허용. 미지정 시 환경변수 IEUM_DECK_OWN 사용 (`references/custom-slides.md`) |
| pageLimit | 발주기관이 정한 분량 상한(슬라이드 수). 지정하면 task_multi 묶음 슬라이드를 허용 |
| structure | module(기본), plan(연구개발계획 발표), sections(비R&D 공모 발표, 보고서형 PPT, 브리핑 덱). plan 과 sections 는 모듈과 Task 검사 대신 항목 전수 대응을 검사 |
| chapters | 장 목록. 예: ["Ⅰ. 제안개요", ...] |
| rfp.tasks | [{id: "T1", text, module}] RFP 과업 세부내용 전수. structure 가 plan 이면 계획서 항목, sections 이면 RFP 요구 항목을 등재. ID 는 섹션대장의 내부 추적용 |
| rfp.moduleTasks | [{id: "M1-T2", title, rfp: ["T1", "T3"], rfpNamed}] 제안사가 설계한 Task. rfpNamed 는 title 이 RFP 가 정한 명칭일 때 true (예시 모듈명 검사 예외) |
| rfp.evalItems | [{id: "A-1", name, score, quantitative}] 세부평가항목 |
| rfp.wording | [{standard, variants: []}] 핵심 워딩의 표준 표기와 교체 대상 변형 표기 |

### meta.labels

- 슬라이드마다 반복하던 라벨 슬롯 값(표지 label, 간트 머리, 모듈 개요 행 라벨 등)을 덱 단위로 한 번 지정
- 해석 순서는 슬라이드 슬롯 값, meta.labels, 기본값(`assets/labels.json`)
- 키는 템플릿 또는 composite 블록 이름과 슬롯 이름 (전체 키, 기본값, 영문 예시는 `references/templates.md` 라벨 슬롯 절)
    + common.pointLabel: 수행 Point 밴드 라벨 (meta.pointLabel 이 있으면 meta.pointLabel 우선)
    + language.latin, language.east_asia: PPTX 글자의 언어 태그 (기본 en-US, 한글이 든 run 은 ko-KR)
    + notation.source: 주석 줄로 인식할 토큰 추가 목록 (기본 토큰 ※, 출처:, 자료:, Source:, Note: 는 유지)
- 일부 키만 지정 가능 (생략한 키는 기본값)
- 알 수 없는 이름과 형식 오류는 lint FAIL
- 예: `"labels": {"cover": {"label": "Proposal"}, "contents": {"title": "Contents"}, "gantt": {"groupHead": "Group", "taskHead": "Task", "reportHead": "Reports"}, "language": {"latin": "en-US"}}`

### themeColors 색 키

- 대비 하한은 색 키의 채움 위에 조판하는 글자색과의 명도 대비 (WCAG 기준)

| 색 키 | 쓰이는 자리 | 위에 얹는 글자 | 대비 하한 |
|---|---|---|---|
| navy | 라벨 셀, 셰브론, 마커, 차트 계열 1번째(navyRamp 0번) | 흰색 | 4.5 |
| navyDeep | 결론 밴드, 질문 배너, 지붕과 기단 | 흰색 | 4.5 |
| navyPastel | 피라미드 2층, 깔때기 짙은 띠, 시장 규모 가운데 원, 차트 계열 2번째(navyRamp 1번) | 흰색 | 3.0 |
| navyPastel2 | 피라미드 3층, 깔때기 옅은 띠, 시장 규모 바깥 원, 차트 계열 3번째(navyRamp 2번) | 본문 글자색 | 3.0 |
| navyRamp 3번 | 차트 계열 4번째, 깔때기 맨 위 띠 | 본문 글자색 | 3.0 |
| tintNavy, tintHead, tintBg | 피라미드 4-5층, 머리 칸, 배경 틴트 | 본문 글자색 | 4.5 |
| textMuted | AS-IS 머리 칸, 일정 막대, 출처와 각주와 축 양끝 표기의 글자색 | 흰색 (글자색으로 쓸 때는 흰 바탕) | 3.0 |

- 매트릭스 초점 사분면과 tint 채움에 color navy 를 지정한 격자 칸은 tintHead 채움 위에 navy 글자를 얹음
- navy 와 tintHead 의 대비가 4.5 미만이면 두 요소를 그린 슬라이드에 빌드 경고 (색은 지정값 유지)

## slides[] 공통 필드

| 필드 | 설명 |
|---|---|
| id | 고유 ID. S001 형식 권장 |
| template | 템플릿 이름 (`references/templates.md`). composite 의 구성 견본은 `references/recipes.md`. 커스텀 슬라이드를 등록한 경우 "own:N" |
| secNo | 절 번호. "1." 형식 권장. "01" 이나 "1" 은 빌더가 "1." 로 보정 |
| section, chapter | 밴드의 절 제목과 우측 장 추적기. 모듈 슬라이드의 section 은 `[Module 1] 모듈명` 형식 |
| headline | 결론 문장 1-2줄 (1줄 50자, 2줄 100자. A4 판형 1줄 43자, 10.83 판형 1줄 40자, 4:3 판형 1줄 37자. 한글 환산 글자 수). 밴드 없는 템플릿(cover, contents, divider, end)과 bandMode blank 슬라이드는 생략 |
| accent | 헤드라인 안 강조 어구 1곳 (빨강) |
| marker | 마커 텍스트. 30자(한글 환산) 초과는 lint FAIL. 값을 비우면 마커 도형도 생략 |
| bandMode | 밴드 모드의 강제 지정. full(기본), noMarker, headerOnly, blank |
| slots, panels, blocks | 템플릿별 내용 (`references/templates.md`) |
| source | 출처 행. 문자열 또는 배열 |
| footnotes | 각주 배열. 1), 2) 번호를 자동 부여하여 출처 행 위에 배치 |
| markerNote | 마커 우측 부제 (단위, 기준 시점 등) |
| rfpTasks, moduleTasks, evalItems | 대응 ID 목록. lint 가 전수 대응과 배점 귀속을 검사 |
| allowCount | RFP 가 지정한 개수를 헤드라인에 쓸 때 true (숫자 선언 검사 예외) |
| notes, digest | 발표자 노트, --digest 요약 문장 |
| factSource | 회사 사실 정보의 출처. 사용자 제공 자료명이나 확인 일자 |
| byLayout | 판형 전용 문구. 형식은 `{"4:3": {"slots.regions.1.block.items": [...]}}`. 키는 판형 이름(쉼표로 여러 판형 지정). 값은 점 경로(배열 칸은 0부터 번호)와 교체 값. 빌드 판형과 일치하는 키의 값만 교체. 없는 경로는 build 오류와 lint FAIL |

- 제안 계열 storyboard(kind 가 proposal 로 시작하거나 meta.rfp 가 있는 storyboard)는 meta.rfp.tasks 가 필수 (없으면 lint FAIL)
- 제안 계열 storyboard 의 structure 가 module 이면 meta.rfp.moduleTasks 도 필수 (없으면 lint FAIL)
- 모듈 ID 는 moduleTasks id 의 접두(M1-T2 의 M1)로 판정
- 모듈 개요 슬라이드의 template 은 module_overview 또는 module_overview 역할의 커스텀 슬라이드
- 모듈 개요 슬라이드의 moduleTasks 에는 해당 모듈 Task 전건을 나열
- 모듈 개요 슬라이드의 moduleTasks 는 Task 슬라이드 출현 집계에서 제외
- 수행조직도(org)와 투입인력표는 함께 배치
- lint 가 인식하는 투입인력표는 staff_card, 마커나 절 제목에 "투입인력" 이 들어간 table 과 composite (영문은 "Staffing", "Key staff", "Project staff", "Staff plan")
- lint 는 수행조직도의 pm, qa, 팀원 칸, 머리 행에 성명 열(성명, 이름, Name)이 있는 표의 성명 칸, 라벨이 성명인 행, staff_card 의 name 에서 칸 앞의 성명을 직급과 관계없이 인식
- 그 밖의 문구는 "[인력A]" 와 "성명 + 컨설팅사와 연구기관 직급"(예: 수석컨설턴트, 수석위원, 책임연구원, Senior Manager)을 인식
- 영문 성명은 대문자로 시작하는 2-3어절("Jane Kim")로 인식하고, 자유 문장에서는 "Jane Kim, Senior Consultant" 처럼 쉼표 뒤에 직급이 붙은 경우만 인식

## 섹션대장 ledger.json

- 구조는 {"slides": [{"id", "chapter", "section", "headline", "rfpTasks": [], "moduleTasks": [], "evalItems": [], "template", "status"}]}
- 섹션대장의 슬라이드 목록은 storyboard 슬라이드 목록과 1대1 대응
- lint 는 슬라이드 id 의 목록과 순서만 대조 (어긋나면 FAIL)
- 헤드라인, 대응 ID, 상태 같은 나머지 필드는 storyboard 를 고칠 때 함께 갱신

## 최소 예시

```json
{"meta": {"title": "○○ 용역 제안발표자료", "kind": "proposal_new", "layout": "16:9", "headlineStyle": "noun", "track": "general",
  "rfp": {"tasks": [{"id": "T1", "text": "성과평가 현황 조사"}], "moduleTasks": [{"id": "M1-T1", "title": "현황 조사", "rfp": ["T1"]}],
          "evalItems": [{"id": "A-1", "name": "과업 이해도", "score": 10, "quantitative": false}], "wording": [{"standard": "성과평가 지표", "variants": ["성과지표체계"]}]}},
 "slides": [
  {"id": "S001", "template": "cover", "slots": {"title": "○○ 용역", "client": "발주기관", "date": "2026. 09."}},
  {"id": "S002", "template": "purpose", "secNo": "1.", "section": "배경 및 목적", "chapter": "Ⅰ. 제안개요", "headline": "본 과업은 ...수립을 목적으로 추진", "marker": "과업의 배경 및 목적", "evalItems": ["A-1"], "slots": {"leads": [{"title": "(제도 변화) ...", "sub": ["...", "..."]}], "purpose": "...", "issues": ["(자료 접근) ..."]}},
  {"id": "S003", "template": "composite", "secNo": "1.", "section": "[Module 1] 현황 조사", "chapter": "Ⅲ. 사업수행계획", "headline": "...", "marker": "이해관계자 면담 설계", "moduleTasks": ["M1-T1"], "rfpTasks": ["T1"], "slots": {"recipe": "interview_plan", "cols": [1, 1, 1], "regions": [{"title": "면담 개요", "block": {"kind": "labeled", "rows": [{"label": "목적", "text": "..."}]}}, {"title": "면담 방식", "block": {"kind": "bullets", "items": ["..."]}}, {"title": "진행 절차", "block": {"kind": "flow", "dir": "v", "nodes": [{"text": "..."}]}}]}},
  {"id": "S010", "template": "task", "secNo": "1.", "section": "[Module 1] 현황 조사", "chapter": "Ⅲ. 사업수행계획", "headline": "...", "marker": "Task 1. 현황 조사", "moduleTasks": ["M1-T1"], "rfpTasks": ["T1"], "slots": {"rows": [["조사 대상", "..."]], "sample": {"items": ["..."]}, "point": "..."}}
 ]}
```
