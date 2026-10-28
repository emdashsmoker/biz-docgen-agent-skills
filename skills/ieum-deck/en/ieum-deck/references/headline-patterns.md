# Headline patterns

- For slides whose topic has a pattern, the storyline step only swaps keywords into the pattern
- The storyboard step uses the confirmed headline as is
- For topics without a pattern, the storyline step writes a conclusion sentence that follows `references/writing-rules.md`
- The patterns are Korean deck text and stay in Korean

## Subject term

- "본 과업" (this engagement) in the patterns is the default
- Replace the default with the subject term that fits the engagement
- The first criterion is the spelling in the RFP, the contract and the contracting agency forms
- If a first-criterion spelling exists, use it as is
- The second criterion is the nature of the output
    + (본 연구, this study) Engagements whose main output is research, analysis or verification (fact-finding surveys, policy research, indicator development research)
    + (본 과업, this engagement) Consulting engagements such as diagnosis, strategy, system building, institutional improvement and workshop operation
    + (본 과제, this project task) Engagements where the open call selection unit is called a 과제
    + (본 사업, this program) Support program operation, pilot programs, build programs
    + (본 프로젝트, this project) Private planning, internal planning, public engagements called projects
    + (본 보고서, this report) When a report-style PPT or briefing deck refers to the document itself
- If there are several candidate terms or the RFP has no spelling, confirm with the user in the kickoff questions
- (Sample confirmation question) "이 문서를 본 과업, 본 연구, 본 과제, 본 사업, 본 프로젝트, 본 보고서 중 무엇으로 지칭할까요"
- If the user does not answer, use 본 과업 for public engagements and 본 프로젝트 for private ones
- Planning research and pre-planning use 본 연구 or 본 과업
- Use one subject term throughout a deck (mixing is a lint WARN)
- When the subject term changes, adjust the following particles (은/는, 을/를, 과/와) too
- The subject term applies to headlines, body labels and subtitles
    + The replacement targets are the template labels and sample text "과업의 목적", "과업의 배경 및 목적", "과업의 목표 및 범위", "본 과업의 최종 목표", "과업 추진 단계", "과업 종료 후"
    + With 본 사업, replace them with "사업의 목적", "사업의 목표 및 범위", "사업 추진 단계", "사업 종료 후"
    + With 본 프로젝트, replace them with "프로젝트의 목적", "프로젝트 추진 단계"
- Exceptions are form names set by the RFP (과업지시서, 과업 세부내용, etc.) and structural labels such as VISION and SCOPE
- An engagement (과업) label left in a non-proposal output is a lint WARN

## Base patterns

- (Task) Task {{N}}은 {{대상}}을 대상으로 {{방법}}을 실시하여 {{산출물}} 도출
- (Analysis result) {{대상}}은 {{발견}}
- (Implication) {{개선 대상}}의 {{개선 방향}}이 필요
- (SWOT synthesis) 강점, 약점, 기회, 위협 요인을 취합하여 {{N}}개 전략 방향 도출

## Noun-ending conversion rules

- The noun style rewrites a whole polite sentence as a noun-ending sentence
- Keep the agreement between particles and predicates after conversion
    + "…을 수립하는 것을 목적으로 합니다" → "…수립을 목적으로 추진" or "…수립이 목적"
    + "…을 제시합니다" → "…제시"
    + "…으로 추진됩니다" → "…으로 추진"
    + "…을 보유하고 있습니다" → "…보유"
- The last word of the result is a noun or a noun-form ending (추진, 도출, 제시, 확보, 수행)
- Check agreement by reading the result with "함" added at the end (e.g. it passes if it reads naturally, like "수립을 목적으로 추진함")
- The polite style applies the conversion rules in reverse to the noun patterns to get polite predicates

## Patterns by topic

- Noun-ending patterns for topics that recur in planning and consulting slides
- Replace the {{ }} slots with engagement content
- Refine the other phrases to fit the engagement
- The layout column holds a template name from `references/templates.md` or a recipe name from `references/recipes.md`
- The group column of the execution plan table is the engagement field of the topic (named after the groups in the `references/recipes.md` recipe list)
- A recipe in the layout column may belong to another group (e.g. market_sizing from the analysis results group for market size estimation in program planning)

### Proposal overview

| Topic | Pattern | Layout |
|---|---|---|
| Background and purpose | 본 과업은 {{정책 환경 변화}}에 대응하여 {{발주기관}}의 {{산출물}} 수립을 목적으로 추진 | purpose |
| Goal and scope | 본 과업은 {{최종 목표}}를 목표로 {{N}}개 모듈을 수행 | scope |
| Strategy | 본 과업은 {{최종 목표}} 달성을 위해 {{전략 1}}, {{전략 2}}, {{전략 3}} 전략을 추진 | strategy |
| Execution process | 본 과업은 {{N}}개 Module 에 맞추어 단계적으로 수행 | process |
| Proposal features | 제안사는 {{전문분야}}의 문제해결 역량을 보유 | features |
| Infrastructure | 제안사는 동향 조사 및 {{전문분야}} 전략 수립에 활용할 데이터베이스 및 분석 도구를 보유 | infra_tiles |
| Key track record | 제안사는 {{대표 분야}} 과업 수행 경험으로 과업 이해도를 확보 | case_card |
| Project lead | 책임자는 {{N}}년 경력의 {{전문분야}} 기획 전문가 | pm_profile |

### Bidder status

| Topic | Pattern | Layout |
|---|---|---|
| General status | 제안사는 {{설립연도}}년 설립 이후 {{분야}} 과업을 수행한 전문 기업 | company_profile |
| Organization and staff | 제안사는 {{N}}개 본부 {{N}}개 팀 {{N}}명으로 구성 | bullets, orgchart |
| Financial status | 제안사의 매출액은 {{연도}}년 {{금액}}에서 {{연도}}년 {{금액}}으로 증가 | finance_status |
| Track record | 제안사는 유사 분야 과업 {{N}}건을 수행하여 과업 수행 경험을 축적 | table, record_cards |
| National funding record | 제안사는 {{전문분야}}에서 {{대표 과업}} 대응으로 국비 {{금액}}을 확보 | record_cards |

### Execution plan

| Group | Topic | Pattern | Layout |
|---|---|---|---|
| Module overview | Module overview | Module {{N}}은 {{목적}}을 목적으로 {{M}}개 단계별 프로세스로 추진 | module_overview |
| Current state diagnosis | Issue structuring | 환경분석 및 전문가 검토 결과를 이슈 트리로 정리하여 {{중점 분야}}를 확정 | issue_tree |
| Current state diagnosis | Interview design | 부서별 주요 구성원 대상 대면 면담으로 {{개선 과제}}를 도출 | interview_plan |
| Current state diagnosis | Demand survey | {{조사 대상}} 대상 수요조사로 분야별 {{요구사항}}을 도출 | survey_design |
| Current state diagnosis | Candidate application survey | 업무별 반복 빈도 및 자료 보유 상태를 조사하여 {{기술}} 적용 후보를 정리 | survey_design |
| Current state diagnosis | Data verification | 실무자, 중간관리자, 책임자 순의 성과자료 검증으로 자료의 신뢰성을 확보 | verify_steps |
| Current state diagnosis | Macro environment analysis | 외부 동향을 종합하여 {{핵심 아젠다}}를 도출 | pest_scan |
| Current state diagnosis | Progress to date | {{정책}} 추진 경과를 정리하여 현 단계의 보완 과제 도출 | history_timeline |
| Current state diagnosis | Case benchmarking | 선행 사례의 성과 요인에서 {{적용 방향}} 도출 | benchmark_cases |
| Current state diagnosis | Agency value chain | 기관 기능을 가치사슬 단계에 대응하여 기능 중복 구간 및 공백 구간 확인 | value_chain |
| Current state diagnosis | Industry value chain | 공급 단계별 국내 공급 수준을 진단하여 취약 단계 및 확보 우선순위 도출 | industry_chain |
| Analysis results | Opinion gathering results | 현장 의견수렴에서 {{주요 요구}} 확인 | interview_findings |
| Analysis results | Analysis synthesis | 환경, 현황, 사례, 의견수렴 분석의 시사점을 종합하여 전략 이슈 도출 | findings_synthesis |
| Strategy | Strategic goal derivation | 상위계획에서 기관 임무와 연관된 내용을 추출하여 사업의 전략목표를 도출 | strategy_derivation |
| Strategy | Environment analysis synthesis | 내부역량 진단 및 외부환경 분석 결과를 비전 및 전략 방향으로 연결하여 전략체계 수립의 근거를 확보 | env_to_strategy |
| Strategy | SWOT | 내부 진단 결과 및 외부 전망을 종합하여 전략 방향 도출의 근거가 되는 SWOT 요인을 확정 | swot, env_to_strategy |
| Strategy | Vision system | 미션부터 전략과제까지 하나의 체계로 연결하여 목표 및 실행 단위를 제시 | vision_system |
| Strategy | Mid-term management goals | 경영환경 요구사항 및 SMART 원칙을 적용하여 비전전략체계에 부합하는 중기 경영목표를 설정 | vision_system |
| Strategy | Strategy system diagnosis | 현행 전략체계를 구조적 역량 및 실행적 역량으로 진단하여 적합성, 연계성, 타당성, 현실성을 검증 | strategy_review |
| Strategy | Goal alignment | 전사 전략을 단위조직 목표 및 개인 직무로 순차 정렬하여 조직평가와 개인평가의 연계성을 확보 | alignment_pyramid |
| Strategy | Individual performance linkage | 조직의 성과목표 및 역량을 개인 성과지표로 연계하여 조직성과와 개인평가를 정렬 | alignment_pyramid |
| Strategy | Candidate task selection | 후보 과제 {{N}}건을 단계별 기준 및 참여 주체의 검토로 좁혀 최종 과제 {{M}}건 선정 | task_funnel |
| Strategy | Alternative comparison | {{대상}} 대안을 같은 기준으로 비교하여 {{선정안}} 선정 | option_evaluation |
| Strategy | Priority judgment | 업무 효과성 및 실행 용이성을 점수로 환산하여 착수 순서를 판정 | priority_matrix |
| Strategy | Program portfolio | 조정기준 항목별 전문가 평가 결과에 따라 기존 사업을 매력성 및 적합성 기준으로 배치 | priority_matrix |
| Strategy | Roadmap | 전략별 이행과제를 연차 계획으로 배열하여 추진 순서 및 과제 간 연계를 제시 | roadmap |
| Strategy | Task definition sheet | 이행과제별 추진방안 및 소요예산을 정의서로 정리하여 착수 가능한 실행계획을 제공 | task_definition |
| Program planning | Program overview | 본 사업은 {{수단}}으로 {{목표}}를 목표로 추진 | table |
| Program planning | Goal system | 사업 목적을 성과목표 및 결과지표로 구체화하여 목표 달성의 측정 기준 제시 | goal_hierarchy |
| Program planning | Logic model | 문제 인식부터 성과까지 사업의 논리 구조를 단계별로 연결하여 투입 대비 성과의 달성 경로를 제시 | logic_model |
| Program planning | Business model | {{고객}}에게 제공하는 {{가치 제안}}을 중심으로 수익 구조 및 운영 자원을 정렬 | business_model |
| Program planning | Market size estimation | {{전체 시장}} 가운데 {{기간}} 내 확보 가능한 수익 시장 규모를 {{규모}}로 추정 | market_sizing |
| Program planning | Detailed task breakdown | 사업목표에 연계한 내역사업별 세부과제를 과제별 성과지표 및 규모 근거로 전개 | project_breakdown |
| Program planning | Task derivation | 전략분야부터 세부과제까지 단계적으로 도출하여 과제별 제안요청서 초안을 작성 | strategy_derivation |
| Program planning | Concretization requirements | 사업 구체화에 필요한 요건을 {{관점}}별로 도출 | cards |
| Program planning | Governance | 주관 부처, 전문기관, 사업단의 관리 계선을 심의 및 협력 주체의 역할과 구분하여 추진 책임 명시 | governance_tree |
| Program planning | Funding | 재원 부담 주체별 조달 방안 및 확인 자료를 연차 투입 계획과 함께 제시 | funding_plan |
| Program planning | Budget and phases | 본 사업은 총 {{N}}년 {{N}}단계 사업으로 {{금액}} 투입 | table, roadmap |
| Program planning | Feasibility review | 과학기술적, 정책적, 경제적 타당성 분석 항목별 기획 근거를 사전 점검 | feasibility_review |
| Program planning | Economic analysis | 총비용 및 편익을 현재가치로 환산하여 비용편익 비율 중심으로 경제성 판정 | econ_analysis |
| Program planning | Financial feasibility | 성과 예측, 투자수익성, 손익분기점 분석을 종합하여 사업의 재무적 타당성을 판단 | financial_feasibility |
| Program planning | Economic ripple effects | 사업비 지출 및 사업화 매출에 산업연관표 계수를 적용하여 생산, 부가가치, 취업 유발효과를 산출 | impact_io |
| Organization diagnosis | Job analysis procedure | 사전준비부터 확정 및 관리까지 순차적 직무분석으로 인사 전반의 기준 정보를 확보 | job_analysis |
| Organization diagnosis | Job identification | 조직계층 기준의 수직적 분석 및 업무프로세스 기준의 수평적 분석을 병행하여 직무를 규명 | job_analysis |
| Organization diagnosis | Appropriate headcount procedure | 인력특성 분석, 현시점 적정인력, 중장기 적정인력, 인력관리 방안 순으로 적정 정원을 산정 | workforce_estimation |
| Organization diagnosis | Headcount estimation method | 거시 산정, 미시 산정, 비교 산정을 병행하여 부서별 적정 인력 규모를 도출 | workforce_estimation |
| Organization diagnosis | Job information collection | 표준 양식으로 수집한 직무정보를 조사팀, 팀장, 직무전문가 검증을 거쳐 직무분류체계로 확정 | job_analysis |
| Organization diagnosis | Task allocation | 업무별 책임 및 승인 주체를 구분하여 업무분장을 명확화 | raci_matrix |
| Organization diagnosis | Organization gap analysis | 진단 결과와 벤치마킹 사이의 격차 분석으로 조직구조 재설계 방향을 도출 | gap_analysis |
| Organization diagnosis | Organization improvement plan | 조직 진단 결과를 기능 효율화, 구조 효율화, 인력 재배치 방향으로 연결하여 개선안을 도출 | org_redesign |
| Organization diagnosis | Function reorganization | 이슈 영역을 통합, 신설, 조정의 개편 영역으로 구체화하여 기능 강화 방향을 도출 | org_redesign |
| Organization diagnosis | Organization structure | 전략, 프로세스, 직무를 순차 연계하여 조직 편제를 마지막 단계에서 확정 | compare |
| Organization diagnosis | Break-even analysis | 시나리오별 손익분기점 도달 시점을 추정하여 사업의 재무 타당성 판단 | financial_feasibility |
| IT planning | Process redesign | 자료 수집 및 초안 작성을 통합하여 업무 프로세스를 재설계 | process_redesign |
| IT planning | Target model | To-Be 업무프로세스부터 기술 및 보안 구조까지 목표모델을 설계하여 구축 범위를 확정 | target_model |
| IT planning | Requirements definition | 업무 및 정보기술 요구사항을 요건으로 정리하여 정보시스템 요건 기술서를 작성 | requirements |
| IT planning | Processing flow | 설계 기준에 맞추어 자료 준비 및 질의 처리 흐름을 구성 | system_architecture |
| IT planning | Platform structure | 이용 채널, 응용 서비스, 모델, 데이터 자원을 하나의 플랫폼 구성으로 연결 | system_architecture |
| IT planning | System structure | 이용자 구간, 업무 처리 구간, {{자원}} 구간을 분리하여 시스템을 구성 | system_architecture |
| IT planning | Data management | 자료 유형별 수집 및 전처리 방식을 정하여 색인까지의 관리 기준을 수립 | data_management |
| IT planning | Pilot verification | 적용 업무 대상 응답 품질 및 처리 성능 측정으로 기술 방식을 확정 | poc_plan |
| IT planning | Operating structure | 이용 정책, 전담 조직, 이용자 역량을 갖추어 서비스 운영을 관리 | operation_governance |
| IT planning | Implementation plan | 이행과제, 소요 예산, 기대 효과를 연결하여 이행계획을 제시 | roadmap, steps |
| Performance management | Department KPI | 조직 차원 및 부서 차원의 관점을 모두 반영한 부서별 KPI 를 성과평가계획표로 확정 | kpi_development |
| Performance management | Performance management system | 현황 분석 및 BSC 기반 KPI 개발을 거쳐 내외부 평가 절차까지 성과관리체계를 설계 | bsc_kpi |
| Performance management | Indicator achievement | 전략계획서의 성과목표 및 성과지표를 기준으로 연도별 달성 현황을 확인 | table |
| Performance management | Outcomes by type | 성과유형별 정량 성과와 계획하지 않은 성과를 구분하여 확인 | table |
| Performance management | Representative outcome trend | 내역사업별 단계 대비 대표성과를 비교하여 성과 추이를 확인 | table |
| Performance management | Performance analysis framework | 분석 영역 및 성과유형별 측정 방안을 사전에 확정하여 성과분석 기준 설정 | performance_framework |
| Performance management | Efficiency analysis | 투입 및 과정의 적절성을 산출의 효율성과 분리하여 분석 | performance_framework |
| Performance management | Effectiveness analysis | 성과유형별 분석지표 및 확인 자료를 사전에 확정하여 효과성을 분석 | performance_framework |
| Performance management | Representative outcome sheet | 종합분석 결과에서 대표성과를 선별하여 소개서로 작성 | representative_outcome |
| Performance management | Feedback plan | 종합분석 결과를 개선방안 및 조치방안으로 연결하여 환류계획을 수립 | feedback_plan |
| Performance management | Management cycle | 계획, 실행, 점검, 개선의 연간 순환으로 점검 결과를 차년도 성과계획에 반영 | pdca_cycle |
| Performance management | Report writing procedure | 대응 전략 수립부터 보고서 확정까지 절차를 순차 수행 | steps |
| Performance management | Success and failure factors | 성공 요인 및 실패 요인에 정량 효과를 함께 제시하여 보고서를 구성 | conclusion, composite |

### Project management

| Topic | Pattern | Layout |
|---|---|---|
| Schedule | 본 과업은 총 {{N}}개월에 걸쳐 수행 | gantt |
| Project organization | 총괄책임자 중심으로 품질관리자 및 Module Leader 를 지정하여 과업 품질을 관리 | org |
| Staffing | 과업별 요구 역량에 따라 등급별 인력을 배치한 투입인력 계획을 제시 | table, staff_card |
| Expert collaboration structure | 분과별 산학연 위원을 균형 있게 구성하여 기획 실무 및 의견수렴 경로를 연결 | collaboration_structure |
| Committee operation | 산학연관 전문가로 구성한 위원회를 추진 단계별 자문 회의로 운영 | advisory_plan |
| Progress control | 주 단위 실적 집계로 계획 대비 진도율 {{기준}}% 미만 구간에 대책을 적용 | progress_control |
| Quality control | 프로젝트 관리 도구를 연결한 과업 관리로 산출물 실적을 수집하여 품질 수준을 점검 | quality_plan |
| Reporting | 주 1회 정례 회의 및 수시 보고를 병행하여 진행 상황을 발주기관과 공유 | report_plan |
| Output submission | 착수, 수행, 완료 단계별 제출 시점에 맞추어 산출물을 발주기관에 제출 | deliverable_plan |
| Security | 물리 보안, 기술 보안, 관리 보안으로 통제 범위를 나누어 과업 자료를 보호 | security_plan |
| Personal data protection | 개인정보 처리 단계별 보호조치 및 보안문서 현장 파쇄 절차를 함께 적용 | privacy_plan |
| Emergency response | 응급환자 발생 시 보고 순서를 사전에 정하여 초기 대응 시간을 단축 | emergency_plan |
| Risk management | 위험 요인별 사전 대응 및 발생 시 조치를 정하여 일정 및 품질 위험 관리 | risk_plan |
| Budget | 비목별 산정 근거 및 재원 구분을 명시하여 사업비 편성의 타당성 확보 | budget_plan |
| Comment response | {{보고회}} 의견을 {{반영 대상}}에 반영하여 최종안 보완 | comment_response |
| Output use | 과업 산출물을 부서별 실행 자료로 연결하여 계획의 이행력 확보 | output_utilization |
| Aftercare | 과업 종료 후 {{N}}개월 무상 사후지원 운영으로 사업 목표의 안정적 달성을 지원 | aftercare |
| Follow-up linkage | 후속 사업 대응부터 후속 과제 발굴까지 지원하여 과업 성과를 후속 사업으로 연계 | aftercare, additional_offer |
| Additional offer | 방법론 이전 및 분석 도구 이전으로 발주기관의 자체 수행 역량을 보완 | additional_offer |
