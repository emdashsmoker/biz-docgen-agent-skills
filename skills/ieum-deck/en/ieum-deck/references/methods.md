# Module skeletons by engagement type

## Application rules

- Read this file at the execution plan design stage, before the step 3 structure confirmation
- Read only the section for the engagement type
- The RFP work details take priority over the skeleton
- Stages the RFP does not require can be omitted
- Place the environment analysis module before the strategy module
- Compose mixed engagements by mixing types module by module
- The matching layouts listed in each section are recipe names from `references/recipes.md` and template names from `references/templates.md`
- How the skeleton applies depends on how far an institutional framework governs the engagement
    + (Framework-based) National R&D performance evaluation response, R&D program planning review response and R&D program planning apply the type skeleton as the default (the framework sets the skeleton and wording)
    + (Conditional framework) IT planning applies the framework procedure if it is a statutory ISP
    + (Discretionary) Management strategy, organization diagnosis, new business discovery, facility feasibility, support program performance analysis and problem solving use the type skeleton as a reference example (the structure differs by contracting agency and engagement)
- A statutory ISP is the preliminary ISP for building an information system above a set amount
- Judge statutory ISP status by the governing law, program budget size and output list
- A statutory ISP uses the procedure and output names of the NIA (National Information Society Agency) ISP·ISMP common guide as is (check the latest edition at kickoff)
- IT planning outside the statutory scope composes modules to fit the contracting agency's requirements
- Modules and Tasks of discretionary engagements are derived from the RFP work details and key issues
- Using the sample skeleton module names as is in a discretionary engagement is a distinctiveness defect
    + In wording tracks mgmt and general, lint WARNs when a `meta.rfp.moduleTasks` title equals a sample module name
    + If the name is set by the RFP, add `rfpNamed: true` to that item
- The module names in the skeletons are Korean deck text and stay in Korean (English glosses in parentheses)

## Type judgment

| Type | RFP signals | Typical outputs |
|---|---|---|
| Strategic planning | Mid- to long-term plan, master plan, development strategy, promotion plan, vision, roadmap | Vision system chart, strategic tasks, roadmap |
| Program planning | New program planning, pre-planning, detailed planning, feasibility, R&D program planning review response, planning report, planning research tasks of R&D budgets | Planning report, logic model, goal and indicator system |
| Performance analysis and evaluation | Performance analysis, performance evaluation response, self-evaluation, management evaluation, indicator development, evaluation system improvement | Performance analysis report, self-evaluation report, indicator system |
| Problem solving | Fact-finding survey, trend survey, demand survey, task discovery, improvement plan, institutional improvement, process improvement, service improvement | Current state diagnosis results, improvement plan, candidate task pool |
| IT planning | ISP, ISMP, intelligent information society master plan, IT strategic plan, system build planning | Target system architecture, implementation plan, budget estimate |
| Support program operation | Business support program operation, commercialization support, startup support, open calls for workforce training operators | Program design document, performance indicators and evidence, budget execution plan |
| R&D plan presentation | Open calls for new national R&D projects (designated, item-designated, free calls), R&D plan presentation evaluation | R&D plan, yearly goals and evaluation indicators, governance, R&D budget |
| Non-R&D open call presentation | Pilot programs, consulting programs, voucher programs, demand-based support programs, consortium calls | Business plan, plan per execution division, performance indicators, budget |

- Private business planning, service planning and internal reports use the same table to judge the type
- New business, service and product planning apply the program planning skeleton
- Adjust the module names of the program planning skeleton to the subject
- Service planning becomes M1 market and user research, M2 competitor and case analysis, M3 service model and feature definition, M4 business viability and execution plan
- IT planning becomes the IT planning skeleton without the statutory ISP procedure: M1 current state and requirements analysis, M2 target system design, M3 build and operation plan
- For engagements that match no RFP signal, judge by the starting point of thinking the engagement requires
    + An engagement that asks to define a target state defaults to the strategic planning skeleton
    + An engagement that asks to find the causes of a current problem defaults to the problem solving skeleton
    + After applying the default, replace modules to fit the RFP work details

## Common norms

- A module opens with a module overview slide
- The module overview columns are Tasks, and the rows are process, data used and outputs
- The output row holds the official output names
- Each Task specifies the data used, the survey scale and the outputs
- Each Task gets at least 1 measured sample
- The sample type is one of a real data table, a real tool screen (NTIS, KOSIS, patent DB, corporate information system) or a case summary
- Mark the sample as a draft with ※
- Fix the input path for tasks and demand to fit the RFP
- The input path is one of a demand survey (planning-sheet questionnaire), a perception survey (scale questionnaire), expert participation (FGI, Delphi, advisory committee) or direct derivation (literature)
- When direct derivation is used alone, add a verification procedure
- Name only the methods the RFP requires (SWOT, AHP, Delphi, logic model, etc.)
- Describe methods the RFP does not require as work content without the method name
- Add a note that the draft advisory committee candidate table is confirmed after consultation with the contracting agency (common practice)

## Strategic planning

```
M1 대내외 환경분석 (internal and external environment analysis)   Policy, market and technology trends. Facts only. Place outlooks and alternatives in M3 and later
M2 내부현황과 사례분석 (internal status and case analysis)         Diagnosis of the target region and organization, leading domestic and overseas cases. Separate the agency introduction status from the capability diagnosis
M3 시사점과 전략체계 (implications and strategy system)           Implication synthesis, SWOT or gap analysis, vision, goals and strategies
M4 실행계획 (execution plan)                                       Action task discovery, priorities (necessity, urgency, feasibility), short- and mid- to long-term roadmap, ripple effects
```

- (SWOT factor sources) Internal status implications go only to strengths and weaknesses
- (SWOT factor sources) External environment implications go only to opportunities and threats
- (SWOT factor sources) Case analysis implications can go to strengths, weaknesses, opportunities and threats
- (SWOT combinations) SO strategies combine only S factors and O factors
- (Vertical alignment) Vision, goals, strategies, strategic tasks, action tasks and performance indicators link through inherited numbering (1. strategy, 1-1. strategic task, 1-1-1. action task)
- (Linkage between tiers) Every item from vision to performance indicators links to at least 1 item in the adjacent tier
- (Implication linkage) Every implication leads to at least 1 task
- (Analysis layout) M1 synthesizes trends, opportunities and threats in the political, economic, social and technology areas into a one-sentence key agenda (pest_scan)
- (History layout) M1 arranges the policy progress to date in time order (history_timeline)
- (Case layout) M2 case analysis contrasts cases on the same comparison items (overview, approach, outcome figures, success factors) (benchmark_cases)
- (Case synthesis) Success factors per case are synthesized into a one-sentence application direction and application tasks per direction
- (Synthesis layout) Open M3 with one analysis synthesis slide gathering per-area implications into strategic issues (findings_synthesis)
- (Task selection) M4 task discovery shows the target count per stage from candidate counts per collection channel to the final task count, with selection criteria, method and participants (task_funnel)
- (Budget breakdown) The overall implementation plan shows short-, mid- and long-term budgets per action task, the total and the share per funding source in a table
- Regional industry promotion engagements cover industry specialization (location quotient), company demand surveys, access to anchor institutions and customers, and the workforce supply base in M2
- Ripple effects are customarily computed with input-output analysis (production, value added and employment inducement)
- Input-output analysis gives the coefficient source and the commodity group allocation basis
- (Common practice for combined management strategy and organization diagnosis engagements) Mid- to long-term management strategy engagements for public agencies cover management strategy, organization diagnosis and management efficiency together
    + Before resetting the mission and vision, evaluate the current strategy system by diagnostic criteria (fit, linkage, validity, feasibility) (strategy_review)
    + The mid- to long-term management strategy consists of environment analysis, resetting mission, vision and core values, development strategy, department-level breakdown of strategic tasks and action tasks, priorities and timing, and yearly performance indicators
    + Organization diagnosis and redesign consist of job analysis, workload survey (quantitative and qualitative analysis), appropriate headcount estimation and allocation, organization structure redesign and delegation of authority improvement
    + The order of organization diagnosis is job analysis, span of control analysis, peer agency benchmarking, redesign plan, phased implementation plan
    + Job analysis and staffing estimation slides show staff participation (briefings, interviews, workshops) together with the verification procedure (owner check, manager review, subject expert verification)
    + Staff size per department is presented as the result after department verification and consultation
    + The staffing estimation table at the proposal stage uses generic names such as 부서 A and 부서 B and form example notation
    + Management efficiency consists of the program portfolio, management evaluation indicator improvement, ESG and the government's public agency innovation direction
    + Management evaluation indicator improvement uses the management evaluation column wording in `references/wording.md`
- (Common practice for non-R&D new business discovery) Present the key issues and solution directions drawn from the engagement understanding as the basis for each work approach
    + The engagement understanding consists of the contracting agency overview, the target program status, higher-level plans, the site status and the uncertainty of conditions
    + New business discovery is a funnel narrowing through business redefinition, a long list, the 1st screen (market attractiveness, fit with the contracting agency, financial feasibility), 2nd screen indicators, new business evaluation and detailed business plans
    + Activation plans are split into pre-development and post-development scenarios
- (Matching layouts) module_overview, pest_scan, history_timeline, benchmark_cases, findings_synthesis, strategy_derivation, strategy_review, env_to_strategy, swot, vision_system, goal_hierarchy, task_funnel, priority_matrix, option_evaluation, roadmap, task_definition, pdca_cycle, impact_io
- (Organization diagnosis matching layouts) job_analysis, workforce_estimation, raci_matrix, gap_analysis, org_redesign, option_evaluation, financial_feasibility, compare
- Select the organization redesign plan and operating model alternatives from the overview per alternative and the comparison result on the same evaluation criteria (option_evaluation)

## Program planning

```
M1 정책과 환경 분석 (policy and environment analysis)          Fit with higher-level plans, policy and technology trends, problems and issues
M2 기존 사업과 사례 분석 (existing program and case analysis)  Review of similar programs, overlap and differentiation, findings on prior planning
M3 목표 체계와 논리모형 (goal system and logic model)          Goal system of purpose, goals and performance indicators, logic model, alignment check of detailed activities
M4 타당성 확보 (securing feasibility)                          Governance, funding, legal and institutional risks, cost estimation and economic analysis
M5 심사와 보고 대응 (review and reporting response)            Planning report writing, in-person meetings and question response (only when the RFP requires it)
```

- (Applicant variant) Business plans written by applicant organizations (corporate R&D projects, commercialization support programs, consortium applications) adjust the content per module within the same skeleton
    + M1 holds market trends, policy trends and unsolved points (fit with higher-level plans is shortened)
    + M2 shows the superiority of the target product and technology with performance figures and comparison targets
    + M3 holds the roles, capabilities and collaboration structure of the participating organizations
    + M4 holds the phased verification plan, the licensing and institutional entry path and the diffusion plan
    + M5 holds the schedule, goal management (PDM), performance indicators (KPI), budget by cost item and the yearly execution plan
    + KPIs are set as quantitative indicators
    + Each KPI carries its measurement timing and calculation basis
- The logic model follows the logic model structure of the Korean Detailed Guidelines for Preliminary Feasibility Studies of National R&D Programs (국가연구개발사업 예비타당성조사 수행 세부지침, 2024) (`logicmodel` block)
    + The items are issue, goal, beneficiary, input, activity, output, outcome and impact, assumption
    + The vertical direction is the flow of program logic
    + The horizontal direction is the time flow of program execution
    + Outcome and impact are combined into one item (split them if the program needs separate review)
    + Item content states the intent and logic of the program planner
- The logic model structure remains the standard method of program planning after the R&D preliminary feasibility study was abolished
- Write outputs (number of papers) and outcomes (changes that occur among beneficiaries) separately
- The goal system consists of the three tiers purpose, goal and performance indicator from [Figure 3-6] of the same guidelines (2024) (`goal_hierarchy`)
    + The purpose is the policy direction the program aims at in the mid to long term
    + The goal is the result the program sets out to achieve
    + The performance indicator is the criterion measuring how far the goal is achieved
    + Engagements that use the terms of the Research Performance Evaluation Act label the same three tiers as strategic goal, performance goal and performance indicator
- Describe the goal as the result that appears among beneficiaries after the program ends
- Center performance indicators on outcome indicators and supplement them with output indicators
- Give each performance indicator a target value, target date and measurement method
- The goal system and the logic model use matching text (the goal is the logic model goal, outcome indicators are outcome and impact, output indicators are output)
- The national R&D preliminary feasibility study is an abolished system
- Its successors are the program planning review for research-type programs and the program execution review and design suitability review for build-type programs
- The non-R&D fiscal program preliminary feasibility study is a current system
- Check at kickoff which is current so the names and procedures of the two systems do not get mixed
- (Scale proportion) Engagements of a few hundred million to a few billion won present a simplified analysis procedure that fits the engagement size
- Economic analysis items: with-and-without comparison, causal consistency of benefits and costs, basis for the discount rate and analysis period, B/C with NPV and IRR, sensitivity analysis
    + (R&D program planning) The base method of economic analysis is cost-benefit analysis
    + (R&D program planning) If benefits are hard to convert into money, substitute cost-effectiveness analysis
    + (R&D program planning) The base decision indicator is B/C (with NPV and IRR)
    + (R&D program planning) Cost items are R&D, research facilities and equipment, and research management
    + (R&D program planning) The cost scope includes costs after the program period
    + (R&D program planning) Benefits are estimated with the market demand approach (future market size × program contribution rate × R&D contribution rate × R&D commercialization success rate × value added rate)
    + Input-output inducement effects (production, value added, employment) are presented as ripple effects separate from economic analysis benefits
- Show economic analysis formulas as a table with one row per indicator (indicator, formula, decision criterion)
- The detailed task breakdown, governance, funding and feasibility review of R&D program planning follow the evaluation items and terms of the same guidelines (2024)
    + The detailed task breakdown is the hierarchy of program, sub-programs (R&D, R&D infrastructure) and detailed tasks, with indicators, periods and size estimation basis per detailed task
    + Governance is the R&D fund and management chain (vertical) and the review and partner bodies (horizontal)
    + Funding sources are national, local and private
    + The financing plan per source carries confirmation documents (National Fiscal Management Plan, mid-term local fiscal plan, financial data of participating companies)
    + The analysis items of the feasibility review are the second-level items of scientific and technological, policy and economic feasibility
    + The overall feasibility evaluation uses the analytic hierarchy process (AHP)
    + The planning committee is composed by expertise, coverage and balance (industry, academia and research institutes, regions, affiliations)
- (Common practice for non-R&D facility master plans and feasibility studies) Public facility engagements such as specialized science museums run in order from current state diagnosis to ripple effects
    + The current state diagnosis consists of laws and higher-level plans (relevant articles, central ministry master plan cycles), domestic facility statistics, 4-5 domestic and overseas cases (cases reflecting regional traits, cases selected in open calls) and regional conditions (election pledges, key industries, existing facilities)
    + The construction feasibility logic is drawn from the implications of the current state diagnosis
    + The basic direction and strategy are set on the construction feasibility logic
    + The detailed plan consists of facility size, exhibition master plan, architectural concept and management and operation plan
    + Economic feasibility (B/C, NPV, IRR) and economic ripple effects are computed after total project cost estimation, funding and annual revenue projection
    + The underlying need of the contracting agency is selection in a central ministry open call, so place the call review criteria and support for writing the business plan under expected effects
    + Use the institutional terms non-R&D preliminary feasibility study or feasibility study
- (Matching layouts) goal_hierarchy, logic_model, issue_tree, project_breakdown, strategy_derivation, governance_tree, funding_plan, feasibility_review, econ_analysis, impact_io

## Performance analysis and evaluation

| Sub-type | Subject | Governing framework | Key outputs |
|---|---|---|---|
| R&D performance analysis and performance evaluation response | National R&D programs | National R&D performance evaluation system (strategic plan, interim self-evaluation, performance management and use, effectiveness analysis) | Overall performance analysis report, self-evaluation report, representative outcome sheet |
| Management evaluation response | Public agencies, local public enterprises | Public agency management evaluation manual, local public enterprise management evaluation | Management performance report improvement plan, response logic per indicator, non-metric narratives |
| Indicator development and system improvement | Internal agency evaluation systems | Agency regulations, higher-level guidelines | Indicator system (definition, formula, weight, measurement method), evaluation procedure, system improvement plan |

- (R&D performance analysis) Run in order from target program status analysis to report writing and review response
    + Design the performance analysis framework as a combination of outcome types, analysis items, indicators and measurement plans
    + Carry out outcome surveys and data verification with specialized agency data, principal investigator surveys and checks against raw data
    + The analysis order is input and process analysis, output efficiency (with a comparison group), outcome effectiveness
    + Set selection criteria first and derive 3-5 representative outcomes
    + Run the report and review response after organizing improvement measures and feedback
    + The performance evaluation guidelines are announced every year, so state the plan for reflecting them when they are released
    + Matching layouts: performance_framework, verify_steps, representative_outcome, feedback_plan, table, steps
- (Management evaluation response) Run from analysis of the manual's indicator structure to report writing support
    + Rebuild the performance logic per indicator on the analysis of the previous year's results and findings
    + Build the non-metric indicator narrative strategy by contrasting with best practices of other agencies
    + The underlying need of the contracting agency is a higher grade, so compress the background narrative
- (Indicator development) Run from analysis of internal and external evaluation systems to the system improvement plan
    + Derive the indicator candidate pool from stakeholder interviews
    + Verify validity and measurability with expert surveys and AHP weights
    + Present the pilot application and system improvement plan after writing indicator definition sheets and formulas
    + Place output indicators and outcome indicators separately
    + Matching layouts: interview_plan, kpi_development, bsc_kpi, alignment_pyramid, advisory_plan
- (Non-R&D support program performance survey analysis) Analyze status and results per program with a performance analysis frame to derive development plans
    + The performance analysis frame consists of indicators by type: input, output, outcome
    + Analyze factors affecting performance with statistical methods such as regression analysis
    + Compute regional economic ripple effects with input-output analysis
    + Survey participating company satisfaction and improvement needs with questionnaires
    + Derive programs and development plans after discovering best practices and reflecting policy trends
    + Use the general column of `references/wording.md` for institutional terms (성과분석, 성과지표, 발전방안)

## Problem solving

- The order of thinking is problem definition, issue structuring, issue prioritization, analysis plan, hypothesis testing, implications, conclusion and action plan
- The default modules compress this order into three: current state diagnosis, gap analysis and improvement plan (four depending on the engagement scope)

```
M1 현황 진단 (current state diagnosis)   Problem definition and cause hypotheses, issue structuring, finding the current state (literature, statistics or surveys, whichever fits the engagement)
M2 갭 분석 (gap analysis)                Gaps against a benchmark, stakeholder opinions (FGI, surveys), cause structuring
M3 개선안 도출 (improvement plan)        Setting and comparing alternatives, priorities, improvement plan and implementation measures
```

- (Issue structuring) Break issues down by a single criterion
- Check the breakdown for overlaps and omissions
- Keep the handling module of every issue in a matching table
- (Hypothesis testing) Design surveys and analyses from the hypothesis testing perspective
- (Survey-centered engagements) Fact-finding, trend and demand survey engagements carry the RFP work items over into the module structure
- The Tasks of survey-centered engagements are detailed in the order survey design (targets, sample, method, question structure), data verification and overall analysis
- (Institutional improvement) Compose in the order current system analysis, problem typology, overseas system comparison, alternative design, alternative comparison table (effect, cost, need for legal amendment, stakeholder acceptance) and roadmap
- The improvement target is whichever the RFP names among institutions, procedures and work processes, organization and staffing, services and programs, systems, and guidelines and forms
- Choose the M2 benchmark by improvement target
    + (Institutions) Laws, regulations of other agencies
    + (Processes) Standard procedures, leading cases
    + (Services) User experience, competing services
- Specify the survey scale and schedule in figures (population, sample size, survey period, response encouragement method)
- Include at least one problem structuring unique to the bidder
- Write hypotheses in a falsifiable form
- Show the improvement plan as a table of changes, implementing body and phased application timing
- Organize interview and survey results as the survey overview, opinions per topic, mention rates and implications (interview_findings)
- The alternative comparison table shows the selected option through weights per evaluation criterion, judgments per alternative and the weighted total (option_evaluation)
- If an institution is the improvement target, also show the articles of laws and regulations to amend
- (Matching layouts) issue_tree, interview_plan, survey_design, verify_steps, interview_findings, gap_analysis, findings_synthesis, option_evaluation, priority_matrix, chart_text, chart_two, analysis_four, key_numbers, illustrative

## IT planning (statutory ISP, intelligent information society master plan, general IT planning)

```
M1 환경분석 (environment analysis)        Policy and technology trends, alignment with higher-level plans, peer agency cases
M2 현황분석 (current state analysis)      Business status (business procedure map, business function definition), information system status (applications, data, infrastructure, security), user requirements survey
M3 목표모델 설계 (target model design)    To-Be business process, To-Be information system architecture, To-Be data architecture, To-Be technology and security architecture
M4 통합 이행계획 (integrated implementation plan)   Implementation task definition, priorities, phased roadmap, total build cost estimate, effect analysis
```

- (Statutory ISP judgment) Check the governing law, program budget size and output list (IT strategic plan, draft RFP, etc.) of the RFP
- If the judgment is unclear, confirm with the user in the kickoff questions
- (What the framework sets for statutory targets) The 4-stage skeleton (environment analysis, current state analysis, target model design, integrated implementation plan), the requirement classification system, budget estimation criteria (software project cost estimation guide) and public IT security design (national network security framework grade classification)
- (What remains discretionary even for statutory targets) Module names and split, Task composition, survey design, level of detail of the target model, implementation task priority criteria
- (IT planning outside the statutory scope) Compose modules and Tasks for the scope the contracting agency requires
- Output names of IT planning outside the statutory scope use the RFP spelling
- The 4-stage skeleton is the default for statutory engagements
- For engagements outside the statutory scope, the 4-stage skeleton is a reference example
- The current state analysis states gaps in an As-Is and To-Be comparison table
- Show the business procedure map and the To-Be business process with flowchart symbols (`flowchart` block)
- Split requirements into functional, non-functional, technical and project support requirements and assign IDs
- The requirement (요구사항) and specification (요건) terms in output names use the guide text as is (e.g. 업무 요구사항 분석서, 정보시스템 요건 기술서)
- Present the budget estimate as an estimation basis table naming an official standard such as the software project cost estimation guide and its year
- Pure software development projects are outside the scope of the IT planning skeleton
- (Common practice for IT proposals) The usual chapters of an ISP proposal summary are strategy and methodology, project execution, project management and project support
    + Strategy and methodology consist of program understanding, strategy and methodology
    + Project execution consists of organization and staff, and execution measures
    + Project support consists of quality assurance and confidentiality and security
    + Program understanding is 4 slides: policy environment, contracting agency data status, contracting agency constraints (security, data, governance), As-Is and To-Be
    + The strategy is derived from program characteristics and risk factors through key success factors
    + Place 1 slide per strategy
    + A strategy slide consists of 4-step STEP cards and a sample example
- (Standard output names) Use the output names of the 9th edition of the ISP·ISMP common guide (official Korean names)
    + (ISP examples) 경영환경 분석서, 법·제도 분석서, 업무현황 분석서, 차이 분석서, 정보화 전략 정의서, To-Be 업무프로세스 설계서, To-Be 정보시스템 구조 설계서, To-Be 데이터 구조 설계서, To-Be 기술 및 보안 구조 설계서, 통합 이행계획 수립서
    + (ISMP examples) 업무 요구사항 분석서, 정보기술 요구사항 분석서, 요구사항 연관표, 정보시스템 요건 기술서
- Names set by the RFP take priority over the standard output names
- Requirement classification ID codes differ by RFP
    + SYR, FUR, PER, SER, QUR, SIR, UIR, DAR, SOR, COR are format examples
    + Codes designated by the contracting agency take priority over the format examples
    + Register the RFP requirement codes in the 00_rfp.md key wording and use them as is
    + If the RFP has no codes, use only the category names
- Public IT security design uses the wording of the national network security framework (N2SF) grade classification (confidential C, sensitive S, open O) and procedure (preparation, grade classification, threat identification, security measures, adequacy assessment and adjustment) as is
- Security measures per grade (network separation, web isolation, content disarm of incoming documents, leak prevention, access rights) follow the spelling of the contracting agency security guidelines first
- The implementation plan consists of implementation task definition, roadmap, size estimation and budget (with the cost estimation guide year), and the build project plan (separate procurement review, RFP)
- The PoC is composed as rounds of goal setting, data preparation, model selection and environment, pilot service and performance analysis
- Give performance conditions (concurrent users, throughput) in figures
- (Matching layouts) process_redesign, target_model, requirements, system_architecture, data_management, poc_plan, operation_governance, survey_design, priority_matrix, compare, roadmap

## Support program operation (business support, commercialization, startups, workforce training operators)

```
M1 정책과 사업 배경 (policy and program background)        Higher-level policies and the parent program, regional and sector conditions, program purpose
M2 수요자 현황과 애로 (beneficiary status and difficulties) Statistics on target companies and participants, fact-finding surveys and questionnaires, difficulties and requests
M3 프로그램 설계 (program design)                          Diagnosis and selection, training, consulting, networking, market access and investment linkage
M4 성과관리 (performance management)                       Performance goal system, indicators and target values, evidence and check method
M5 운영과 집행 (operation and execution)                   Governance and staff, annual schedule, budget and execution plan
```

- Beneficiary difficulties carry statistical evidence (number surveyed, response rate, share of top answers)
- Place programs stage by stage
- Specify the target, format, frequency and outputs of each program stage
- Split performance goals into core and voluntary performance goals
- The performance indicator table columns are category, indicator, interim target, final target (cumulative) and evidence
- Place output indicators (counts, number of companies) and outcome indicators (sales, investment attracted, employment) separately
- Present the budget as an allocation table per item and a quarterly execution plan

## R&D plan presentation (open calls for new national R&D projects)

```
1 필요성 (need)                         Background and policy trends, technology status and problems, ripple effects
2 목표와 내용 (goals and content)        Final goal, goals per phase and year, evaluation items and indicators, yearly research content
3 추진전략과 체계 (strategy and governance)   Strategy, consortium composition and roles per organization, collaboration and risk management
4 연구수행 역량 (research capability)   Capabilities of lead and participating organizations, track records of the principal investigator and researchers, infrastructure
5 활용과 사업화 (use and commercialization)   Outcome use plan, commercialization strategy, expected effects
6 연구개발비와 보안 (R&D budget and security) R&D budget by cost item, safety and security measures plan
```

- The numbers are the chapter numbers of the plan items
- The section structure uses the chapter structure of the plan
- The execution units are years and detailed tasks, so section titles take the `[1차년도]` and `[세부과제 1]` formats
- The coverage check for technology development projects is full coverage of the plan items (`meta.structure` value plan)
- List the plan items in `meta.rfp.tasks` and match them with the slides' `rfpTasks`
- A plan item without a matching slide is a lint FAIL
- (Planning research exception) Survey and planning tasks commissioned under R&D budgets and frameworks (technology development planning research, pre-planning, detailed planning) design the work content as modules and Tasks
    + The document form and table of contents follow the R&D plan
    + The content design uses the program planning skeleton (M1 policy and environment analysis, M2 existing program and case analysis, M3 goal system and logic model, M4 securing feasibility)
    + Place modules and Tasks inside the research content item of the plan
    + Apply the module overview and full Task coverage rules
    + Judgment signals are 기획연구, 사전기획, 상세기획 or 기획과제 in the engagement name and a planning report as output
- The presentation follows the item order of the RFP and the evaluation table as is
- The chapters and sections of the table of contents are plan items set by the framework, so place all plan items as they are
- Yearly content covers every year of the program period
- Put the matching page number of the R&D plan on each slide
- Present the final goal as quantitative evaluation indicators (item, unit, target value, measurement method, comparison with the world's best level)
- Put phases and years in one table for yearly goals and link them to outputs
- Number the lead organization and joint organizations of a consortium
- Show the tasks and participating researchers of each organization together
- For projects evaluated before, place a table contrasting the findings with how they were reflected
- The contrast table carries the numbers of the slides where they were reflected
- Contrast the technology level with comparison targets (leading domestic and overseas organizations, competing platforms) in figures
- Present the R&D budget as allocation by cost item and yearly execution
- Personnel costs and research facility costs carry their calculation basis
- Security projects place the security grade, access control and data management procedure on a separate slide
- (Matching layouts) purpose, scope, features, strategy, logic_model, goal_hierarchy, roadmap, governance_tree, gantt, org, pm_profile, infra_tiles, security_plan

## Non-R&D open call presentation (pilot, consulting, voucher, demand-based support programs)

```
1 사업 개요 (program overview)          Background, program goal and scope, strategy, proposal features
2 참여자 현황 (participants)             Lead and participating organizations, participating staff, program track record (both sides for demand and supply structures)
3 수행부문 (execution divisions)         Target discovery, execution plan, verification plan and operation plan for each division the RFP defines
4 확산과 성과 (diffusion and outcomes)   Ecosystem and regional activation, industrialization and commercialization, jobs and ripple effects, future plans
5 운영관리 (operation management)        Performance reporting, governance, budget
```

- The numbers are the chapter numbers of the RFP items
- The section structure uses the RFP chapter structure
- The execution units are the execution divisions the RFP defines, so section titles take the `[수행부문 1] 부문명` format
- Manage full coverage of RFP items with the section ledger (`meta.structure` value sections)
- List the RFP items in `meta.rfp.tasks` and match them with the slides' `rfpTasks`
- The chapters and sections of the table of contents use the order and names of the RFP work items as is
- With two or more execution divisions, give each division its own chapter
- Each division chapter repeats the same sub-section composition (discovery, execution, verification, operation)
- Place an effectiveness verification plan and a test verification plan in each division
- Programs split into demand and supply (vouchers, pilots) present the demand organizations and supply companies separately
- Show the role split between demand organizations and supply companies in a table
- Present the target system and adoption plan as an architecture diagram and a phased adoption procedure
- Market and demand evidence carries source and year
- Growth rates state their calculation basis
- Present outcomes as quantitative indicators (counts, sales, employment, market entry) together with the diffusion path
- An RFP item without a matching slide is a lint FAIL
- (Matching layouts) purpose, scope, strategy, process, company_profile, target_model, poc_plan, goal_hierarchy, key_numbers, funding_plan, gantt, org, report_plan
