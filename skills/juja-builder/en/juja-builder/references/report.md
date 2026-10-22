# Pre-Diagnosis Report Path

- The path that writes diagnosis results as of the time before an engagement starts, based on the RFP, in the structure of a final report
- (Purpose) In the diagnosis stage before kickoff, the client's staff check the current state, gaps, and direction (draft), and use the document for advance consultation and internal reporting. It follows the structure of a final report, so it doubles as a draft that previews the final deliverable
- Uses are advance consultation material with the client, base material for the kickoff report, and survey material for proposal preparation
- The output range is the full table of contents or selected chapters. Usually some chapters are produced
- The design order is RFP, diagnosis file, module framework, storyline, table of contents
    + The diagnosis file and the report storyline correspond to the proposal strategy file and the storyline of the proposal path
    + The object of design is the logic that solves the client's problem. The method is the problem-solving methodology of the Diagnosis Design section
- Sections that need field research (questionnaires, interviews, internal data, and so on) are also filled with a preliminary diagnosis from public materials. Field research is designed as the means of verifying the preliminary diagnosis
- For excluded engagements, apply the scope item in the introduction of SKILL.md as is

## Scope of SKILL.md

| Category | SKILL.md sections |
|---|---|
| Applied as is | Usage Notice, Chat Replies, Preparation, the requirement table of RFP Dissection, Module Frameworks by Engagement Type, Module Overview Table, Manuscript Hierarchy, Style of □ Headings, Bracketed Subheadings, Reader-Perspective Writing, Self-Contained Writing, Sentence Discipline, Reusing Source Images, Typesetting, Render Review |
| Replaced by report.md | Procedure, Proposal Strategy (diagnosis file), Chapter Structure, Storyline Finalization, Volume Units, check targets, defaults for table of contents and page numbers |
| Not applied | Scoring table, section ledger, Common Part, Task Description Standard, Placement of the Implementation Structure, the attributed-points criterion of In-Depth Review |

## Procedure

| Step | Output files | Completion condition |
|---|---|---|
| 0 Start | Basic report information in 00_진단서.md | `selftest` PASS, kickoff answers reflected |
| 1 RFP dissection and diagnosis design | 01_요구항목표.md, 00_진단서.md | Requirement items transferred, all sections of the diagnosis file filled (except the reflecting-section column of the utilization design) |
| 2 Structure finalization | 02_모듈총괄표.md, 02_스토리라인.md | Placement section column of the requirement table filled, `check rfp` PASS, user approval after presenting the three files including 00_진단서.md in one turn |
| 3 Source research | 03_자료대장.md | At least one verdict row per hypothesis, figures checked in code |
| 4 Manuscript writing | 원고/NN_chapter-name.md | `check volume --file` PASS for each file |
| 5 Checks | 05_점검기록.md | `check all` PASS, one self-review |
| 6 Typesetting and review | 납품/사전진단보고서.hwpx or .docx | Render review passed |

- The start sequence is dependency installation, securing the renderer, `init workspace --kind report`, `selftest workspace`, `rfp RFP_file workspace`, and kickoff questions
    + `init --kind report` places assets/diagnosis.md as 00_진단서.md
- Ask the items below all at once as kickoff questions
    + Output range. Full table of contents or selected chapters
    + Report title and the real name notation of the client
    + Whether web search is allowed. If not, figures in literature sections are model knowledge values with a reference year and the `[확인]` marker
    + Whether a field research plan exists (survey targets, sample size, survey timing, and so on). If there is no plan, the model writes a draft survey design
    + Delivery format (one of hwpx or docx recommended. Both is allowed after the notice in the SKILL.md Output Types section), whether to insert a cover, band color theme, long-table handling
    + Whether to include a PDF. Not included by default. The approximate rendering notice is in PDF Copy of the SKILL.md Render Review section
    + The judged report type and engagement type. Judge with the TOC example table of the Table of Contents Design section and the SKILL.md Module Frameworks by Engagement Type section
- Step 1 applies the requirement transfer rules of the SKILL.md RFP Dissection section. In a pre-diagnosis report workspace, `rfp` places only the requirement table (no scoring table). After the transfer, fill 00_진단서.md according to the Diagnosis Design section
- Step 2 writes 02_모듈총괄표.md (SKILL.md Module Overview Table section) and 02_스토리라인.md. For 02_스토리라인.md, copy `<SKILL>/assets/report-storyline.md` into the workspace and fill it
    + In the placement section column of the requirement table, enter section numbers (for example 2.1)
    + For requirement items outside the output range, enter `범위 외` (out of scope)
    + Requirement items for execution duties the report does not answer (post-delivery support, training, security pledges, and so on) also get `범위 외`. One line of reason in the remarks column
    + `check rfp` compares placement section values with the section numbers of the table of contents design table in 02_스토리라인.md
    + Presentation and approval are in the Storyline Finalization section
- Steps 3 and 4 can repeat chapter by chapter. After finishing the source research for one chapter, write that chapter's manuscript
- At session handover, read state.json, 00_진단서.md, and 02_스토리라인.md first. Judge whether step 2 is complete from the `(Approval)` line of 02_스토리라인.md

## Diagnosis Design

- Diagnosis design follows one problem-solving methodology. Its steps are problem definition, issue decomposition, prioritization, analysis planning, analysis, synthesis, and communication. The rules below are the detailed rules of each methodology step
- Methodology steps are called by name. Work steps of the Procedure section are called by number. The correspondence of the two and where each is written are in the table below

| Methodology step | Work step | Where it is written |
|---|---|---|
| Problem definition | Step 1 | The Procurement Background, Competitive Landscape, Problem Statement, and Expected Outcomes sections of 00_진단서.md |
| Issue decomposition | Step 1 | The Diagnostic Questions section of 00_진단서.md |
| Prioritization | Step 1 | The priority column of the diagnostic question table in 00_진단서.md |
| Analysis planning | Steps 1 and 2 | The Hypotheses section of 00_진단서.md (step 1), drafts of 02_모듈총괄표.md and 02_스토리라인.md (step 2) |
| Analysis | Step 3 | 03_자료대장.md |
| Synthesis | Step 3 | The final 02_스토리라인.md. Finalize the draft's judgment statements and chapter messages with the analysis results |
| Communication | Steps 1 and 4-6 | The Utilization Design section of 00_진단서.md (step 1), manuscripts (step 4), checks (step 5), typesetting (step 6) |

- (Procurement background) Apply the underlying-need questions of the SKILL.md Proposal Strategy section (procurement circumstances, persuasion targets, negative phenomena). For private companies, use management performance, new business plans, investment schedules, and so on as material for procurement circumstances
- (Competitive landscape) If the client or the target program competes with other actors for limited resources, include a competitive perspective in the problem definition. Resources are customer purchases, national funds, ministry budgets, R&D projects, investment, and so on
    + Cases include competition among local governments for national funds, competition among ministries for budget, competition among research consortia for large R&D projects, revenue businesses of public corporations and agencies, and business growth and technology commercialization of private companies
    + Items to enter are resources and providers, competitors and substitutes, and competitive conditions. Enter only confirmed facts
    + Competitive conditions are the rules of resource allocation. Open-call methods, evaluation criteria, eligibility for procurement, price and entry regulation, and so on
    + Competitive advantages and disadvantages are set up as diagnostic questions and hypotheses. They are confirmed in the competitive analysis of an analysis chapter
- (Problem statement) It consists of situation, problem, key question, and scope and constraints. The problem is the gap between the state the client aims to reach and the situation
    + The grounds for the target state are values confirmed from higher-level plan goals, required levels of institutions, levels of comparison organizations or competitors, customer requirements, and so on
    + A summary of the RFP's background sentences does not count as a problem statement
    + Scope and constraints are the areas the solution covers, excluded areas, and constraints (budget, laws, schedule, and so on). Confirm them from the RFP and the procurement background
    + The key question asks the direction of the solution for the decision the client will make on receiving the report. For example "2단계 사업의 지원 대상과 규모는 무엇인가" (what are the support targets and scale of the phase 2 program). The answer goes in the direction (draft) section. The material for the direction (draft) is the diagnosis results
- (Expected outcomes) Apply the outcome rule of the SKILL.md Proposal Strategy section (specifying target, time, and state)
- (Diagnostic questions) An issue tree that asks why the problem arose. The issue tree of solution directions unfolds in the main engagement after the diagnosis ends
    + The root question is "why did the problem in the problem statement arise". Every diagnostic question asks for causes. Facts about the current state are recorded in 03_자료대장.md as one of supporting (지지), refuting (반증), or background (배경)
    + A sub-question splits the cause candidates of its parent question. Stop unfolding when reaching a cause the client can act on or an external factor the client cannot control
    + The decomposition criterion is one of time, structure, or type for each group of questions under the same parent. Time divides a process with a before-and-after order. For example the order of a workflow or a process from cause to effect. Structure divides a whole into parts. For example the components of an organization, region, or system. Type divides a higher concept into kinds. For example kinds of causes, company size, user types
    + A group has 2-4 questions. Check for overlaps and gaps. Assign a responding module to each question. For a question without a responding module, add a module or delete the question
- (Prioritization) The criteria are the size of the effect on the problem and how far the client can change it
    + The value is one of 상 (high), 중 (medium), and 하 (low). High if both criteria are high, medium if only one is high, low if both are low
    + Assign analysis and volume first to the sections of high questions
    + Difficulty of obtaining data is handled in the data type and analysis method of the hypothesis table
- (Hypotheses) Set an answer first for each leaf diagnostic question. Confirm or reject it with data
    + The answer to a parent question is set in the synthesis step by bundling the verdicts below it
    + Hypotheses are the criterion that sets the scope of data collection
    + The support condition is what the data looks like when it supports the hypothesis. The refutation condition is what the data looks like when it rejects the hypothesis
    + Choose analysis methods from the section for the engagement type in methods.md
- (Utilization design) Writing principles that make the final results usable in the client's decisions. Enter in the order of utilization obstacles, final result requirements, and design principles. The design principles serve as manuscript writing rules for the reflecting sections

## Table of Contents Design

### RFP-First Principle

- The source of the table of contents is the RFP task content. Place every RFP requirement item in the table of contents. Check placement with the placement section column of the requirement table
- The model adjusts the RFP composition to fit the report's logic. Adjustment types are order adjustment, method supplementation, and content correction
    + (Order adjustment) If the RFP's listing order departs from the flow of the Chapter Order section, change the order of the table of contents. For example, if the RFP lists strategy development and internal status analysis before external environment analysis, place them in the order of external environment analysis, internal status analysis, and strategy development
    + (Method supplementation) If the analysis methods the RFP specifies fall short of the engagement purpose, add supplementary methods. Choose them from the SKILL.md Module Frameworks by Engagement Type and methods.md
    + (Content correction) Write factual errors and outdated items in the RFP (abolished systems, reorganized organization names, ended plans, and so on) by the current standard
- Record the adjustments in the RFP Adjustment Log table of 00_진단서.md. Present them together with the table of contents in the step 2 approval request

### TOC Derivation

- Derive the table of contents from the diagnostic questions and RFP requirement items. The order is diagnostic questions, module framework, storyline, table of contents
- Chapter and section names follow the notation of the RFP task content. Rewrite names from the module framework and TOC examples in RFP wording. Record the changed notation in the `RFP 용어` (RFP terms) table of 00_진단서.md
- Adjust the number and composition of chapters to the RFP and the engagement scale. Fit the scale by merging, splitting, or omitting chapters
- The basis of the chapter structure is 02_모듈총괄표.md. One Module maps to one or more chapters, and one Task to one section. Split the chapters of modules with many Tasks
    + Take the module framework from the SKILL.md Module Frameworks by Engagement Type table. Check the diagnostic questions each module answers in the responding module column of the diagnostic question table in 00_진단서.md
    + Supplement chapters without modules (engagement overview, conclusion, appendix, and so on) with the section composition table per chapter in the TOC Examples section
- Each section of a chapter that maps to a module has at least one question it answers (diagnostic question, key question) or at least one placed requirement item. Delete sections with neither from the table of contents. Sections of the engagement overview, conclusion, and appendix chapters follow the section composition table per chapter in the TOC Examples section
- Sub-composition of a section goes down to the subsection (1.1.1). Use 가나다 as grouping units when a section has five or more □
- For reports with an institutionally set form (R&D self-evaluation result report, effectiveness analysis report, and so on), the form of that year's guidelines is the table of contents. Apply diagnosis design to the narrative logic inside the form

### Chapter Order

- The chapter order is the flow of the storyline. The conclusion of an earlier chapter is the premise of the next. The grounds of a later chapter are confirmed in earlier chapters
- The flow follows the stream table at the opening of methods.md
    + (Goal-setting stream) The strategic planning type and the informatization planning type. Engagements that develop plans such as master plans, mid- to long-term strategies, development strategies, and informatization strategy plans. It narrows from the environment the client cannot control to the areas the client controls, then moves on to goals and prescriptions. The stages are macro environment, micro environment, internal status, benchmarking, strategy, and implementation plan
    + (Gap-analysis stream) The gap-analysis types of the stream table, including the problem-solving type. Performance analysis, status surveys, demand surveys, institutional improvement, and so on. It proceeds in the order of current state diagnosis, gap against the goal, cause structuring, and alternative design
    + (Business planning type) A flow that adds a goal system to the gap-analysis stream. It proceeds in the order of environment and capability analysis, problems and issues, goal system and logic model, program content, and feasibility review
    + (Composite engagements) Engagements that set goals from the conclusion of a gap analysis. Attach goal-setting chapters after the gap-analysis chapters. For example, a development strategy after performance analysis, or a master plan after a feasibility study
- The stages to include are set by the report's purpose. Keep the order among included stages. Skipping to a non-adjacent stage is allowed
- Facts of an earlier stage narrow the analytical focus of a later stage. For example, policy change leads to market requirements, and market requirements lead to the client's capability gaps
- An institutional introduction (history, organization, budget, staff, and so on) may come before the environment analysis. Capability diagnosis (gaps, strengths and weaknesses, and so on) comes after the environment analysis
- Prescriptions (strategies, initiatives, execution, and so on) go in prescription chapters after the analysis chapters. The grounds of prescriptions are the implications of the preceding analysis chapters
- The reverse-order check traces back from execution initiatives to strategies, from strategies to implications, and from implications to analytical facts. For a chapter or section where the grounds break, add grounds to the earlier chapter or delete it

### TOC Examples

- Chapter structure examples from other reports. They are used to check for omissions after table of contents design. The grounds of the table of contents are the diagnostic questions and RFP requirement items
- Judge the report type by the RFP's engagement name and task content. Record the result in the basic report information of 00_진단서.md

| Report type | Identification signals | Chapter structure example | Matching engagement type |
|---|---|---|---|
| Strategic planning | 기본계획, 중장기 전략, 발전전략, 발전방안, 육성계획 | 과업 개요 → 외부 환경 분석 → 내부 역량 분석 → 사례 분석 → 전략 방향 → 추진 과제 → 실행 계획 → 결론 (engagement overview → external environment analysis → internal capability analysis → case analysis → strategic direction → initiatives → action plan → conclusion) | Strategic planning type |
| Business planning | 신규사업 기획, 사전기획, 타당성 검토 | 사업 개요 → 외부 환경 분석 → 내부 역량 분석 → 문제와 해결 방안 → 사업 추진 방향 → 세부사업별 추진 계획 → 추진 체계와 운영 관리 → 소요 자원 → 사업 타당성 분석 → 파급 효과 (program overview → external environment → internal capability → problems and solutions → program direction → plans per sub-program → implementation structure and operation management → required resources → program feasibility analysis → ripple effects) | Business planning type |
| Feasibility study | 건립 타당성, 설립 타당성, 타당성 조사 | 과업 개요 → 현황과 필요성 분석 → 수요 조사와 수요 예측 → 사례 분석 → 사업 타당성 분석 → 결론 → 부록 (engagement overview → status and necessity analysis → demand survey and forecast → case analysis → feasibility analysis → conclusion → appendix) | Business planning type |
| Performance analysis | 성과분석, 성과조사, 사업 평가 | 과업 개요 → 사업 개요와 추진 현황 → 성과 분석 → 개선 방안 → 부록 (engagement overview → program overview and status → performance analysis → improvements → appendix) | Problem-solving type |
| R&D performance evaluation | 자체평가, 효과성 분석, 종료평가 | The form of that year's guidelines. An effectiveness analysis example is 사업 개요 → 성과 활용과 확산 실적 → 사업 효과성 분석 → 부록 (program overview → utilization and diffusion results → program effectiveness analysis → appendix) | R&D performance analysis and evaluation type |
| Informatization planning | 정보화전략계획(ISP), 정보화 마스터플랜 | 과업 개요 → 환경 분석 → 현황 분석 → 목표모델 설계 → 이행계획 → 운영과 발전 방향 (engagement overview → environment analysis → current state analysis → target model design → transition plan → operation and development direction) | Informatization planning type |
| Demand survey | 수요조사, 실태조사, 인식조사 | 과업 개요 → 현황 분석 → 조사 설계 → 조사 결과 분석 → 결론과 제언 → 부록 (engagement overview → current state analysis → survey design → survey result analysis → conclusions and recommendations → appendix) | Problem-solving type |
| Trend analysis | 동향 조사, 기술 조사분석, 산업 분석 | 과업 개요 → 정책 동향 → 기술 동향 → 시장과 산업 동향 → 결론과 시사점 (engagement overview → policy trends → technology trends → market and industry trends → conclusions and implications) | Problem-solving type |

- The criterion dividing external environment and internal capability is whether the actor of the analysis can control it. For national programs, the domestic research base (technology level, researchers, infrastructure, and so on) is internal capability. International and domestic are sub-divisions within the external environment
- Section composition examples per chapter are in the table below

| Chapter | Section composition example |
|---|---|
| 과업 개요 (engagement overview) | Engagement background and necessity, engagement purpose and scope, execution method and structure |
| 외부 환경 분석 (external environment analysis) | A macro environment section (policy, technology, economy, society) and a micro environment section (market and industry, competition and substitutes, customers, investment). International, domestic, and implications subsections in each section |
| 내부 역량 분석 (internal capability analysis) | Track record, resources held (organization, staff, budget, infrastructure), technology level, competitive advantages and disadvantages, synthesis of strengths and weaknesses |
| 사례 분석 (case analysis) | International cases, domestic cases, benchmarking implications |
| 문제와 해결 방안 (problems and solutions) | Problem, goals, beneficiaries, inputs, activities, outputs, outcomes, and assumptions of the logic model |
| 성과 분석 (performance analysis) | Analysis framework (performance types, indicators, measurement methods), results against goals, output per input with comparison groups, ripple effects, success factors and limiting factors |
| 전략 방향 (strategic direction) | SWOT analysis, vision and goals, implementation strategy system |
| 사업 타당성 분석 (program feasibility analysis) | For business planning, scientific and technological, policy, and economic feasibility. For feasibility studies, required budget, economic analysis, ripple effects |
| 결론 (conclusion) | Summary, policy recommendations, follow-up tasks |
| 부록 (appendix) | Questionnaire, calculation formulas, raw data |

## Storyline Finalization

- Write 02_스토리라인.md with the assets/report-storyline.md template. It consists of the framework, the one-line storyline, chapter messages, the table of contents design table, and the field research design
- The framework is the flow of the whole report. If it holds diagnosis and improvement, situation, complication, resolution (SCR). If it asks the client for a decision, situation, complication, question, answer (SCQA). Map chapters to the framework with the stage column of the chapter message table
- Judgment statements carry over unchanged as □ headings of the manuscripts. Apply the writing norms of the SKILL.md Storyline Finalization section (style of □ headings, short sentences with nominal endings, line limits, design language only in side columns)
- Judgment statements of diagnosis sections and preliminary diagnosis sections are expected conclusions derived from hypotheses. Their endings are verdict sentence endings (-으로 나타남, -인 상황, and so on). For □ headings of sections without hypotheses, apply the □ heading rule of the Manuscript Writing section
- The one-line storyline and chapter messages are sentences that end with the client's expected outcomes
- Before presenting, self-check the items below. Fix rows that deviate before presenting
    + For each diagnostic question, a section that answers it exists in the table of contents design table
    + Each hypothesis has a support condition, a refutation condition, and an analysis method
    + Every row of the requirement table has a placement section (`check rfp` PASS)
    + The chapter order matches the flow of the Chapter Order section. No chapter breaks the grounds in the reverse-order check
    + For each design principle of the utilization design, a reflecting section exists in the table of contents design table
    + Module and Task names are identical to 02_모듈총괄표.md
- Present in one turn. Deliver 00_진단서.md, 02_모듈총괄표.md, and 02_스토리라인.md through the file delivery feature
    + At most three items for confirmation. If there is an RFP adjustment log, include it among the confirmation items
- When the user approves, write the date and scope on the `(Approval)` line at the top of 02_스토리라인.md. The condition for starting step 3 is the approval record
- Changes after approval
    + If source research rejects a hypothesis, revise the judgment statement to fit the data. Reflect in the order of the hypothesis table of 00_진단서.md, 02_스토리라인.md, and the manuscripts. Revised judgment statements need user reconfirmation
    + Notation polishing with the same meaning is discretionary. Reflect it in 02_스토리라인.md with the same notation

## Source Research

- The unit of collection is the hypotheses of 00_진단서.md. Look for supporting and refuting grounds together for each hypothesis. Collecting data for only one side tilts the conclusion toward the initial hypothesis
- Data sources are material the user submitted and web pages retrieved in this work. If web search is not allowed, attach a reference year and the `[확인]` marker to model knowledge values
- Search both the Korean web and the English web. Keep search terms to short key words. Cite the original publisher's page
- Record facts in 03_자료대장.md one row at a time
    + One fact per row. For list-type material (policy lists, organization lists, and so on), record one table as one row
    + The verdict is one of 지지 (supporting), 반증 (refuting), or 배경 (background). Background is a current-state fact unrelated to the hypothesis
    + The source is organization (year), material name, and the address of the subpage where the information appears. For figures retrieved from a database, state the database name, query conditions, and retrieval date together

| ID | 가설 | 판정 | 사실 | 수치와 단위 | 기준 시점 | 출처 | 반영 절 |
|---|---|---|---|---|---|---|---|
| F01 | H1 | 지지 | [확인] | [확인] | [확인] | [확인] | [확인] |

- Choose sources by quality
    + (Cite first) Publications and press releases of central ministries and local governments, nationally approved statistics, laws, reports of the National Assembly and the Board of Audit and Inspection, reports of government-funded research institutes and specialized agencies, peer-reviewed papers, reports and statistics of international organizations, the client's public disclosures, and so on
    + (Cite after checking the original source) Press reports, companies' own announcements, association materials, claims raised by only one source, and so on
    + (Do not cite) Open wiki text, personal blogs and social media, compilations without sources, content presumed to be auto-generated, and so on
- If refuting grounds reject a hypothesis, apply the change rules after approval of the Storyline Finalization section
- Each row of the source ledger is reflected in at least one section. For a row with an empty reflecting section, reflect it in a manuscript or delete it from the ledger
- Calculate totals, shares, and rates of change in code. Recheck figures written in sources in code as well

## Manuscript Writing

- One manuscript file per chapter. The file name is `NN_장이름.md` (NN is the two-digit chapter sequence). build merges in file name order
- Heading notation is `#` chapter, `##` section, `###` subsection, and `####` 가나다. The typesetter assigns the numbers (제1장, 1.1, 1.1.1, 가.)
- Caption notation is `<표> title` for tables and `![title](path)` for figures. The typesetter assigns numbers per chapter (<표 2-1>, [그림 2-1])
    + Tables and figures without captions are left out of the number count and the list of tables and list of figures
    + The ❍ before a table states the gist of the table
- Compose analysis sections in the order of current-state facts, comparison and interpretation, and implications. Put implications in an implications subsection (###) at the end of the section
- The style of □ headings is set per subsection (SKILL.md Style of □ Headings section). Trend, status, and list subsections use the keyword type. Implications, diagnosis, and strategy subsections use judgment statements with nominal endings. Diagnosis sections and preliminary diagnosis sections are written as judgment statements throughout
- The subject of the text is the analysis target and its results
    + Verdict endings are the verdict sentence endings in the lexicon.md sentence ending vocabulary (-으로 확인, -으로 집계, -으로 나타남, -인 상황, and so on)
    + Do not use the execution phrasing of proposals (-을 수행, -을 제시, and so on) or proposal-only vocabulary (제안사, 수행 방안, 산출물 시안, and so on)
- The writing mode is set in two steps
    + A section that holds prescriptions for the key question (strategies, initiatives, improvements, recommendations, and so on) is a direction (draft) section
    + Among the other sections, a section with a hypothesis whose data type is field data is a preliminary diagnosis section. All others are diagnosis sections
- Composition by writing mode
    + (Diagnosis section) Written through to the conclusion with public materials. Sources of figures in the body are `[^n]` footnotes. Sources of table figures go on a `자료:` (source) line under the table
    + (Preliminary diagnosis section) Write first what public materials can fill. The composition order is a public material analysis □, an implications □ holding the expected conclusion, an additional confirmation items □, and a survey plan table. The first line of the section is `※ 공개 자료 기준 작성 (현장 조사 결과로 보완 예정)` (written from public materials, to be supplemented with field research results)
    + (Direction (draft) section) Derive the direction from the implications of the diagnosis results. Add (안) at the end of the □ heading. It is finalized after consultation with the client
- Preliminary diagnosis sections use public substitute data for each kind of field data
    + (Internal data) Estimate internal status from the client's disclosures and public documents. ALIO (the public institution management information disclosure system), Clean-Eye (the local public enterprise management information disclosure system), budget and settlement documents, performance reports, audit results and council findings, organization and program status on the institution's website, and so on. State the calculation formula and reference date of estimates on a ※ line under the table
    + (Questionnaire) Present the expected distribution from nationally approved statistics and prior surveys on the same topic. This distribution is the comparison standard for field research. Present a draft item structure (areas, number of items, scales, and so on) under the survey plan table
    + (Interview) Summarize stakeholders' positions from public statements such as National Assembly audit answers, public hearing materials, and press releases. Present draft interview questions under the survey plan table
- The columns of the survey plan table are survey name, target, sample, method, timing, and items to confirm. The source is the field research design table of 02_스토리라인.md. In the items to confirm column, rewrite the hypothesis as an item the survey confirms. For example "지원 기업의 매출 변화 폭" (the range of sales change among supported companies)
- Prefer time series of three years or more for figures. Give the rate of change alongside time series figures
    + `check numbers` rechecks totals and composition ratios
    + Write only code-calculated values for derived figures such as rates of change
- Volume is two or more ❍ and two or more evidence lines per □, and one or more tables or figures per section. `check volume` judges the □ criterion

## Reader-Perspective Writing

- Apply the SKILL.md Reader-Perspective Writing section. The rules below supplement it for the readers of a pre-diagnosis report
- (Readers) The primary readers are the client's staff. The secondary readers are the persuasion targets in 00_진단서.md (budget authorities, supervising agencies, and so on)
    + Staff lift □ and tables out into internal reports and budget explanation material. Write the reference date with figures so they read in their new place as well. For example "2024년 결산 기준" (as of the 2024 settlement)
    + Write figures and indicators in the units and names the client uses. For example fiscal years, budget units, performance indicator names, and program names
- (Tone) Do not write text that teaches or lectures the client or criticizes the client's organization. Staff read such sentences as pointing at their own work
    + (Teaching) Text that explains the client's own duties, systems, and basic concepts. Summarize the client's own status that it already knows (history, organization, program list, and so on) only as far as the persuasion targets need for their judgment. Put the volume into newly confirmed facts, comparison results, and the size of gaps
    + (Lecturing) Statements of obligation and urging such as "반드시 OO해야 함", "OO이 시급", and "인식 전환 필요". Present needed measures as a direction (draft) with grounds
    + (Organizational criticism) Text that evaluates the client's organization, departments, staff, or ways of working. Write shortfalls by the gap description rules below
- (Gap description) What describes a shortfall is the inconvenience users and beneficiaries experience, conditions (facilities, regions, industries), and terms (systems, program composition)
    + Write the foundations already in place and the results achieved first. Write the shortfall against the level the changing environment newly requires
    + Attach comparison targets and figures to judgment words such as "부족" and "한계". Grounds are statistics, comparison figures, stakeholder survey results, and so on. `check tone` judges evaluative words such as "그간 OO에 소홀" and "형식적 운영" as FAIL
    + Write improvement directions with expressions that widen the foundation, such as 보완, 확충, 강화, and 연계
- (Report vocabulary) The vocabulary of the manuscripts is that of the final report the client receives
    + Do not use diagnosis design terms in the manuscripts. 가설, 반증, 검증 가설, 예비 진단, 진단 결과, 지지 조건, 뿌리 질문, 이슈 트리, and so on. Write what field research will confirm as 확인 사항 and what was analyzed as 분석 결과
    + For technical terms of analysis techniques (location quotient, input-output analysis, and so on), add a one-line meaning on a ※ line under their first appearance
- (Implications) Write the implications of analysis sections as matters the client decides or prepares
    + Write the direction (draft) section so that what the client decides in advance consultation is visible. If there are options, present alternatives and selection criteria together
    + Describe the effects of the direction (draft) as changes that happen to the program's beneficiaries such as residents, companies, and users

## Checks

- The report targets of `check all` are requirement placement, volume composition (all manuscripts), tone and vocabulary, figure checks, and leftover confirmation markers (warning only)
- The tone verdict excludes the Module and Task names of 02_모듈총괄표.md and the terms in the `RFP 용어` table of 00_진단서.md. There is no whitelist fixing procedure
    + If actual terms of the engagement's subject work trip the tone verdict (평가위원 in an R&D evaluation engagement, 과제 RFP, and so on), add them to the `RFP 용어` table in their original notation
- For leftover `[확인]`, bundle the list of locations into one turn at step 5 and ask the user. Fill in values received. For places without values, delete the sentence or row after user approval
- Records of the self-review and render review go under the `## 수동 기록` section of 05_점검기록.md
- One self-review. The items are figure integrity, source reliability, logical leaps, reader perspective, and bracketed subheadings from the SKILL.md In-Depth Review section, plus the two items below
    + (Hypothesis response) The □ conclusions of the manuscripts match the verdicts in 03_자료대장.md. Replace judgment statements of rejected hypotheses with the revised versions
    + (Internal vocabulary) The manuscripts meet the report vocabulary rule of the Reader-Perspective Writing section. Framework stage names, final result requirements, and numbers such as Q1 and H1 are also check targets. Where they remain, describe their meaning as actual content. The tone verdict of `check all` does not judge this vocabulary

## Typesetting

- The command is `build workspace --format format --toc --page-number --long-table handling`. Add `--cover` according to the kickoff answer
- Table of contents, page numbers, and divider pages are the default composition of a report. Turn them off only when the user asks
- A divider page is a page before the body of each chapter. It holds only the chapter number and title. The body starts from the first section on the next page. Turn off with `--divider off`
- The list of tables and list of figures follow the table of contents on new pages. They include tables and figures with captions
- Chapter titles are "제N장" bands. Sections 1.1, subsections 1.1.1, items 가.
- Output files are 납품/사전진단보고서.hwpx and .docx
- For partial output, `--chapter-start N` keeps the chapter numbers of the full table of contents. Caption numbers start with the same chapter number
- Inserting the module overview table is optional. Putting one `(삽입: 모듈총괄표)` line in the execution method section of the engagement overview chapter places it there
- Table of contents page numbers are approximate values based on rendering. Check in `TOC page numbers filled n/m` of the build log that all m entries were filled
    + Keep the table of contents even if entries are missing (it is the default composition of a report). Record the missing entries in the final report. Also state that hwpx needs a table of contents refresh in 한/글 and docx needs page numbers filled in Word
- The report title goes on the cover (`--cover`). Without a cover, it is reflected in the file name of the output path (`build workspace 납품/보고서명.hwpx`)

## Final Report

- Record the output range (chapter list), the list of preliminary diagnosis sections and the hypotheses to verify, rejected hypotheses and revised judgment statements, `[확인]` items deleted with user approval, missing table of contents page numbers, and one line on renderer limitations
