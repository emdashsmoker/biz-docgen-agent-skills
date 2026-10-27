# 템플릿 목록

- 템플릿은 파라메트릭 템플릿, composite 템플릿, free 템플릿, 커스텀 슬라이드 템플릿(`own:N`)으로 구분
- 파라메트릭 템플릿은 표지, 목차, 배경과 목적, 추진전략, 모듈 개요, 일정, 수행조직처럼 구조가 정해진 슬라이드를 담당
- composite 템플릿은 칸 격자와 블록으로 분석과 방법론 슬라이드를 담당 (구성 견본은 `references/recipes.md` 의 레시피)
- free 템플릿은 템플릿과 레시피로 담기지 않는 도식을 좌표 비율로 직접 배치
- 커스텀 슬라이드 템플릿은 커스텀 슬라이드를 등록한 경우에만 사용 (`references/custom-slides.md`)
- 밴드 필드는 모든 본문 템플릿 공통 (secNo, section, chapter, headline, marker, source, accent)
- 판형은 `meta.layout` 으로 지정
- 판형별 좌표는 빌더가 환산
- 견본의 문구 분량은 16:9 기준 (좁은 판형의 문구 분량은 SKILL.md 디자인 시스템의 판형 항목)
- 일부 견본 슬라이드는 4:3 과 A4 판형 전용 축약 문구를 `byLayout` 에 함께 수록

## 선택 규칙

- 구조가 정해진 슬라이드(표지, 목차, 간지, 배경과 목적, 목표와 범위, 특징, 추진전략, 프로세스, 모듈 개요, 일정, 수행조직)는 해당 파라메트릭 템플릿을 사용
- 분석, 조사 설계, 방법론, 관리 방안은 `references/recipes.md` 에서 용도가 맞는 레시피를 먼저 찾음
- 레시피에 없는 단순 구조(전폭 표, 차트와 시사점, 카드, 단계)는 table, chart_text, chart_two, cards, steps 를 사용
- chart_text 와 chart_two 의 시각자료 자리는 차트 전용
- 시각자료 자리에 표, 도식, 이미지를 둘 슬라이드는 composite 로 조판
- 견본(`assets/proposal-templates.json`, `assets/recipe-demos.json`)의 차트 데이터, 표 값, 항목 문구는 과업 내용으로 교체
- free 템플릿 슬라이드는 발표자료 1건당 3-8장을 권장 (8장 초과는 lint WARN)

## 다양성 기준

- 다양성 기준은 모든 산출 대상에 같은 값으로 적용 (적용 조건은 SKILL.md 슬라이드 다양성 절)
- 같은 구성은 3장까지 연속 배치 가능 (4장 연속부터 lint WARN)
- Task 슬라이드는 Task 마다 다른 구성을 선택 (Task 슬라이드 3장 이상이 모두 같은 구성이면 lint FAIL)
- 본문 구성 종류 수는 본문 슬라이드 수의 30%(최소 3종) 이상 (미만이면 lint WARN)
- 구성 1개의 비중은 본문 슬라이드의 40% 이하 (초과면 lint WARN)

## 표 조판

- 셀 안의 여러 항목은 배열로 기재 (항목이 둘 이상이면 빌더가 불릿과 좌측 정렬을 적용)
- 불릿은 항목 경계를 식별하는 표지이므로 줄바꿈으로 여러 줄이 된 문구도 항목 1개로 셈
- 표기 예: `"rows": [["조사 단계", ["문헌 분석", "통계 검토", "전문가 자문"], "1단계"]]`
- 문자열 안의 줄바꿈도 항목 구분으로 조판 (항목마다 불릿)
- 셀 조판 규칙은 표를 쓰는 모든 템플릿에 공통 (table, task, illustrative, free 와 composite 의 table 블록)
- 열 폭은 열마다 가장 긴 셀 문구의 한 줄 폭으로 자동 산정
    + 자료 열은 숫자 열, 하베이 볼 열, 두 글자 이하 기호 열(역할 부호 등)
    + 같은 종류의 자료 열이 2개 이상 이어지면 같은 폭으로 맞춤
    + 한 줄 폭 합이 표 폭보다 작고 같은 종류 자료 열이 3개 이상 이어지면 남는 폭을 그 묶음에만 나눔 (역할 부호, 연도, 대안처럼 표 본체를 이루는 묶음)
    + 그런 묶음이 없으면 남는 폭을 모든 열에 한 줄 폭 비례로 나눔
    + 한 줄 폭 합이 표 폭보다 크면 긴 열부터 같은 폭으로 축소 (짧은 열은 한 줄 유지, 어절 폭은 보장)
- 열 정렬은 열 단위로 통일
    + 여러 항목 셀이 있는 열은 좌측 정렬
    + 진단 질문 열(문장 끝이 "는가", "인가", "는지" 같은 질문형인 셀이 있는 열)은 좌측 정렬
    + 숫자 열은 자릿수 비교가 쉽도록 우측 정렬
    + 그 외 한 항목 셀만 있는 열은 하베이 볼 열을 포함하여 가운데 정렬
- 한 열의 셀은 모두 한 항목이거나 모두 여러 항목으로 구성 (여러 항목 열의 한 항목 셀은 불릿 없이 좌측 정렬)
- 셀의 세로 정렬은 표 전체를 가운데로 통일
- `colW`(폭 비율)와 `align`(열별 정렬)은 빈 기입 칸처럼 문구와 무관한 폭이나 정렬이 필요할 때만 지정
- 표 글자 채움(열별 한 줄 폭 합이 표 폭에서 차지하는 비율)이 60% 미만이면 빌드 경고
    + 해소 순서는 셀 문구 보강(대상, 기준, 수치 병기), 정보 열 추가(담당, 주기, 기준, 산출물), 칸 폭 축소
    + 자리 표기(`[회사 확인]` 등) 셀이 있는 표는 검사 제외
- 표 셀 값이 ●(보유), ◐(부분 보유), ○(미보유)이면 셀 가운데에 원 도형으로 조판
- 하베이 볼 범례는 `legend` 슬롯(table 템플릿)이나 칸 주석(composite)으로 표기
- 하베이 볼의 원 색은 본문 글자색
- 행 높이는 행마다 글줄 수로 산정한 필요 높이에서 시작하여 남는 높이를 낮은 행부터 같은 높이가 되도록 배분
- 행 높이 상한은 글자만 있는 한 줄 행 0.5인치, 여러 줄 행은 줄 간격 1.3배를 담는 높이(0.8인치 이하), 하베이 볼이 있는 표 0.8인치
- 여러 줄 셀은 행 높이가 남는 만큼 줄 간격을 1.3배까지 넓힘
- 머리 행 높이는 0.4인치 (머리 글이 두 줄이면 그 높이)
- table 과 illustrative 템플릿은 표가 행 높이 상한에 걸려 본문보다 짧으면 제목과 표 묶음을 본문 세로 가운데에 배치
- 같은 값이 이어지는 행이나 열은 앞뒤 행의 관계를 보고 병합 여부를 판단
- 병합은 `merged` 로 지정. 합치는 첫 칸은 `{"text": "기획", "rowspan": 3}` (가로 병합은 `colspan`), 합쳐져 가려지는 칸은 `{"merged": true}`

## 파라메트릭 템플릿

- 나란한 패널(bullets, compare, conclusion, cards, chart_text 의 발견 패널)의 높이 상한은 항목 간격을 18pt 까지 넓힌 높이
- 불릿 상자의 항목 간격은 PowerPoint 줄 높이(글꼴 크기의 1.4배)로 잰 남는 높이 안에서 넓힘
- 패널 묶음과 수행 Point 밴드는 본문 세로 가운데에 배치
- 14pt 패널 제목 바(bullets, compare, conclusion, cards, chart_text 발견 패널, strategy 기둥, features 타일, staff_card 역할)의 높이는 0.42인치 (글줄 위아래 여백 0.09인치)
- 행 라벨 상자(module_overview, task_multi, roadmap)와 내용 상자 사이 간격은 0.14인치
- compare 는 gap 수가 AS-IS 항목 수, TO-BE 항목 수와 같으면 행 대응 비교로 조판
    + 행마다 AS-IS 상자, 격차 화살표, TO-BE 상자를 배치
    + 글자는 항목 14pt Bold, 근거 12pt, 격차 13pt Bold (본문 높이를 넘으면 한 단계씩 축소)
    + 두 상자는 가장 긴 글줄에 맞춘 같은 폭이고 묶음은 본문 가운데에 배치
    + 열 제목은 AS-IS 회색, GAP 연한 테마 색, TO-BE 테마 색 (GAP 제목은 `gapHead` 로 변경)
- bullets, cards, conclusion 패널은 항목 14pt, 근거 12pt 로 조판 (bullets, cards 는 높이가 모자라면 11pt 까지 축소)
    + 패널 폭은 가장 긴 글줄에 맞춘 같은 폭이고 패널 묶음은 본문 가운데에 배치
    + 수행 Point 밴드와 결론 밴드는 패널 묶음과 같은 폭
    + bullets, cards 의 수행 Point 문구가 밴드 안에서 2줄을 넘으면 패널 묶음과 밴드를 함께 넓힘 (상한 본문 폭)
- swot 은 가운데 전략 칸(SO, WO, ST, WT)을 좌우 요인 열보다 넓게 두고 네 전략 칸을 같은 서식으로 조판
    + 네 요인 칸에서 가운데 전략 칸으로 모이는 화살표를 요인 열과 전략 칸 사이에 배치

| 분류 | template | 용도 | slots 필드 | 가변 범위 |
|---|---|---|---|---|
| 표지와 간지 | cover | 표지. 가로선은 제목 위아래에 1개씩. 제목은 두 선 사이 정중앙. client 에는 발주기관명만 기재. client 위치는 clientPos 로 선택 | title, label, date, client, logo, company | - |
| 표지와 간지 | contents | 목차 | items[] | 2-7 |
| 표지와 간지 | divider | 간지 | no("Ⅰ"), title, items[] | 절 1-8 |
| 표지와 간지 | end | 종료 | title, company | - |
| 제안 개요 | purpose | 배경과 목적 | leads[{title, sub[], note}], purpose, issues[], leftHead, rightHead, purposeHead, issueHead, client, clientPos | 리드 2-4. 리드마다 제목 1문장과 근거 2-3항목. 목적 상자 라벨은 purposeHead (기본값 "목적") |
| 제안 개요 | scope | 비전, 목표, 모듈 범위, 산출물 | vision, goal, goalHead, visionTag, scopeTag, outputTag, modules[{title, items[]}], outputs[문구 또는 모듈별 문구 배열] | 모듈 2-5. 목표 라벨 문구는 goalHead (기본값 "본 과업의 최종 목표"). 산출물 행 왼쪽에 OUTPUT 라벨 (구조 라벨 VISION, SCOPE, OUTPUT 은 visionTag, scopeTag, outputTag 로 변경). outputs 가 모듈 수와 같은 길이의 배열 목록이면 모듈 열 아래에 여러 항목 불릿으로 정렬. 문구 목록이면 1-2개는 모듈 열 폭 칸을 가운데 정렬, 3-5개는 한 줄, 6-10개는 줄당 5칸 이하로 두 줄 |
| 제안 개요 | features | 질문 배너와 역량 타일 | question, tiles[{title, items[]}] | 타일 2-4, 타일별 항목 1-4 |
| 제안 개요 | strategy | 지붕(목표), 전략 기둥, 기단(결론)의 집 모양 | goal, strategies[{title, items[], result}], conclusion | 전략 2-4, 전략별 항목 4-5 (기둥 안을 채우는 분량). 기둥은 같은 폭. 지붕과 기단은 기둥 묶음보다 양옆으로 0.2인치 넓음. 층 사이 간격은 0.16인치. 글자는 지붕 16pt(길면 14pt 까지 축소), 기둥 제목과 기단 14pt, 기둥 항목 12pt |
| 제안 개요 | process | 모듈 셰브론과 Task 상자 | modules[{id, title, tasks[]}], idFormat, titleFormat | 모듈 2-7, 모듈별 Task 2-6. 모듈 번호는 id 에 기재 (title 은 모듈명만 기재). id 가 없으면 idFormat (기본값 "Module {n}"), 셰브론 문구는 titleFormat (기본값 "M{n}. {t}"). Task 상자는 마지막 상자 하단을 본문 하단에 맞춰 배분 (상자 간격은 균등 간격의 1.5배 상한). 모듈 사이는 ㄱ자 연결선. 모듈 6개 이상이면 모든 셰브론의 높이와 글꼴을 같은 값으로 자동 조정 |
| 수행계획 | module_overview | 모듈 개요표 | tasks[{title, process[], data[], output[]}], rowLabels | Task 2-6. 산출물이 여럿이면 output 배열에 모두 기재 (여러 항목 불릿) |
| 수행계획 | task | Task 설계표와 실측 표본 | leftHead, head[], rows[[항목, 내용]], sample{head, table 또는 items 또는 image 또는 chart, tag}, point | 행 3-6. 설계표 열 제목은 head (기본값 "항목", "내용"). 표본 꼬리표는 sample.tag (기본값 Sample) |
| 수행계획 | task_multi | Task 묶음 매트릭스 (분량 제한 시) | tasks[{id, title, items[]}], rowLabels[], freeLabel, idFormat, point | Task 2-4. items 는 "라벨 : 값" 형식 (행 정렬 조건). 이 형식이 아닌 항목을 모으는 행의 라벨은 freeLabel (기본값 "주요 내용"). id 가 없으면 idFormat (기본값 "Task {n}") |
| 분석과 비교 | bullets | 패널 1-4열 | panels[{head, items 또는 text, headFill, fill}], point | 열 1-4 |
| 분석과 비교 | table | 전폭 표 | title, legend, head[], rows[][], point | 행 1-16 |
| 분석과 비교 | chart_text | 차트와 시사점 | chartTitle, chart{type, barDir, categories, series, numFmt}, findings[{head, items}] | 발견 1-3. chart 필드는 `references/recipes.md` 의 chart 블록과 같음 |
| 분석과 비교 | chart_two | 2단 차트 | left{title, chart, items}, right{title, chart, items} | - |
| 분석과 비교 | compare | AS-IS, TO-BE, 격차 | asis{head, items}, tobe{head, items}, gap[], gapHead | 항목 2-4. 항목은 20자 안팎의 제목(text)으로 작성하고 근거는 하위 항목(sub) 1-2개로 병기. 격차는 항목별 개선 수단을 10자 안팎으로 기재하여 항목 수와 맞춤 (격차가 한 문장이면 gap 1개로 두 패널 아래 띠에 조판) |
| 분석과 비교 | swot | SWOT | S[], W[], O[], T[], so[], wo[], st[], wt[], labels{S, W, O, T, SO, WO, ST, WT} | 칸별 1-4. 요인 칸 제목은 labels (기본값 "강점 (S)", "약점 (W)", "기회 (O)", "위협 (T)"). 전략 칸 제목도 labels 의 SO, WO, ST, WT 로 변경 |
| 분석과 비교 | cards | 카드 N열 | cards[{title, items 또는 text}], point | 2-8 |
| 분석과 비교 | steps | 셰브론 단계와 설명 | steps[{title, items[]}], stepLabel, point | 3-5. 접두는 stepLabel 로 지정 (기본값 STEP, "" 이면 제목만 표기). 항목 간격은 상자 높이에 맞춰 자동 배분. 설명 상자 높이 상한은 항목 높이의 1.3배. 묶음은 본문 세로 가운데 |
| 분석과 비교 | illustrative | 산출물 예시 | title, table 또는 image, tag | 꼬리표는 tag (기본값 Illustrative) |
| 분석과 비교 | conclusion | 종합과 결론 밴드 | panels[{head, items}], conclusion | 패널 2-4. 패널 항목은 20자 안팎의 판단 문장으로 작성하고 근거 수치는 하위 항목(sub)으로 병기 |
| 일정과 조직 | roadmap | 전략별 연차 로드맵 | periods[], lanes[{title, tasks[{text, from, to}]}], laneHead, note | 레인 2-5. 레인 머리 칸 문구는 laneHead (기본값 "전략"). 레인명은 전략명과 같이 동작 명사로 종결 (`references/strategy.md`) |
| 일정과 조직 | gantt | 추진일정 | months, weeks, groups[{name, tasks[{name, from, to}]}], reports[{name, at}], groupHead, taskHead, reportHead, monthFormat | 6-12개월. 구분 열 머리 문구는 groupHead (기본값 "구분"), 과업 열 머리 문구는 taskHead (기본값 "과업"), 보고 행 묶음 이름은 reportHead (기본값 "보고회"), 월 머리 문구는 monthFormat (기본값 "{n}M"). 행 높이 상한(0.32인치)에 걸려 높이가 남으면 표를 본문 세로 가운데에 배치 |
| 일정과 조직 | org | 수행조직도 | client, clientNote, pm, pmTitle, qa, qaTitle, advisory, advisoryTitle, advisoryNote, teams[{name, members[], share}], note | 모듈 상자 2-8 (7개 이상은 2행 자동 배치). 상자에는 인력만 표기 |
| 일정과 조직 | staff_card | 인력 카드 | people[{role, name, career[], records[], photo}], recordsHead | 2-6 (사용 기준은 4명 이상). 사진이 없으면 사진 열 생략. 실적 띠 라벨은 recordsHead (기본값 "주요 실적") |
| 일정과 조직 | orgchart | 회사 조직도 (대표, 자문위원회, 경영지원, 본부, 팀, 인력 표, 협력 네트워크) | ceo, advisory{name, note}, staff{name, note}, units[{name, teams[]}], people[{label, count, ratio}], peopleHead[], network[], leftHead, rightHead, netHead | 본부 2-8, 본부별 팀 1-6. 남는 높이는 상자 높이, 항목 간격, 계선 길이 순으로 배분. 배분 후 남은 높이만큼 묶음을 세로 가운데로 이동 |
| 자유 구성 | composite | 칸 격자와 블록 (`references/recipes.md`) | recipe, cols 또는 rows, regions[{title 또는 caption, block 또는 blocks, note}], flow, rowFlow, numbered, dividers, point, conclusion | 레시피 견본은 1-6칸 |
| 자유 구성 | free | 좌표 비율 자유 배치 | blocks[{kind, x, y, w, h(0-1 비율), ...}] (슬라이드 최상위 또는 slots 아래) | 발표자료 1건당 3-8장 |
| 자유 구성 | digest | --digest 요약 | (자동) | - |

- 수행조직도와 회사 조직도의 배치 규칙은 SKILL.md 수행조직 절을 따름

## 라벨 슬롯

- 템플릿과 블록의 고정 라벨은 슬라이드 슬롯 값, `meta.labels`, 기본값(한국어) 순으로 해석
    + 슬롯을 비우면 `meta.labels` 의 같은 템플릿(또는 블록)과 슬롯 값을 사용
    + `meta.labels` 에도 없으면 아래 기본값으로 조판 (기본값 표는 `assets/labels.json`)
    + `meta.labels` 를 지정하지 않은 덱은 기존과 같은 한국어 라벨로 조판
- 영문 발표자료와 제안 외 산출물은 덱 공통 라벨을 `meta.labels` 에 한 번 지정하고 슬라이드마다 다른 라벨만 슬롯에 지정
- `meta.labels` 형식은 `{템플릿 또는 블록: {슬롯: 라벨}}`
    + 하위 슬롯은 점 경로 키로 지정 (예: `"task": {"sample.head": "..."}`)
    + 목록 라벨(rowLabels, head, peopleHead)은 기본값과 같은 개수로 지정
    + 객체 라벨(labels)은 키 단위로 병합 (지정한 키만 바뀜)
    + 형식 라벨(idFormat, titleFormat, monthFormat)의 `{n}` 은 번호, `{t}` 는 제목
    + 일부 키만 지정해도 됨 (생략한 키는 기본값)
- 수행 Point 밴드 라벨은 슬라이드 pointLabel, meta.pointLabel, meta.labels.common.pointLabel, 기본값 순
- lint 는 알 수 없는 템플릿, 블록, 슬롯 이름과 값 형식 오류를 FAIL 로 보고 (형식 라벨에 `{n}` 이나 `{t}` 가 빠지면 WARN)

| 템플릿 또는 블록 | 슬롯 | 기본값 |
|---|---|---|
| common | pointLabel (슬라이드 pointLabel 과 meta.pointLabel 이 우선) | 수행 Point |
| common | company (슬라이드 company 와 meta.company 가 우선) | 회사명 |
| cover | label | 제안발표자료 |
| contents | title | 목차 |
| end | title | 감사합니다 |
| purpose | leftHead, rightHead, purposeHead, issueHead | 배경 및 필요성, 과업의 목적, 목적, 주요 이슈 및 해결방안 |
| scope | goalHead, visionTag, scopeTag, outputTag | 본 과업의 최종 목표, VISION, SCOPE, OUTPUT |
| process | idFormat, titleFormat | Module {n}, M{n}. {t} |
| module_overview | rowLabels | 단계, 추진과정, 활용자료, 산출물 |
| task | leftHead, head, sample.head, sample.tag | Task 수행 설계, [항목, 내용], 실측 표본 (※ 시안), Sample |
| task_multi | freeLabel, idFormat | 주요 내용, Task {n} |
| compare | asis.head, tobe.head, gapHead | AS-IS, TO-BE, GAP |
| swot | labels{S, W, O, T, SO, WO, ST, WT} | 강점 (S), 약점 (W), 기회 (O), 위협 (T), SO, WO, ST, WT |
| steps | stepLabel ("" 이면 제목만 표기) | STEP |
| roadmap | laneHead | 전략 |
| gantt | groupHead, taskHead, reportHead, monthFormat | 구분, 과업, 보고회, {n}M |
| org | client, pmTitle, qaTitle, advisoryTitle | 발주기관, 총괄책임자 (PM), 품질관리자 (PL), 자문위원회 |
| staff_card | recordsHead | 주요 실적 |
| orgchart | ceo, leftHead, rightHead, peopleHead, netHead | 대표이사, 조직 구성, 인력 구성, [구분, 인원, 비중], 주요 협력 네트워크 |
| illustrative | title, tag | 참고자료 및 산출물 예시, Illustrative |
| valuechain 블록 | stageLabel, support.label, base.label | 단계, 지원 기능, 공통 기반 |
| porter 블록 | supportLabel, primaryLabel, ownerLabel | 지원 활동, 본원적 활동, 담당 부서 |
| goalsystem 블록 | labels{vision, purpose, goal, performance, strategies, tasks, quant, qual} | 비전, 사업 목적, 사업 목표, 성과 목표, 전략분야, 전략과제 및 세부과제, 정량, 정성 |
| house 블록 | labels{mission, vision, goals, tasks, base} | 미션, 비전, 전략목표, 전략과제, 핵심가치 |
| logicmodel 블록 | labels{issue, goal, beneficiary, input, activity, output, outcome, assumption} | 1. 문제/이슈, 2. 목표, 3. 수혜자, 4. 투입, 5. 활동, 6. 산출, 7. 성과/영향, 8. 가정 |
| canvas 블록 | labels{partners, activities, resources, value, relationships, channels, segments, cost, revenue} | 핵심 파트너, 핵심 활동, 핵심 자원, 가치 제안, 고객 관계, 채널, 고객 세그먼트, 비용 구조, 수익원 |
| language | latin, east_asia | en-US, ko-KR |
| notation | source | [] (추가 토큰 없음) |

- (language) PPTX 글자의 언어 태그 (run 의 lang, 차트의 c:lang)
    + latin 은 일반 run 과 차트의 태그, east_asia 는 한글이 든 run 의 태그
    + finalize.py 가 빌드 기록(<파일명>.build.json)의 값을 적용 (기본값은 기존과 같은 결과)
- (notation) 주석 줄로 인식할 토큰의 추가 목록. 콜론 없이 기재 (예: `["Fuente", "Nota"]`)
    + 기본 토큰(※, 출처:, 자료:, Source:, Note:)은 그대로 인식
    + 추가 토큰도 "토큰:" 형태로 시작하는 항목만 주석으로 조판하고 lint 주석 표기 검사에 포함
- scope 구조 라벨(visionTag, scopeTag, outputTag)은 10pt 로 조판되므로 영문 대문자로 지정 (다른 표기는 check_layout 11pt 하한 WARN)
- 회사명은 내용이므로 `meta.company` 로 지정. 미지정 시 자리 표시는 `common.company` 라벨 (기본 "회사명")
- 라벨 슬롯이 아닌 고정 문구는 내용이 비었을 때만 나타나는 자리 표시와 언어와 무관한 번호 기호
    + 이미지 자리 상자의 문구(이미지, 사진, 표본 화면, 산출물 화면, 로고)와 인력 자리 표기([인력A], [인력])는 내용을 채우면 사라짐
    + 커스텀 슬라이드의 빈 이미지 슬롯 대체 문구([기관명], "접수 → 검토 → 승인 → 처리 → 통보", 원본 문구에 "파쇄" 가 있을 때의 설명 문구)와 빈 차트 슬롯의 견본 항목(항목 A, B, C)도 슬롯을 채우면 사라짐
    + 목차 로마 숫자(Ⅰ-Ⅶ), 원 숫자(①-⑩), 1., 1-1., 1) 번호, ※ 표시는 고정

### 영문 라벨 예시

- 영문 발표자료의 `meta.labels` 전체 예시 (`assets/labels.json` 과 같은 키)
- 일부 슬라이드만 영문인 덱은 영문 슬라이드가 쓰는 템플릿의 라벨만 지정하거나 해당 슬라이드의 슬롯에 지정

```json
{"meta": {"labels": {
 "common": {"pointLabel": "Key point", "company": "Company name"},
 "cover": {"label": "Proposal"},
 "contents": {"title": "Contents"},
 "end": {"title": "Thank you"},
 "purpose": {"leftHead": "Background and need", "rightHead": "Purpose of the project", "purposeHead": "Purpose", "issueHead": "Key issues and solutions"},
 "scope": {"goalHead": "Final goal of the project", "visionTag": "VISION", "scopeTag": "SCOPE", "outputTag": "OUTPUT"},
 "process": {"idFormat": "Module {n}", "titleFormat": "M{n}. {t}"},
 "module_overview": {"rowLabels": ["Stage", "Process", "Data used", "Outputs"]},
 "task": {"leftHead": "Task design", "head": ["Item", "Details"], "sample.head": "Measured sample (※ draft)", "sample.tag": "Sample"},
 "task_multi": {"freeLabel": "Key content", "idFormat": "Task {n}"},
 "compare": {"asis.head": "AS-IS", "tobe.head": "TO-BE", "gapHead": "GAP"},
 "swot": {"labels": {"S": "Strengths (S)", "W": "Weaknesses (W)", "O": "Opportunities (O)", "T": "Threats (T)", "SO": "SO", "WO": "WO", "ST": "ST", "WT": "WT"}},
 "steps": {"stepLabel": "STEP"},
 "roadmap": {"laneHead": "Strategy"},
 "gantt": {"groupHead": "Group", "taskHead": "Task", "reportHead": "Reports", "monthFormat": "M{n}"},
 "org": {"client": "Client", "pmTitle": "Project manager (PM)", "qaTitle": "Quality manager (QM)", "advisoryTitle": "Advisory committee"},
 "staff_card": {"recordsHead": "Key projects"},
 "orgchart": {"ceo": "CEO", "leftHead": "Organization", "rightHead": "Staff", "peopleHead": ["Group", "Staff", "Share"], "netHead": "Partner network"},
 "illustrative": {"title": "Reference and output examples", "tag": "Illustrative"},
 "valuechain": {"stageLabel": "Stage", "support.label": "Support functions", "base.label": "Common base"},
 "porter": {"supportLabel": "Support activities", "primaryLabel": "Primary activities", "ownerLabel": "Owner"},
 "goalsystem": {"labels": {"vision": "Vision", "purpose": "Purpose", "goal": "Goal", "performance": "Performance goals", "strategies": "Strategic areas", "tasks": "Strategic tasks\nand sub-tasks", "quant": "Quant.", "qual": "Qual."}},
 "house": {"labels": {"mission": "Mission", "vision": "Vision", "goals": "Strategic goals", "tasks": "Strategic tasks", "base": "Core values"}},
 "logicmodel": {"labels": {"issue": "1. Problem/issue", "goal": "2. Goal", "beneficiary": "3. Beneficiaries", "input": "4. Inputs", "activity": "5. Activities", "output": "6. Outputs", "outcome": "7. Outcomes/impact", "assumption": "8. Assumptions"}},
 "canvas": {"labels": {"partners": "Key partners", "activities": "Key activities", "resources": "Key resources", "value": "Value propositions", "relationships": "Customer relationships", "channels": "Channels", "segments": "Customer segments", "cost": "Cost structure", "revenue": "Revenue streams"}},
 "language": {"latin": "en-US", "east_asia": "ko-KR"}
}}}
```

## free 블록

- (내용 상자) panel{head, items}, bullets{items, fill, line}, text{text, sz, bold, align, fill, line}, label{text, fill}, box{text, fill, line}
- (데이터) table{head, rows}, chart{type, categories, series, numFmt}
- (흐름) chevron{steps, allChevron}, callout{label, text}, arrow{dir: right 또는 down}, line{color, pt, arrow, dash}
- (기타) image{src, caption, label}, circle{text, fill}, grid{cols, rows, cells[{r, c, span, text, fill: navy 또는 tint}]}
