# Content Models for the Original Part

- When and how much to read is in the reference file table at the opening of SKILL.md. At step 3, read only the section for the one file being written
- Every model comes from compositions widely used in portrait-format qualitative technical proposals
- Examples in code fences are Korean manuscript text as written in manuscripts. Fences mark the extent of an example

## Volume Units

- Volume is set by the number of composition units. Filling the composition units below reaches the usual proposal volume

| Unit | Lower-bound composition | How to fill |
|------|-------------------------|-------------|
| □ point | 2 ❍, 2 evidence lines (hyphen or ※), 350 characters | Split the claim into cause and effect. Place one line each of figures, material names, and cases as evidence |
| Background section | 3-5 □ (group 5 into subsections), 2 or more tables or figures | Choose among a higher-level plan citation table, a current statistics table, a pilot project status table, and an institutional history table |
| Features and Strengths section | 3-4 capability claim □, 3 or more track record tables | One named engagement list table per claim |
| Implementation Strategy section | 3-4 strategy □, 2 or more supporting tables or figures | Samples of the method. Choose among a step execution table, a quality indicator table, a usage scenario table, a subcommittee composition table, an execution procedure table, and a diagnosis criteria table |
| Task | 1 or more tables or figures, 900 or more characters of text | Named analysis target lists, filled preliminary survey tables, comparison matrices, diagnosis item tables |

- `check volume` judges the lower bounds of the □ point and Task rows. A shortage of ❍ under □ and a Task without a table are FAIL. Evidence line and character counts are warnings
- Lower bounds at the level of the Background, Features and Strengths, and Implementation Strategy sections are outside code checks. Check them directly when completing a file
- The source of lower and upper bounds is the constants in the settings part of scripts/proposal.py (VOLUME_*, SQUARE_TITLE_MAX, LINE_MAX). If they differ from values in the documents, the settings part rules
- Line limits per level are in the table below. □ and ※ take one typeset line. ❍, hyphen, and ․ take two lines at most. Values are character counts including spaces (confirmed by rhwp rendering, varying by 2-3 characters with word length)

| Level | Lines | Cap |
|-------|-------|-----|
| □ | 1 line | 40 characters |
| ※ | 1 line | 50 characters |
| ❍ | 2 lines | 86 characters |
| Hyphen | 2 lines | 84 characters |
| ․ | 2 lines | 82 characters |

- `check volume` warns on overruns. Resolve an overflowing sentence by splitting it and adding a lower level, or by converting to a table
- When below a lower bound, add units in the order below
    1. Add evidence lines (one line of figures, one of material names, one of cases)
    2. Add ※ notes (term definitions, source dates, calculation bases)
    3. Add tables (preliminary survey results, target lists, criteria tables)
    4. Split □ (separate a cause □ and an effect □)

## Background and Necessity

- Background and Necessity is the WHY section. The role of the section, its framework (SCQA or SCR), and the order narrowing from the macro environment to the client's inside are in the SKILL.md Background Framework section
- A Background □ is a sentence-type judgment statement. For example `□ 정부는 [상위계획명]으로 디지털 트윈을 인프라 관리의 표준 수단으로 지정` (the government designates digital twins as the standard means of infrastructure management through [higher-level plan name])
- ❍ is one fact that composes the □ judgment statement. Write higher-level plan names, system names, and statistics by their real names. The length of one item stays within the ❍ cap of the line-limit table in the Volume Units section
- A hyphen is the evidence for ❍. Write the reference date of figures and the source organization together
- ※ holds term definitions, source dates, and calculation bases. It resolves in advance the points evaluators may question
- One table or figure per □ is recommended. Excerpt the original table of the cited material and attach a source row
- Place underlying-need hypotheses in the C stage. Specify the scale of the client's problem with figures or numbers of findings

### Background □ Examples

```
□ 시설 관리 데이터의 부서별 분산으로 통합 조회가 제한
- 시설관리부의 2차원 도면 관리시스템과 안전점검부의 점검 이력 데이터베이스는 부서별로 개별 운영
    + 두 시스템의 시설 식별자 체계 차이로 동일 시설의 점검 이력과 도면의 동시 조회가 제한
    + 도면 관리시스템은 [연도] 구축 당시의 좌표 체계를 유지하여 GIS 포털과 위치 정합이 불가
- [연도] 내부 감사는 점검 이력 누락 사례 [N]건에 대해 데이터 연계 방안 마련을 요구[^2]
    + 지적 사례의 [N]%는 도면과 점검 이력의 시설 식별자 불일치에서 발생
    + 감사 지적 사항은 [연도] 업무계획의 데이터 연계 과제로 반영
※ 감사 지적 건수는 [기관명] 제공 자료 기준 (착수 후 원본 대조 예정)
```

## Proposal Scope (Engagement Purpose and Objective)

- The first □ of the Proposal Scope section (32) is the engagement purpose and objective. The two items are separated into one ❍ each. Each ❍ is one sentence
- (Purpose ❍) Take the RFP's engagement purpose sentence in its original wording. If it has several sentences, compress them into one ❍ around the key noun phrases (within the ❍ cap of the line-limit table). Remove self-references such as "본 과업은" and "본 연구는". Start with the content of the purpose
    + Hyphens are the details, grounds, or criteria of the purpose, whichever apply. Details are the original wording of the sub-items attached to the RFP's purpose sentence. Grounds are the circumstances in the RFP's background sentences (higher-level plan clauses, system enforcement dates, findings) and the problem the purpose answers. Criteria are conditions that define the purpose (targets of application, scope, higher-level plans it must conform to)
- (Objective ❍) If the RFP has an objective sentence, take it in its original wording. If not, derive it from the purpose
    + Hyphens are detailed objectives or criteria. A detailed objective is one element that composes the objective. The material for derivation is the upper items of the RFP task details. Criteria are the conditions that decide whether the objective is reached (requirements to reflect, who finalizes the work products, completion timing)
    + If no detailed objectives can be derived from the RFP and task content, do not create them. Write only criteria, or end with ❍ and no hyphens
    + If the objective was derived, add the note `※ 목표는 과업 세부내용에서 정리` (objective organized from the task details)
- Definitions of purpose and objective
    + The purpose is the higher-level state or direction the client aims to reach through the engagement's results. Its time range and field follow the RFP. The answer to "why do it". Examples are "행정업무와 대민 서비스의 AI 활용 확산" (spreading AI use in administrative work and public services), "지역 산업 구조의 고도화" (upgrading the regional industrial structure), and "기관 경영 성과의 관리 역량 제고" (strengthening the capacity to manage institutional management performance)
    + The objective is the result the engagement sets out to achieve. The usual objective of research and planning engagements is to develop and derive plans, strategies, and measures by the end of the engagement. The answer to "what, and how far". Examples are "5개년 실행계획서 확정" (finalizing a five-year action plan), "실증사업 추진계획 수립" (developing a demonstration project plan), "육성 전략 수립과 추진과제 발굴" (developing a promotion strategy and discovering initiatives), and "경영평가 등급 향상" (raising the management evaluation grade)
    + There is one purpose. Objectives are the points of arrival toward the purpose. There can be several
    + Put the purpose and the objective once each in their own ❍. Execution methods (surveys, analysis, consultation) are the content of the execution part
- Do not attach figures such as counts, ratios, or numbers of items to the purpose, objectives, detailed objectives, or criteria
    + Allowed numbers are those within plan periods and plan names. Examples are "5개년 전략 수립" and "2027-2031 종합계획 수립"
    + Keep figures in the RFP's original purpose and objective sentences as they are
    + Present survey scale and work product quantities in the Task descriptions and tables of the execution part
- The volume follows the volume of the content the RFP presents. If the RFP's purpose and objective are one sentence each, end with just two ❍
- Warnings on evidence line and character counts (`check volume`) from the □ in this section are not to be resolved
- The following □ is the engagement scope. A composition with one ❍ with a bracketed subheading per scope division is recommended
    + Derive the divisions from the RFP's description of scope. For example (공간적 범위) (spatial scope), (시간적 범위) (temporal scope), (내용적 범위) (content scope)
    + The temporal scope follows the RFP. It usually states the period in which the work products apply (the plan period for a mid- to long-term strategy)
    + The content scope includes all RFP task instruction items in their original wording. Check for omissions by comparing with the upper items of 01_요구항목표.md
    + If the content scope has many items, split them into 1-3 hyphens under ❍. If there are more, develop them in a separate □ with one ❍ and 1-3 hyphens per task item
    + Reflect only the exclusions the RFP states
- The whole section is a descriptive section. □ is the keyword type

### Proposal Scope □ Examples

```
□ 과업 목적 및 목표
- (목적) 기관 행정업무와 대민 서비스의 AI 활용 확산
    + [상위계획명]은 [연도]까지 기관별 AI 활용계획 수립을 규정
    + [기관명] 정보화 기본계획([연도]-[연도])은 [연도] 말에 계획 기간이 만료
    + 후속 정보화 기본계획은 AI 활용 과제의 반영이 필요
- (목표) 2027-2031년 5개년 실행계획서와 연차별 이행과제 목록을 확정
    + (반영 대응표) 상위계획 요구 항목의 기관 반영 여부 판정과 미반영 항목의 보완 방향 제시
    + (연차 로드맵) 이행과제별 담당 부서, 소요 예산, 착수 연도를 5개년으로 배치
    + (확정 기준) 실행계획서는 상위계획 요구 항목을 반영하여 [기관명] 정보화위원회 보고로 확정
※ 목표는 과업 세부내용에서 정리
```

- The first example below is the minimal form when the RFP's purpose and objective are one sentence each. The next two examples are the summary form and the expanded form of the engagement scope

```
□ 과업 목적 및 목표
- (목적) OO도 산업 구조의 고도화와 OO 기술 경쟁력 확보
- (목표) OO산업 테스트베드 구축(안)을 위한 실증사업 추진계획 수립
```

```
□ 과업 범위
- (공간적 범위) OO도 전역
- (시간적 범위) 2027-2031년
- (내용적 범위) 환경분석, 전략수립, 이행과제 발굴, 로드맵 수립
    + 환경분석은 정책, 산업, 기술 동향과 도내 산업 현황을 포함
    + 이행과제는 연차별 소요 예산과 담당 부서를 포함
```

```
□ 내용적 범위
- (환경분석) 국내외 정책, 산업, 기술 동향과 도내 산업 현황 분석
    + 상위계획과 관련 법령 검토
    + 도내 기업 현황과 수요 조사
- (전략수립) 비전과 목표, 분야별 추진전략 도출
    + 전략과제와 핵심 성과지표 설정
- (이행모델 수립) 이행과제 발굴과 연차별 로드맵 수립
    + 이행과제별 소요 예산과 추진체계 제시
```

## Features and Strengths

- Features and Strengths usually repeats a structure of 3-4 capability claims. Each claim comes with an evidence table. The section usually runs 5-10 pages
- Derive capability claims from the differentiation points and implementation strategy of 00_제안전략서.md
- The claim example table is a reference for sentence patterns

| Claim example | □ judgment statement form | Evidence table |
|---------------|---------------------------|----------------|
| Principal investigator expertise | 연구책임자는 N년 경력의 학위 소지자로 분야 A 및 B의 전략기획 전문가 (the PI holds a degree with N years of experience and is a strategic planning expert in fields A and B) | PI track record table (engagement name, period, client, amount) |
| Track record in the [기관명] field | 제안사는 최근 5년간 분야 A 과업 N건을 수행하여 제도와 자료 구조를 이해 (the proposer carried out N field-A engagements in the last five years and understands its systems and data structures) | Track record table by field (year, count, representative engagements) |
| Methodology held | 제안사는 로드맵 수립 및 기술수준 조사의 방법론을 과업 N건에 적용 (the proposer has applied roadmap development and technology level survey methods to N engagements) | Track record table by methodology |
| Tools and data held | 제안사는 특허 및 논문 분석 도구, 정책 문헌 DB, 기관 네트워크를 보유 (the proposer holds patent and paper analysis tools, a policy literature DB, and an institutional network) | Tool list table, advisory network table |
| Similar [기관명] engagements | 제안사는 [기관명] 유관 과업 N건으로 보고 체계 및 자료 접근 경로를 확보 (through N engagements related to [agency name], the proposer has secured reporting lines and data access paths) | [기관명]-related track record table |

- Features and Strengths is the WHAT section. It describes the proposer's held assets (methodology, track record, staff, tools, data) with evidence. The division of roles with the Implementation Strategy section is in the SKILL.md Argument Section Structure section
- The structure is the same for every claim. A □ judgment statement, ❍ elaboration per field (bracketed subheadings by the criteria of the SKILL.md Bracketed Subheadings section), hyphens with named past engagements and the work products secured in them, and a track record table, in that order
- Take the values of track record tables only from 회사자료.md and material the user provides. Cells without data get `[확인]`
- Track record tables run on in several tables by field. Unify widths with `(폭: 실적)` between caption and table
- Make the principal investigator section a separate section (##) when its points are large. Split the field track record tables into 2-3 tables

### Features and Strengths □ Examples

```
□ 연구책임자는 분야 A 및 B의 전략 수립 전문가
- 연구책임자는 N년 경력의 [학위] 소지자로 분야 A와 분야 B의 데이터 활용 전략 수립을 수행
    + [학위] 취득 후 [기관명]에서 N년간 분야 A의 정책연구와 중장기 계획 수립을 담당
    + [연도] [과업명 3]에서 연구책임자로 참여하여 [기관명] 유관기관의 이행과제 목록을 작성
- 분야 A의 기술로드맵, 제도 개선, 생태계 조성 연구를 수행하여 기술, 데이터, 정책을 연계한 기획 역량을 확보
    + [연도] [과업명 1]에서 국내 기업 N개사의 데이터 보유 현황을 조사한 결과표를 보유
    + [연도] [과업명 2]에서 수요조사 문항 설계와 우선순위 평가 기준표를 작성

<표> 연구책임자 분야 A 수행실적
| 과업명 | 과업기간 | 발주기관 | 금액(천원) |
|---|---|---|---|
| [과업명 1] | [기간] | [발주기관] | [확인] |
```

## Implementation Strategy

- Implementation Strategy usually has 3-4 strategies. Each strategy consists of a □ judgment statement, 2-3 ❍, and one supporting table or figure, in that order
- Strategies unfold from the implementation strategy derivation table of 00_제안전략서.md. Unfolding means writing out each row as □ judgment statements and ❍. A table that lists risk factors or values secured by strategy, such as the derivation table, does not go into the manuscript. The materials for derivation are engagement characteristics and risk factors. The derivation table and the reason it stays out of the manuscript are in the SKILL.md Proposal Strategy section
- For each strategy, specify one risk factor from the derivation table and one factual ground about the engagement's subjects. Provide at least one strategy that answers each risk factor. The validity conditions of a strategy (specialization and differentiation) are in the SKILL.md Proposal Strategy section
- The examples below are judgment statements that take the work the RFP and institutions require as a premise. Their content is a specialized measure that fulfills the duty or a measure added on top of it
- The strategy example table is a reference for sentence patterns and composition

| Means | Engagement type | Risk factor | □ judgment statement form | Value secured | Supporting sample |
|---|---|---|---|---|---|
| Design principle | Informatization planning | Staff distrust of generative AI wrong answers | 답변마다 근거 문서를 제시하는 검색 구조로 생성형AI 오답의 불신을 해소 | 원문과 대조되는 신뢰성 (reliability checkable against the original) | Retrieval quality indicator table (indicator, formula, target level) |
| Design principle | Informatization planning | Sensitive materials cannot be sent to external models | 자료 등급별 처리 경로 분리로 국가 망 보안체계 안에서 생성형AI를 활용 | 민감 자료의 외부 유출을 막는 안전성 (safety that prevents sensitive materials from leaking) | Usage scenario table (situation, data grade, tool, processing path) |
| Design principle | Regional industry master plan | Promotion measures indistinguishable from other regions' plans | 지역 보유 역량의 체계적 분석으로 지역 특화형 육성 방안을 도출 | 중앙부처를 설득하는 차별성 (distinctiveness that persuades central ministries) | Capability diagnosis table (item, grounding material, judgment criterion) |
| Design principle | Indicator development | Disconnect between diagnosis results and policy goals | 기술, 정책, 성과의 단계별 대응표로 진단 결과의 정책 활용성을 확보 | 정책과의 정합성 (consistency with policy) | Stage correspondence table (technology, strategic goal, policy outcome, indicator) |
| Design principle | Performance analysis and evaluation | Overinterpreting outcomes without a comparison group | 지원과 비지원 기업을 함께 보는 비교 설계로 성과의 과대 해석을 방지 | 재검증을 견디는 객관성 (objectivity that withstands re-verification) | Comparison group design table (group, selection criteria, size, comparison indicators) |
| Execution activity | Indicator development | Indicator interpretations that differ by technology field | 기술 특성별 분과 위원회 구성으로 지표의 분야별 타당성을 확보 | 분야별 해석가능성 (interpretability by field) | Subcommittee composition table (subcommittee, target field, members, review agenda) |
| Execution activity | Indicator development | Missing, duplicated, or hard-to-interpret indicators | 분과별 지표 사전테스트로 지표의 완결성과 해석가능성을 검증 | 완결성 (completeness) | Pretest design table (subcommittee, mock targets, judgment items) |
| Execution activity | Strategic planning in general | A gap between results and expectations that surfaces at the final report | 착수 초기의 이슈별 산출물 초안 공유로 결과물과 기대의 차이를 해소 | 결과의 예측 가능성 (predictability of results) | Execution procedure table (step, timing, participants, work products) |
| Execution activity | Regional industry promotion | Detailed initiatives disconnected from field demand | 수요기업 및 공급기업의 요구가 일치하는 과제 선별로 실효성을 확보 | 실효성 (effectiveness) | Survey design table (targets, scale, items), council operation table |
| Execution activity | Performance evaluation response | Missing performance evidence within the evaluation submission deadline | 대상사업별 근거자료 선행 정리로 부처 평가 일정 내 대응을 확보 | 일정 내 대응의 확실성 (certainty of an on-time response) | Response schedule per target program (target program, evaluation type, deadline, materials organized in advance) |
| Execution activity | Management strategy | A plan shelved internally after development | 구성원 설명회와 수요 맞춤형 산출물 정리로 전략의 내부 활용을 확보 | 활용성 (usability) | Utilization support plan table (target, method, timing, work products) |

- A judgment statement puts in one sentence the means (a design principle or execution activity) and the risk it resolves or the value it secures. If it exceeds the □ cap of the line-limit table in the Volume Units section, move the elaboration of the means down to ❍
    + For an execution activity, write the design of the activity (composition criteria, target, timing) in the means position
    + Institutional events after the engagement ("예산 반영" (budget reflection), "상급 기관 심의 대응" (response to a supervising agency's review)) are material for section messages
    + Put timing where it qualifies the method, as in "착수 초기의 초안 공유" (sharing drafts early in the engagement) and "기획 일정에 맞춘 시범 적용" (pilot application aligned with the planning schedule). Declaring completion timing of work products is schedule chart content. The reason is in the SKILL.md Argument Section Structure section
- What ❍ describes is the grounds for choosing the means (facts about the engagement's subjects), how the means is implemented (steps, tools, judgment criteria, participants, work products), and the value secured
- A supporting table is a sample of the method. It is evidence of practical understanding that previews what the engagement's final results will look like. Add the note `※ 참고용 예시 (미확정)` under the table
- Implementation Strategy is the HOW section. It describes by what principles and activities the engagement's difficulties are overcome. Introductions of track records, staff, and held tools go in the Features and Strengths section
- When a grounds ❍ cites a held fact, continue with how it is applied in this engagement
- Write strategy names in the language of the engagement
- End strategy names with an action noun that names the measure's action (for example, 수립, 연계, 운영, 제시, 설계, 도출, 반영 in Korean; establishment, linkage, operation, design in English)
    + (Output name ending) A name ending in "지표 체계" (indicator system) or "로드맵" (roadmap) reads as a work product of the Proposal Scope section
    + (Meeting body name ending) A name ending in "자문위원회" (advisory committee) or "실무협의회" (working council) reads as a committee of the implementation structure
    + (Methodology name ending) A name ending in "로직모델" (logic model) or "델파이" (Delphi) reads as a held asset of the Features and Strengths section
    + For example, write "근거 제시형 검색 구조" (evidence-presenting retrieval structure) as "근거 제시형 검색 구조 설계" (design of an evidence-presenting retrieval structure), and "기술 특성별 분과 위원회" (subcommittees by technology trait) as "기술 특성별 분과 위원회 구성" (composition of subcommittees by technology trait)
- Place the advisory member candidate pool table and the per-session operation (draft) table in this section only when the implementation structure content sits in the Implementation Strategy section. The placement criteria are in the SKILL.md Placement of the Implementation Structure section. These tables are implementation structure content. If a committee is a means of the strategy, use the subcommittee composition table as the sample
- Select the advisory member candidate pool table from the advisory network in 회사자료.md or a list the user provides. Write names as `OOO` or `[확인]`

### Implementation Strategy □ Examples

- The first example is a design-principle strategy whose ❍ lines split into grounds, method, and value. The second is an execution-activity strategy composed of two method ❍ and one value ❍

```
□ 표와 그림까지 추출하는 문서 변환으로 HWP 보고서의 수치 누락을 방지
- [기관명]의 핵심 자료는 HWP와 PDF 형식의 보고서와 규정집
    + 본문 표와 그림에 담긴 수치는 일반 텍스트 추출에서 누락되거나 순서가 뒤섞임
    + 수치가 빠진 문서로 만든 검색 자료는 생성형AI 답변의 오류로 이어짐
- 수집, 변환, 정제, 저장의 단계마다 추출 품질을 판정하는 변환 경로를 설계
    + 운영 문서 100건을 표본으로 텍스트 추출률과 표 구조 보존율을 진단
    + 개인정보는 정제 단계에서 가명 처리 후 저장
- 원문의 표와 수치를 보존한 검색 결과로 담당자가 답변을 원문과 대조 가능
    + 수치 질의의 답변에 근거 문서와 쪽 번호를 함께 제시

<표> 단계별 데이터 품질 지표(안)
| 단계 | 지표 | 산식 | 목표 수준 |
|---|---|---|---|
| 수집 | 수집 완전성 | 수집 파일 수 ÷ 대상 파일 수 × 100 | [확인] |
| 변환 | 텍스트 추출률 | 추출 용량 ÷ 원문 추정 용량 × 100 | [확인] |
| 정제 | 비식별 정확도 | 가명 처리한 개인정보 수 ÷ 전체 개인정보 수 × 100 | 100% |
| 활용 | 검색 재현율 | 시험 질의의 상위 5건 안 정답 근거 비율 | [확인] |
※ 참고용 예시 (미확정)
```

```
□ 설문 및 면담으로 확인한 수요를 계획에 담아 이행 단계의 기업 참여를 확보
- 입주기업 300개사 설문으로 애로사항과 지원 수요를 분야별로 집계
    + 설문 문항은 입지, 인력, 규제, 자금 영역의 24문항으로 구성
    + 설문은 온라인 배포와 미응답 기업 유선 독려로 회수율을 확보
- 관리기관 담당자 면담 12회로 설문에서 드러나지 않는 운영 애로를 확인
    + 면담 대상은 관리기관의 입주 지원, 시설 관리, 기업 지원 담당자로 선정
    + 면담에서 확인한 의견은 과제 후보의 실행 가능성 판단에 반영
- 수요가 확인된 과제로 계획을 구성하여 이행 첫해부터 입주기업의 참여를 확보
    + 수요 근거가 없는 과제 후보는 자문위원회 검토 후 제외
    + 제외한 후보와 제외 사유는 과제 후보 목록표로 실무협의회에서 [기관명]과 공유

<표> 조사 설계
| 구분 | 대상 | 규모 | 산출물 |
|---|---|---|---|
| 설문 | 입주기업 | 300개사 | 수요 집계표 |
| 면담 | 관리기관 담당자 | 12회 | 운영 애로 목록 |
```

## Task Description

- Task types (analysis-centered, derivation-centered) and the definition of module and Task purposes are in the references/methods.md Common Standards section
- The column and row composition of the module overview table is in the SKILL.md Task Description Standard section. The examples below fill that specification

### Module Overview Table Example

```
<표> Module 1 개요
(폭: 모듈개요)
| 구분 | Task 1-1. 시스템 실사 | Task 1-2. 담당자 면담 |
|---|---|---|
| 추진과정 | ◦ 시스템 목록 확정<br>◦ 기능과 데이터 항목 대조<br>◦ 현황표 작성 | ◦ 면담 대상 선정<br>◦ 질문지 설계<br>◦ 면담 실시와 정리 |
| 활용자료 | ◦ 시스템 구축 완료보고서 6건<br>◦ 데이터베이스 스키마 | ◦ 부서별 업무분장표<br>◦ 면담 질문지 3영역 24문항 |
| 산출물 | ◦ 시스템 현황표<br>◦ 데이터 항목 대응표 | 면담 결과 보고서 |
```

- A Task places label ❍ lines directly under the band. Label sets are the per-type sets in the methods.md Common Standards section. The kinds of filled tables are in the SKILL.md Task Description Standard section
- Place a filled table under the label the table supports. Before the table, state its conclusion first in one hyphen under that label. This conclusion sentence gives the angle for reading the table
    + For example `    + 사전조사 결과 데이터 유통 단계는 기관별 보유 수준의 편차가 가장 큼` (the preliminary survey shows the largest variation in holdings across organizations at the data distribution stage)
- The author decides which label a filled table supports by the reading flow of the Task
    + Tables that specify targets (named target list tables) go under (분석 대상)
    + Tables and figures that show methods and procedures (item structure tables, diagnosis item tables, criteria tables, methodology application examples) go under (분석 방법), a criteria label, or (수행 절차)
    + Tables that preview the results (preliminary survey result tables, comparison matrices, work product drafts) go under (산출물). The concluding hyphen starts by naming the character of the table, as in "사전조사 결과" (preliminary survey results) or "시안 기준" (per the draft). This start distinguishes it from a description of the work products' composition
    + A table that spans several labels goes under (산출물)
- In a comparison matrix, columns are targets and rows are stages or items. Fill cells with one set of ○ △ × or ● ◐ ○. Give the legend as ※ under the table
- Cells with only one symbol are excluded from cell bullet handling. Such columns are typeset center-aligned
- When web search is allowed, the filled preliminary survey table lists public statistics and published institutional data first. The source of values and the note under the table are in the SKILL.md Task Description Standard section
- A named target list for literature and material surveys has three columns: organization name, material name, and reason for selection. Specify the number of targets within the range that can actually be surveyed

### Task Basic Description Example

```
Task 1-1. 시설 관리 시스템 실사

- (목적) 시스템별 기능과 데이터 항목의 중복과 공백을 확인하여 연계 대상 선정의 판단 자료를 확보
- (분석 대상) 시설 관리 업무에 쓰이는 시스템 6개와 각 시스템의 데이터베이스 스키마
- (분석 방법) 구축 완료보고서의 기능 목록과 운영 화면을 대조하여 현행 기능을 확정
- (산출물) 시스템 현황표, 데이터 항목 대응표
    + (시스템 현황표) 시스템별 구축 연도, 운영 부서, 기능 목록, 데이터 보유량으로 구성
    + (데이터 항목 대응표) 시설 식별자의 일치 여부를 판단 기준으로 작성
    + 두 산출물은 연계 과제 도출의 후보 목록 작성에 활용
```

- The first two hyphens under (산출물) enumerate the composition of each work product and take bracketed subheadings. The third hyphen is the point of use of both work products together and goes at the end of the group without a bracketed subheading
- The scope of the (산출물) line and where to state submission timing are in the methods.md Common Standards section

### Task Filled Table Placement Example

```
Task 1-1. Task 제목

- (목적) ...
- (분석 대상) ...
    + 조사 대상은 대상 분야의 실증 단계가 앞선 국내외 기관으로 선정
<표> 조사 대상 기관
- (분석 방법) ...
- (산출물) ...
    + 사전조사 결과 데이터 유통 단계는 기관별 보유 수준의 편차가 가장 큼
<표> 단계별 보유 현황 사전조사
```

### Task Filled Table Example

```
    + 조사 대상은 대상 분야의 실증 단계가 앞선 국내외 기관으로 선정

<표> 조사 대상 기관
| 구분 | 기관명 | 조사 자료 | 선정 사유 |
|---|---|---|---|
| 국외 | [기관 A] | 공시 자료, 실증 발표 자료 | 대상 분야 대량 실증 착수 |
| 국외 | [기관 B] | 제품 자료, 협력 계약 공시 | 산업 현장 실증 데이터 축적 |
| 국내 | [기관 C] | 공시 자료, 정부과제 성과 | 국내 대표 플랫폼 상용화 사례 |

    + 사전조사 결과 데이터 유통 단계는 기관별 보유 수준의 편차가 가장 큼

<표> 단계별 보유 현황 사전조사
| 단계 | [기관 A] | [기관 B] | [기관 C] |
|---|---|---|---|
| 데이터 수집 | ○ | ○ | ○ |
| 데이터 유통 | △ | ○ | × |
| 서비스 제공 | ○ | ○ | ○ |
※ ○ 자체 보유, △ 협력사 의존, × 미보유
※ 사전조사 결과 (착수 후 [기관명] 자료로 갱신)
```
