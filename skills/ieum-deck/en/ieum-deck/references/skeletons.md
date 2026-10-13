# Table of contents skeletons

- Design the table of contents to fit the RFP and the document purpose
- If the RFP prescribes a table of contents or an evaluation item order, use that order as is
- Headers paired with evaluation items put the item number in section (e.g. "1) 과업 이해도")
- Path-style headers write section in the "주제 〉 세부" format (kickoff question 13)
- Chapter names are Korean deck text and stay in Korean (English glosses in parentheses)

## Default proposal deck skeleton

- Applies to proposal decks whose RFP does not prescribe a table of contents

| Chapter | Section candidates | Layout types | Volume (30-45 slides for a 20-minute presentation) |
|---|---|---|---|
| Ⅰ. 제안개요 (proposal overview) | Background and purpose, goal and scope, strategy, execution process, proposal features, expected effects | purpose, scope, strategy, process, features, output_utilization (pm_profile, case_card, infra_tiles when highlighting the lead and track record) | 5-8 |
| Ⅱ. 제안업체 현황 (bidder status) | General status, organization chart, financial status, similar track record | Common part produced by company2slides.py (company_profile, bullets or orgchart, finance_status, table or record_cards) | 3-5 |
| Ⅲ. 사업수행계획 (execution plan) | Overview per module (`[Module 1] 모듈명`), Tasks, Task bundles, methodology, output examples | module_overview, composite recipes (`references/recipes.md`), task, task_multi, steps, illustrative | 15-25 (2-8 per module) |
| Ⅳ. 사업관리부문 (project management) | Schedule, project organization, staffing, management methodology, risk management, security, output use, aftercare, additional offers | gantt, org, table or staff_card, management slides produced by company2slides.py (project management recipes), risk_plan, output_utilization | 6-10 |

- Present the engagement scope split into time scope (engagement period and plan period), spatial scope (target region or organization) and content scope (modules and work items)
- Present expected effects together with the use plan per engagement output (output_utilization)
- If the RFP has social value (jobs, regions, support for vulnerable groups, safety) as an evaluation item, place 1 slide with the implementation plan in the project management chapter
- The use of the expert collaboration recipe follows the layout selection section of SKILL.md
- Staff evaluation items are attributed to the project lead profile slide
- Management evaluation items are attributed to project management slides
- Quantitative evaluation items (credit rating, number of track records) are excluded from slide allocation
- The writing order is background and need, strategy, execution plan per module, outputs and expected effects, then placing the common part

## Report meeting decks

| Stage | Layout | Volume |
|---|---|---|
| Kickoff report | Engagement overview, direction and strategy, execution plan per module, schedule and organization, requests for cooperation | 40-55 |
| Interim report | Progress to date, how kickoff comments were reflected, interim results per module (mainly analysis slides), plan for remaining work, items for discussion | 30-40 |
| Final report | Engagement overview and progress, results summary, results per module (analysis, strategy, tasks), implementation plan, expected effects, how comments were reflected, follow-up proposals | 50-60 |

- Place 1-3 results summary slides after the engagement overview (analysis summary and SWOT, strategy system, task list)
- Present the progress to date as the dates and main discussions of report meetings, committees and advisory meetings in time order (history_timeline)
- Place 1 implications slide at the end of each analysis chapter
- The implications slide links the implications of the analysis results to strategic issues (findings_synthesis)
- The comment response contrasts each comment from the previous report meeting and advisory meetings with what was reflected and where (comment_response)

## R&D plan presentation

- Applies to R&D plan presentations for open calls for new national R&D projects

| Chapter | Section candidates | Volume |
|---|---|---|
| Ⅰ. 연구개발과제의 필요성 (need for the R&D project) | Background and need, technology status and problems, ripple effects | 4-6 |
| Ⅱ. 목표 및 내용 (goals and content) | Final goal and evaluation indicators, goals per phase and year, schedule and main results | 6-10 |
| Ⅲ. 추진전략 및 추진체계 (strategy and governance) | Strategy, consortium composition and roles per organization, risk management | 3-5 |
| Ⅳ. 연구수행 역량 (research capability) | Organization capabilities, track records of the principal investigator and researchers, infrastructure | 3-5 |
| Ⅴ. 활용방안 및 기대효과 (use plan and expected effects) | Outcome use, commercialization strategy, expected effects | 2-4 |
| Ⅵ. 연구개발비와 보안 (R&D budget and security) | R&D budget by cost item (budget_plan), safety and security measures plan | 1-3 |

- `meta.structure` is plan (full coverage of plan items is checked instead of modules and Tasks)
- Planning research (survey and planning tasks commissioned under R&D budgets) is the exception
    + `meta.structure` is module
    + Modules and Tasks go in the research content of chapter Ⅱ
- The chapter and section order follows the RFP and the evaluation table
- The chapter composition in the table is an example for designated calls
- Place every item and year set by the plan
- For projects that went through a written evaluation, place 1 table contrasting findings and how they were reflected before chapter Ⅰ (comment_response)
- Put the matching page number of the R&D plan in `markerNote` on each slide

## Non-R&D open call presentation

- Applies to open call presentations for pilot, consulting, voucher and demand-based support programs

| Chapter | Section candidates | Volume |
|---|---|---|
| Ⅰ. 사업 개요 (program overview) | Background, program goal and scope, strategy, proposal features | 4-6 |
| Ⅱ. 참여자 현황 (participants) | Lead organization, participating organizations, participating staff, program track record | 3-5 |
| Ⅲ. 수행부문 A (execution division A) | Target discovery, execution plan, effectiveness verification, test verification, operation plan | 6-10 |
| Ⅳ. 수행부문 B (execution division B) | Same sub-sections as execution division A (repeated per division) | 6-10 |
| Ⅴ. 확산과 성과 (diffusion and outcomes) | Ecosystem activation, industrialization and commercialization, jobs, future plans | 3-5 |
| Ⅵ. 운영관리 (operation management) | Performance reporting, governance, budget (budget_plan) | 2-3 |

- `meta.structure` is sections (full coverage of RFP items is checked instead of modules and Tasks)
- Chapter and section names use the RFP work items as is
- For programs split into demand and supply, split chapter Ⅱ into demand organizations and supply companies
- Manage the correspondence between RFP required items and slides with the section ledger

## Support program operation proposal

- Applies to open calls for business support, commercialization, startup and workforce training operators

| Chapter | Section candidates | Volume |
|---|---|---|
| Ⅰ. 제안 개요 (proposal overview) | Background, target status, need (field survey), engagement scope, goals | 5-7 |
| Ⅱ. 수행기관 현황 (operator status) | General status, organization and staff, similar operation track record, infrastructure and network | 3-5 |
| Ⅲ. 사업 수행계획 (program execution plan) | Detailed plan per program (diagnosis, training, consulting, networking, market access and investment) | 10-18 |
| Ⅳ. 성과관리 (performance management) | Performance goal system, indicators and target values, evidence and checks, expected effects | 3-5 |
| Ⅴ. 사업비 사용계획 (budget use plan) | Allocation by cost item, quarterly execution plan | 1-2 |

## Program planning application presentation

- Applies to application presentations for corporate R&D and commercialization project calls

| Chapter | Section candidates | Volume |
|---|---|---|
| Ⅰ. 사업 개요 (program overview) | Background and need, program information, product and technology superiority, consortium capability, strategy | 6-10 |
| Ⅱ. 세부 추진계획 (detailed plan) | Work per module, verification plan, institutional entry, diffusion and marketing | 10-16 |
| Ⅲ. 사업 관리계획 (program management plan) | Schedule, goal management (PDM), performance indicators (KPI) | 3-4 |
| Ⅳ. 소요 예산 (required budget) | Budget breakdown, execution plan | 1-2 |
| Ⅴ. 기대효과 (expected effects) | Technological, business and social effects | 1-2 |

## General planning PPT

- Applies to private planning decks, internal reports and training material
- The module skeleton follows the engagement type judgment in `references/methods.md` (program planning for new businesses and services, strategic planning for mid- to long-term plans, IT planning for system build planning)
- The chapters of the table of contents are the modules of the chosen skeleton
- Adjust chapter names to the subject
- Use the parametric templates and composite recipes as they are
- Skip RFP analysis, score attribution, institutional wording and the section ledger
- Apply the full Task coverage and module overview rules only when there is an execution plan part

## Briefing deck

- The scope follows the briefing deck section of SKILL.md
- The default flow is conclusion, evidence, actions (add 1 background slide if needed)
- Place the conclusion on the first slide
- Later slides present the evidence for the conclusion
- Split detailed evidence into appendix slides
- Choose layout types to fit the content by the same criteria as other output types

## Report-style PPT

- One slide per section
- Place the section's points side by side as bullets panels (the md2storyboard draft places up to 5 panels per slide and moves overflow panels to the next slide)
- A five-panel draft exceeds the recommended bullets column count (1-4), so merge panels or switch to another layout at the storyboard writing stage
- No page limit
- Place a synthesis slide (conclusion or findings_synthesis) at the end of each chapter
- Place 1-3 results summary slides after the overview chapter
- Keep section numbers in section so the header shows continuing sections
- Keep the source line (source) on every slide
- Generate the draft with `md2storyboard.py --kind report`
- Finish the draft by refining the headlines and panels
