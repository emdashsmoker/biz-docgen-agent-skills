# Execution Plan Methods

- When and how much to read is in the reference file table at the opening of SKILL.md. Apply what you read to the engagement type verdict at step 0, framework finalization at step 2, and execution plan writing at step 3
- The frameworks are standard practice widely used in public service contract proposals. The RFP task details take priority over the frameworks
- Compositions that differ from a framework are allowed. Avoid only reversed order (environment analysis after strategy)
- A track classifies how far institutions set the framework. The status of a framework depends on its track

| Track | Types | Status of the framework |
|-------|-------|-------------------------|
| Institution-based | R&D performance analysis and evaluation type, management evaluation response type, R&D business planning within the business planning type | Institutions set the framework and wording. Apply the framework of the type as the default |
| Conditionally institutional | Informatization planning type, non-R&D business planning within the business planning type | The informatization planning type applies institutional procedures if a mandatory ISP applies. Other IT planning is composed within the RFP scope. Non-R&D business planning applies the analysis structure of the applicable guidelines if it is subject to institutional review such as the preliminary feasibility study for fiscal programs. Other planning uses the analysis structure as a reference and is composed to fit the RFP scope and project size |
| Discretionary | Strategic planning type (including management strategy, organizational diagnosis, indicator development, new business discovery), problem-solving type, support program operation type | The framework is a reference example. Modules and Tasks are derived from the RFP task details and key issues |

- Name only the techniques the RFP requires (SWOT, AHP, Delphi, logic model, and so on). Describe other techniques by their execution content without names
- Differences among type frameworks are differences in work product specifications. The thinking structure splits into the goal-setting stream and the gap-analysis stream. The stream is the basis for deciding module order. Stream names are design language (SKILL.md Terms section)

| Stream | Thinking order | Types |
|--------|----------------|-------|
| Goal-setting (strategic planning methodology) | Define the target state, align with higher-level policy, establish the goal system, cascade downward | Strategic planning type, informatization planning type, the goal system and higher-level policy alignment parts of the business planning type |
| Gap analysis (problem-solving methodology) | Establish the current state, derive the gap against the goal, structure causes, design alternatives | Problem-solving type, R&D performance analysis and evaluation type, management evaluation response type, support program operation type, the current state diagnosis and alternative derivation parts of the business planning type |

- In the business planning type the two streams overlap within one engagement. For subjects of institutional review such as the preliminary feasibility study, give large weight to the goal system and higher-level policy alignment
- Judge an engagement that matches no identification signal by its stream
    + An engagement that requires defining a target state takes the strategic planning framework as the default
    + An engagement that requires establishing the causes of a current problem takes the problem-solving framework as the default
    + After applying the default, replace modules according to the RFP task details

# Common Standards

## Purpose of Modules and Tasks

- A purpose is what the work products and activities of that unit supply to the final results of the engagement. The results of a unit are documents and activities. Activities such as running consultative bodies, gathering opinions, advising, and supporting demonstrations also count as results of a unit. Apply the question of the engagement objective down to modules and Tasks (engagement purpose and objective are defined in the content-models.md Proposal Scope section)
    + (Engagement objective) What is secured when the engagement ends
    + (Module purpose) Which part of the final results do this module's work products and activities become, or which part do they ground
    + (Task purpose) Which part of the module's work products do this Task's work products and activities become, or which judgment do they ground
- The ending of a purpose depends on the character of the unit
    + (Analysis character) Analysis of trends, current state, cases, and performance supplies grounds to later stages. Endings are "OO의 근거 확보" (securing grounds for OO), "OO 도출" (deriving OO), "OO에 활용" (used for OO)
    + (Development character) Model design, strategy development, and plan development directly build components of the final results. Endings are "OO 수립" (developing OO), "OO 설계" (designing OO), "OO 확정" (finalizing OO)
    + (Activity character) Running consultative bodies, gathering opinions, expert advice, and supporting demonstrations and training are results in themselves. Endings state what the activity secures ("OO 의견 수렴" (gathering OO opinions), "OO 합의 확보" (securing OO agreement), "OO 타당성 제고" (raising OO validity))
- The sentence pattern is target, action, results of work products and activities, and point of use, in that order. One of each element
    + (Target) The materials and scope to analyze or synthesize. For an activity-character unit, the participants
    + (Action) One of analysis, diagnosis, comparison, synthesis, operation, and gathering. Put method details in the labels after the purpose and in the 추진과정 row of the overview table
    + (Results of work products and activities) The purpose sentence states what the work products contain (implications, factors, criteria, logic, candidate lists) or what the activity secures (opinions, agreement, review results). Put the name of a work product on the (산출물) line and its submission timing in the schedule chart
    + (Point of use) The later stage inside the engagement where the results of work products and activities are used. Describe it by stage name or work product name (number references are covered in the SKILL.md Self-Contained Writing section). Specify down to which judgment of the later stage it serves
- The client's outcomes (defined in the SKILL.md Proposal Strategy section) are the content of the argument sections and section messages. Do not repeat them for every module and Task
    + For a module whose work products serve directly in the client's external persuasion or review response, describe the point of use that far. For example, a module that builds feasibility logic
- One purpose per unit. Split a Task whose purpose divides in two
- Examples
    + (Analysis-character module) 국내외 정책, 산업, 기술 동향을 분석하여 전략 도출의 근거가 되는 기회 요인과 위협 요인을 도출 (analyze domestic and international policy, industry, and technology trends and derive the opportunity and threat factors that ground strategy derivation)
    + (Development-character module) 환경 분석의 시사점과 수요조사 결과를 종합하여 비전, 목표, 추진전략을 수립 (synthesize the implications of the environment analysis and the demand survey results and develop the vision, goals, and implementation strategies)
    + (Analysis-centered Task) 주요 기술 분야의 발전 단계를 분석하여 전략과제 발굴 시 기술 타당성 판단의 근거를 확보 (analyze the development stages of major technology fields and secure grounds for judging technical feasibility when discovering strategic initiatives)
    + (Derivation-centered Task) 후보 과제를 평가 기준으로 선별하여 전략별 세부과제를 확정 (screen candidate initiatives by evaluation criteria and finalize detailed initiatives per strategy)
    + (Activity-character Task) 산학연 전문가 협의체를 운영하여 세부과제 우선순위 평가의 전문성을 확보 (run an industry-academia-research expert council and secure expertise for prioritizing detailed initiatives)

## Task Types

- Types are divided by the nature of the work products. If the work products are the current state of the target (current status, actual conditions, gaps, causes), the Task is analysis-centered. If they are a future direction (implications, strategies, initiatives, indicators, models), it is derivation-centered
- Type names (analysis-centered, derivation-centered) are the author's design language. Keep labels uniform within a section. (목적) and (산출물) are judgment targets of `check density`. Keep their notation
- The definition and scope of (목적) are in the Purpose of Modules and Tasks section above. The scope of (산출물) follows the rules below
    + Write only the names of work products in (산출물)
    + On the hyphen level below it, write the components, judgment criteria, and points of use of the work products
    + Present submission timing only once, in the schedule chart and the work product submission plan table
    + Only when the RFP requires submission timing per Task, give the timing alongside on the (산출물) line

| Type | Character | Label set | Table forms |
|------|-----------|-----------|-------------|
| Analysis-centered | Reveals the current state of the target. Methods are literature and material surveys, interviews and questionnaires, diagnosis and process analysis, data analysis | (목적)(분석 대상)(분석 방법)(산출물) (purpose, analysis targets, analysis method, work products) | Named target lists, preliminary survey results, question area and item structure, diagnosis item tables, current procedure step tables |
| Derivation-centered | Makes implications, strategies, initiatives, and indicators from analysis results | (목적)(활용 자료)(a criteria label fitting the action)(수행 절차)(산출물) (purpose, materials used, criteria, execution procedure, work products) | Selection criteria tables, evaluation criteria (draft), work product drafts |

- An analysis-centered Task specifies the analysis targets (organizations, materials, interviewee ranks, work procedures) and analysis methods by their real names
- Choose the table form to fit the analysis method. The items to specify for interviews and questionnaires are in the Opinion-Gathering Tools section below
- For work whose counts are actually set, specify the scale in figures
- A derivation-centered Task describes judgment criteria and procedures reproducibly
    + (Criteria) What to select or divide by. For example, policy fit, urgency, feasibility, and the grounding materials for judging each criterion
    + The author names the criteria label naturally to fit the Task's action. For example, (선정 기준) (selection criteria) for a Task that picks from candidates, (평가 기준) (evaluation criteria) for a Task that assigns ranks and weights, (설정 기준) (setting criteria) for a Task that sets indicators and target values, and (설계 기준) (design criteria) for a Task that builds models and systems
    + (수행 절차) (execution procedure) The order of candidate generation, first screening, quantitative evaluation, and committee consultation, with the owner of each step
- The tables of a derivation-centered Task are criteria tables or drafts. For example, a priority evaluation criteria table, a strategic initiative candidate list (draft), and an indicator formula table
- Keep label sets uniform per type. Omit elements that do not apply
- The column and row composition of the module overview table is in the SKILL.md Task Description Standard section. The name of the last row is uniformly 산출물

## Committee Design

- Committee design signals practical understanding. Specify the name, composition, sessions, agenda, and the path by which results are reflected
- The standard composition is the table below. If the RFP specifies names, use those names

| Committee | Composition | Role | Usual sessions |
|-----------|-------------|------|----------------|
| 자문위원회 (advisory committee) | 5-9 external experts from industry, academia, and research | Review of results at each stage and advice on direction | 3-4 (after kickoff, before the interim report, before the final report) |
| 분과위원회 (subcommittee) | 3-5 experts per field | Presenting target candidates per field, reviewing the adequacy of classification systems and indicators, reviewing pilot application results | 2 per subcommittee plus written reviews as needed |
| 실무협의회 (working council) | [기관명] staff and the research team | Data requests, decisions on pending issues, confirmation of interim work products | Biweekly or monthly |
| 보고회 (reporting meeting) | [기관명] decision-makers and the research team | Kickoff report, interim report, final report | 3 |

- Present member candidates in a candidate (draft) table. Columns are serial number, category (산, 학, 연, 정: industry, academia, research, government), affiliation, position, and name
- A candidate pool of around 15-20 people is conventional. For small engagements, about twice the committee size
- State affiliations and positions by real names. Add the note `※ 위원은 [기관명]과 협의하여 확정` (members to be finalized in consultation with [agency name])
- The source for selecting candidates is in the SKILL.md Committees section
- If no candidates are secured, describe only the fields and headcount
- The per-session operation table has the columns session, timing, agenda, and point of use of review results (work product name)

```
<표> 자문위원회 차수별 운영(안)

| 회차 | 시기 | 안건 | 결과 반영 |
|---|---|---|---|
| 1차 | 착수 후 3주 | 분석 프레임워크와 조사 설계 검토 | Task 1-2 조사 문항 확정 |
| 2차 | 중간보고 전 | 시사점과 전략 방향 검토 | Task 3-1 전략 후보 수정 |
| 3차 | 최종보고 전 | 실행계획과 지표 검토 | 최종보고서 반영 |
```

- The management part handles minutes and the history of reflecting results. The execution plan states only the points of use

## Opinion-Gathering Tools

| Tool | When it applies | Items to specify |
|------|-----------------|------------------|
| Questionnaire survey | Actual conditions and perceptions, identifying demand | Target group and population size, sample size, item structure (items per area), distribution channel, target response rate, reminder procedure |
| In-depth interview | Establishing causes, how a system actually operates | Interviewee ranks and headcount, sessions, question areas |
| FGI | Confirming disagreements among stakeholders | Group composition criteria, number of groups, participants per session |
| Delphi | Deriving expert consensus (indicators, technology levels, future outlooks) | Panel size, number of rounds, consensus criteria (coefficient of variation, quartiles) |
| AHP | Deriving priorities and weights | Hierarchy structure, number of raters, consistency ratio threshold |
| Demand survey | Initiative discovery (planning-document type) | Submission form items, distribution targets, refinement criteria (duplicates, out of scope, excessive budget) |

- Composing initiatives or indicators through direct derivation alone lacks demand grounds. Add a committee review or demand confirmation procedure
- The figures for scale and procedure are the evidence of the opinion-gathering design

# Strategic Planning Type

## Module Framework

| Module | Content | Work products |
|--------|---------|---------------|
| M1 외부 환경 분석 (external environment analysis) | Select only the items that fit the topic among policy, economic, social, technology, and legal system trends. International first, then domestic | List of environmental change factors |
| M2 내부현황 및 사례 분석 (internal status and case analysis) | Capability diagnosis of the target organization, analysis of leading domestic and international cases | Diagnosis results, case implications |
| M3 비전 및 전략 도출 (vision and strategy derivation) | Synthesis of implications, vision system, strategies and strategic initiatives by field | Vision system diagram, strategic initiative list |
| M4 실행계획 및 로드맵 (action plan and roadmap) | Discovery of implementation initiatives, priorities, roadmap, funding and implementation structure, performance indicators | Implementation initiative cards, roadmap, indicator table |

## Rules by Stage

- (Environment analysis) Facts first. Do not write interpretation, outlook, To-be, or solutions at this stage
- (Internal status) Diagnose strengths and weaknesses together. Reveal the gap between the requirements the environment analysis identified and the internal status. Separate introductory status (history, organization, budget) from capability diagnosis
- (Implications) The stage that links analysis results to strategy. For each implication, state the source of its grounding facts (external, internal, case). Jumping to strategy without implications is a logical leap
- (SWOT) Use internal status implications for strengths and weaknesses. Use external environment implications for opportunities and threats. Use case implications for all four. Cross strategies combine only the two relevant quadrants
- (Gap analysis) A four-column table of As-is, To-be, gap, and resolution strategy. The grounds for To-be are case analysis and higher-level plans
- (Strategy system alignment) Vision, mission, strategies, strategic initiatives, implementation initiatives, and performance indicators inherit numbers as a single system (1. strategy, 1-1. strategic initiative, 1-1-1. implementation initiative)
- Every upper and lower item of the system has a counterpart. Place them so that every implication leads to at least one initiative
- (Regional industry promotion) Place industry specialization (location quotient), company demand surveys, accessibility to anchor institutions and demand sources, and the workforce supply base in M2
- (New business discovery) Narrow candidates in the order of redefining the business, Long List, first screen (market attractiveness, fit with the client, financial feasibility), second screen indicators, new business evaluation, and detailed business plans. Separate activation measures into before and after development scenarios
- (Vision derivation) Reflect higher-level plans and national policy (top-down) together with the common direction of strategies (bottom-up). Present as a three-column table of top-down, bottom-up, and final
- (Priorities) Present evaluation criteria (necessity, urgency, feasibility, ripple effect) and points as a table. Specify the raters and procedure. Close the results with a short-, mid-, and long-term roadmap
- (Ripple effect) Place it in M4 if the RFP requires it. For the input-output analysis formulas, apply the table in the Business Planning Type section

## Priority Evaluation Criteria Example

- Columns: 기준 (criterion), 판단 내용 (what is judged), 배점 (points), 근거 자료 (grounding materials). Rows: policy fit, urgency, feasibility, ripple effect

| 기준 | 판단 내용 | 배점 | 근거 자료 |
|------|-----------|------|-----------|
| 정책 부합성 | 국정과제와 상위계획과의 연계 정도 | 30 | 국정과제, 상위계획 |
| 시급성 | 미추진 시 발생하는 손실의 시점 | 20 | 환경 분석 결과 |
| 실현가능성 | 예산, 인력, 제도 여건 | 30 | 내부현황 진단 |
| 파급효과 | 수혜 범위와 연계 산업 | 20 | 사례 분석 |

- The usual form has the advisory committee or a subcommittee as raters, scores collected through an online survey, and weights derived with AHP

## Composite Management Strategy Engagements

- Mid- to long-term management strategy for public institutions conventionally covers management strategy, organizational diagnosis, and management efficiency together
    + (Management strategy) Environment analysis, resetting the management philosophy system (mission, vision, core values), development strategy, cascading strategic and action initiatives to the department level, priorities and timing, annual performance indicators
    + (Organizational diagnosis and redesign) Job analysis, quantitative and qualitative analysis of workload surveys, calculation and allocation of appropriate headcount, organizational structure reform plan, improvement of delegated authority
    + (Management efficiency) Business portfolio, improvement of management evaluation indicators, ESG, reflection of the government's direction for public institution innovation. Wording for improving management evaluation indicators follows the Management Evaluation Response Type section
- Organization and HR engagements (organizational diagnosis, rank structure, headcount calculation) proceed in the order of job analysis, span of control analysis, benchmarking of similar institutions, redesign plan, and staged implementation plan
- Indicator development engagements (an institution's internal evaluation system) run from analysis of internal and external evaluation systems to institutional improvement plans
    + Derive the indicator candidate pool through stakeholder interviews. Verify validity and measurability with an expert survey and AHP weights
    + After writing indicator definition sheets (definition, formula, weight, measurement method), present a pilot application and institutional improvement plans. Place output indicators and outcome indicators separately

# Business Planning Type

## Logic Model

- Place the cells of the logic model in the order of problems and issues, program goals, inputs, activities (detailed activities), outputs, outcomes, and impacts
- Each link between two adjacent cells is subject to verification. Without the earlier cell, the later cell does not hold
- Put detailed activities (sub-programs, initiative groups) in the activity cell. Put the direct products of activities in the output cell. Put changes that occur among beneficiaries in the outcome cell
- Confusing outputs with outcomes lowers trust in the whole logic model. The number of papers is an output. A change in the localization rate is an outcome

## Goal System Alignment

| Goal system | Matching logic model cell | Alignment check |
|-------------|---------------------------|-----------------|
| Program purpose | Impact | Does it match the state the program aims to change |
| Strategic goal | Outcome | Is it described at the level of beneficiary change |
| Performance goal | Output, short-term outcome | Is it achievable within the program period |
| Performance indicator | Means of measurement | Does it link one-to-one with a performance goal. Is its formula objective |
| Detailed activity | Activity | Can it be specified which performance goal it contributes to |

- An alignment check table filled with actual values in the proposal is evidence that the design is complete
- Indicators meet representativeness and measurability together. State the measurement formula and the source of grounding materials alongside

## Combining with Diagnostic Tools

| Variant | Composition | When it applies |
|---------|-------------|-----------------|
| Full | Issue diagnosis → gap analysis or SWOT → goal setting → logic model | Large new programs, review response, cases requiring grounds for goal derivation |
| Logic-model-centered | Handle problem definition and goal setting inside the logic model | The client provides a logic model template, the program scope is clear |
| Diagnostic-tool | Link goals and initiatives through gap analysis or SWOT without a logic model | Small programs, restructuring plans for existing programs |

- Each variant uses one of gap analysis and SWOT. State the grounds for the choice of variant in one row

## Module Framework

| Module | Content |
|--------|---------|
| M1 정책 및 환경 분석 (policy and environment analysis) | Fit with higher-level plans, policy and technology trends, derivation of problems and issues |
| M2 유사사업 및 지적사항 분석 (analysis of similar programs and findings) | Review of similar programs, duplication and distinctiveness, item-by-item resolution of review findings on prior planning |
| M3 목표체계 및 논리모형 설계 (goal system and logic model design) | Purpose, strategic goals, performance goals, indicators, detailed activities, alignment check |
| M4 타당성 확보 (securing feasibility) | Implementation structure, financing, legal and institutional risks, cost estimation and economic analysis |
| M5 심사 및 보고 대응 (review and reporting response) | Writing the request document, responding to face-to-face meetings and Q&A, managing pending issues |

- The preliminary feasibility study for national R&D programs was abolished by amendments to the National Finance Act and the Framework Act on Science and Technology that passed the National Assembly in January 2026. The preliminary feasibility study for fiscal programs is a current system
    + The successor system for research-type programs is the program planning inspection (사업기획점검). It inspects programs with a total cost of KRW 100 billion or more for about five months from November of the year before the budget request
    + Construction-type programs that build research facilities and equipment (total cost of KRW 100 billion or more and national funding of KRW 50 billion or more) undergo the program implementation review (사업추진심사), design suitability review (설계적합성심사), and major plan change review (주요계획변경심사) stage by stage
- At the start, check the current names and procedures and distinguish the two systems
- Adjust the analytical center of gravity to the character of the program. Ripple logic for securing leading technology, market demand and cost-benefit for industrial application, and utilization and cost-effectiveness for building infrastructure and workforce

## Non-R&D Business Planning

| Program type | Analysis structure |
|------|-----------|
| Construction and facilities | Identify issues → economic analysis (demand, benefits, costs) → policy analysis → balanced regional development → overall evaluation |
| Welfare and income transfer | Identify issues → economic and social environment → adequacy of program design → cost-effectiveness → overall evaluation |
| Informatization | Identify issues → economic analysis (cost-effectiveness if benefits are hard to quantify) → policy analysis → technical analysis (fit with business requirements, suitability of applied technology, adequacy of implementation and operation plans) → overall evaluation |

- Small and medium-sized planning puts the adequacy of program design at the center of the analysis. The check targets are the appropriateness and urgency of program goals, appropriateness of beneficiaries, adequacy of implementation methods, appropriateness of the delivery system, and adequacy of implementation and operation plans

## Economic Analysis Discipline

- Compare implementation with non-implementation (With-Without). Do not use before-and-after comparison
- Count only benefits directly tied to the program's purpose. Exclude sunk costs, reflect opportunity costs, exclude VAT
- Reflect operating costs, reinvestment costs, and residual value in addition to initial investment. State the applied discount rate and analysis period with their grounds
- If benefits are hard to quantify, substitute cost-effectiveness analysis. State the grounds for the substitution. Carry out sensitivity analysis of key variables
- Do calculations in code. Present formulas as two-column tables (the Korean tables below are as written in manuscripts)

<표> 경제성 분석 산식

| 구분 | 산식 |
|---|---|
| 현재가치 | 미래가치 ÷ (1 + 할인율)^경과연수 |
| 순현재가치 | 편익 현재가치 합계 - 비용 현재가치 합계 |
| 편익비용비 | 편익 현재가치 합계 ÷ 비용 현재가치 합계 |
| 내부수익률 | 순현재가치를 0으로 만드는 할인율 |
| 비용효과비 | 효과 한 단위당 비용 |

<표> 산업연관분석 산식

| 구분 | 산식 |
|---|---|
| 생산유발액 | Σ(상품군별 지출액 × 생산유발계수) |
| 부가가치유발액 | Σ(상품군별 지출액 × 부가가치유발계수) |
| 고용유발인원 | Σ(상품군별 지출액 × 고용유발계수), 단위 명/10억원 |

- Use inducement coefficients from the Bank of Korea input-output tables. State the release year and the commodity classification standard alongside. Present the grounds for allocating the total program cost by commodity group as a table
- Do not double-count inducement effects as benefits in the economic analysis
- Presenting large-scale analysis procedures for a small program reads as infeasible. Scale analysis procedures to the program size

# R&D Performance Analysis and Evaluation Type

- The evaluation systems and the common execution procedure assume the performance evaluation system for national R&D programs
- Performance evaluation of non-R&D programs uses different system names and guidelines. Check the evaluation guidelines of the relevant system and replace the evaluation system table
- Steps 1 through 9 of the common execution procedure apply to performance evaluation of both R&D and non-R&D programs
- Institutional management evaluation response follows the Management Evaluation Response Type section

## Evaluation Systems

| R&D evaluation system | Timing | Key work products |
|------|------|-------------|
| Strategic plan development (전략계획서 수립) | New program or end of the plan period | Strategic goals, performance goals, performance indicators, evaluation plan |
| Interim evaluation self-assessment (중간평가 자체평가) | During the program (usually a three-year cycle) | Self-assessment report, comprehensive performance analysis report, representative outcome descriptions |
| Performance management and utilization plan (성과 관리와 활용 계획) | At program end | Performance management and utilization plan, final goal achievement rate |
| Effectiveness analysis (효과성 분석) | Within five years after the end | Effectiveness analysis report, ripple effect estimation |

- Separate guidelines are announced every year for each evaluation system. Before the guidelines are released, prepare by the previous year's guidelines. State in the proposal the order of updating the response after release
- If there are several target programs, present a per-program overview first (purpose, legal basis, period, scale, summary table of performance goals and indicators)
- If there are several evaluation systems, separate modules per system

## Common Execution Procedure

| Step | Content |
|------|---------|
| 1 대상사업 현황분석 (target program status analysis) | Review of the strategic plan and annual reports, review of the linkage of the performance system (purpose, strategic goals, performance goals, indicators) |
| 2 분석 프레임워크 수립 (analysis framework development) | A four-column table of performance type × analysis item × analysis indicator × measurement method, with points |
| 3 성과 조사 및 검증 (performance survey and verification) | Specialized agency data, principal investigator survey, beneficiary survey, comparison with raw data |
| 4 투입 및 과정 분석 (input and process analysis) | Appropriateness of the purpose and government support, implementation structure, budget scale and portfolio |
| 5 산출의 효율성 분석 (output efficiency analysis) | Output per input presented with comparison groups (overall average, similar programs) |
| 6 성과의 효과성 분석 (outcome effectiveness analysis) | Qualitative excellence, goal attainment, influencing factors, ripple effects |
| 7 대표성과 도출 (representative outcome derivation) | Setting selection criteria, collecting outcome information, writing descriptions (3-5 at most) |
| 8 종합분석 및 개선방안 (comprehensive analysis and improvements) | Improvements and action plans per weak area, feedback plan |
| 9 보고서 및 점검 대응 (report and inspection response) | Report writing, response to the self-inspection committee and higher-level inspection |

- R&D performance types are scientific, technological, economic, social, and infrastructural. Refer to the national R&D standard performance indicator system. Add outcomes specific to the program
- Non-R&D programs use the performance type classification of the relevant system
- Specify the target, period, distribution method, reminder procedure, and verification method of the principal investigator survey. List in advance the data to request from the specialized management agency
- For non-R&D programs, replace the survey targets with program staff and beneficiaries
- Classify the causes of unmet indicators (insufficient output for the input, missing evidence, a problem with the indicator setting itself)
- State the goal achievement rate as a formula that sums the products of each indicator's weight and achievement rate
- Utilization and diffusion of outcomes analyze success factors and failure factors together. Leaving out failure factors does not meet the inspection criteria

# Management Evaluation Response Type

- The management evaluation response type is an institution-based track whose framework and wording are set by the public institution management evaluation manual (공공기관 경영평가편람) and the local public enterprise management evaluation system. Do not use the framework of the R&D performance analysis and evaluation type together with it
- The execution order is analysis of the manual's indicator structure, analysis of prior-year evaluation results and findings, rebuilding performance logic per indicator, developing a writing strategy for non-quantitative indicators, comparison with best practices of other institutions, and support for writing the management performance report
- Key work products are an improved management performance report, response logic per indicator, and non-quantitative narratives
- Use indicator names and points exactly as written in the manual of the relevant year. State a plan that reflects the manual's revision date

# Problem-Solving Type

## Module Composition

- The thinking order is the steps of the problem-solving methodology: problem definition, issue decomposition, prioritization, analysis planning, analysis, synthesis, and communication
- This order is usually compressed into 3-4 modules of current state diagnosis, gap analysis, and improvement derivation
- (Problem definition) Derive from the procurement background the problem the client wants to solve and hypotheses about its causes. A problem definition identical to the RFP summary has no discriminating power. Include at least one problem structuring unique to the proposer
- (Issue decomposition) Decompose sibling issues by a single criterion (one of time, structure, or type). Check for duplicates and omissions. Keep a correspondence table of the module that handles each issue
- (Analysis planning) Design surveys and analyses from the viewpoint of hypothesis testing. Rewrite a hypothesis that no result could refute
- (Survey-centered engagements) For status surveys, trend surveys, and demand surveys, the RFP task items are the module structure. Make Tasks concrete in the order of survey design (targets, sample, method, item structure), data verification, and comprehensive analysis
- (Institutional improvement) Analysis of the current system, typology of problems, comparison with foreign systems, alternative design, an alternative comparison table (effect, cost, need for legal amendment, stakeholder acceptance), implementation roadmap
- (Program performance analysis) Build the frame with indicators by type of input, output, and outcome. Analyze factors influencing outcomes with statistical techniques such as regression. Calculate regional economic ripple effects with input-output analysis. Survey participating companies' satisfaction and improvement points with a questionnaire. For system terms, use the general names performance analysis (성과분석), performance indicators (성과지표), and development measures (발전방안)
- The improvement targets are those the RFP specifies among systems, procedures and work processes, organization and staffing, services and programs, information systems, and guidelines and forms
- Choose the comparison standard of the gap analysis according to the improvement target. Laws and other institutions' rules for systems, standard procedures and leading cases for processes, user experience and competing services for services
- Present improvements as a three-column table of changes, implementing body, and application timing per stage. If a system is the target, state the articles to be amended as well

<표> 대안 비교표 예시

| 대안 | 개선 효과 | 소요 비용 | 법령 개정 | 수용성 | 종합 |
|---|---|---|---|---|---|
| 1안 현행 유지 보완 | 낮음 | 낮음 | 불필요 | 높음 | 단기 |
| 2안 제도 신설 | 높음 | 중간 | 시행령 개정 | 중간 | 중기 |

# Informatization Planning Type

- Both mandatory ISPs and IT planning outside mandatory scope are identified as this type. A mandatory ISP is one that a system such as a law or budget guideline requires before an information system is built. IT planning outside mandatory scope is planning for system and platform builds, data and AI adoption plans, digital transformation plans, and next-generation and upgrade plans that the client procures out of its own demand
- IT planning outside mandatory scope composes modules within the client's required scope. Do not force ISP procedures and work product names on it. The module framework and standard work product names below are reference examples

## Module Framework

| Module | Content | Work products |
|--------|---------|---------------|
| M1 환경 분석 (environment analysis) | Policy and technology trends, informatization cases of similar institutions | Environmental factors and implications |
| M2 현황 분석 (current state analysis) | Business status, information system status, infrastructure and security, user requirements | Current state diagnosis and list of improvement requirements |
| M3 목표모델 설계 (target model design) | Business model, information model, application model, technology model, security model | Target architecture |
| M4 이행계획 (transition plan) | Definition of implementation initiatives, priorities, schedule per stage, required budget, expected effects | Implementation roadmap, initiative cards, budget calculation table |

- For public plans such as intelligent information society plans, replace M3 with a policy initiative system. Add the implementation structure and performance indicators to M4
- For user requirements in the current state analysis, specify the scale of questionnaires and interviews in figures. Present system status as a table of real system names, year of introduction, and operator
- Present the required budget as a table together with calculation grounds (staff unit costs, equipment quotation basis)
- (Identifying a mandatory ISP) Identify by the basis for development (a system such as a law or budget guideline), the project cost scale, and the list of work products (information strategy plan, draft request for proposal). If unclear, confirm in the kickoff questions
- For mandatory subjects, the parts set by institutions are the four-stage framework, the requirement classification system, the budget calculation standard (the SW project cost estimation guide of the Korea Software Industry Association), and public informatization security design (national network security system grade classification). Module names and division, Task composition, survey design, the level of detail of the target model, and the priority criteria for implementation initiatives are discretionary
- Standard work product names are 환경분석서, 현황분석서, 정보화 비전 및 전략 정의서, 업무 프로세스 설계서, 목표모델 설계서, 데이터관리체계 설계서, 운영체계 설계서, 이행계획서, 차년도 사업계획서, and 제안요청서. Names the RFP sets take priority
- Divide requirements into functional and non-functional. Use only classification codes the RFP specifies. If the RFP has no codes, use only classification names
- Security design for public informatization uses as is the wording of the national network security system grade classification procedure (preparation, grade classification, threat identification, security measures, adequacy evaluation) and of the measures per grade
- Compose the transition plan in the order of defining implementation initiatives, roadmap, sizing and budget (state the revision year of the SW project cost estimation guide), and build project plans (review of separate procurement, request for proposal)
- Project understanding in an informatization proposal is conventionally composed of the policy environment, the client's data status, the client's constraints (security, data, governance), and the contrast between current and target states

# Support Program Operation Type

## Module Framework

| Module | Content | Work products |
|--------|---------|---------------|
| M1 정책 및 사업 배경 (policy and program background) | Higher-level policy and the underlying program, regional and field conditions, program purpose | Program purpose definition |
| M2 수요자 현황 및 애로 (beneficiary status and difficulties) | Status statistics of target companies and participants, status surveys and questionnaires, difficulties and requests | Demand tally table |
| M3 프로그램 설계 (program design) | Diagnosis and selection, education, consulting, networking, market access and investment linkage | Program design document |
| M4 성과관리 (performance management) | Performance goal system, performance indicators and target values, evidence and inspection method | Performance indicator table |
| M5 운영 및 집행 (operation and execution) | Implementation structure and staffing, annual schedule, program budget and execution plan | Execution plan table |

- For beneficiary difficulties, give statistical grounds alongside: number of survey targets, response rate, and share of top responses
- Place programs by stage. For each stage, specify the target, method, frequency, and work products
- Divide performance goals into core performance goals and autonomous performance goals. The columns of the performance indicator table are category, performance indicator, interim target, final target (cumulative), and evidence
- Place indicators separately as outputs (counts, number of companies) and outcomes (sales, investment attracted, employment)
- Present the program budget as an allocation table by item and a quarterly execution plan
