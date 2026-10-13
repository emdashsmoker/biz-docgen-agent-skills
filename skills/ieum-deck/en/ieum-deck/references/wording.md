# Institutional wording

- The wording track is fixed in kickoff question 7
- Record the fixed wording track in `meta.track`
- Wording tracks
    + (rnd) National R&D performance evaluation, R&D program planning review, R&D program planning
    + (mgmt) Public agency management evaluation
    + (general) Agency self-evaluation, non-R&D preliminary feasibility study, general engagements
- lint warns about institutional terms outside the wording track (the checked terms are the framework-specific terms in the rnd and mgmt columns)
- The terms are Korean deck text and stay in Korean

## Terms by track

- Use institutional terms only in engagements the framework applies to (a term outside its scope reads as a poor grasp of the framework)
- Choose slide terms from the column of the wording track

| Concept | rnd column | mgmt column | general column |
|---|---|---|---|
| Plan document | 전략계획서 | 경영계획, 경영실적보고서 | 성과계획서, 사업계획서 |
| Evaluation stage | 중간평가 자체평가, 특정평가, 종료평가 | 실적 평가(계량, 비계량) | 자체 평가, 성과 점검 |
| Evaluating body | 자체점검위원회, 상위점검 | 경영평가단 | 평가위원회, 내부 심의 |
| Performance management | 성과관리·활용계획, 대표성과 소개서 | 우수사례 | 성과 관리 방안, 대표 성과 |
| Ex-post analysis | 효과성 분석, 실태점검 | 지적사항 이행 | 성과 분석, 개선 방안 |
| Program planning review | 사업기획점검(연구형), 사업추진심사와 설계적합성심사(구축형) | Not applicable | 비R&D 예비타당성조사(현행), 타당성 검토 |
| Indicators | 성과목표, 성과지표, 지표 정의서 | 계량지표, 비계량지표 | 핵심성과지표(KPI), 측정 지표 |

## Column signals

- If the RFP has "국가연구개발사업 등의 성과평가 및 성과관리에 관한 법률", "전략계획서" or "특정평가", use the rnd column
- If the RFP has "사업기획점검" or "연구개발계획서", use the rnd column (R&D program planning)
- If the RFP has "경영평가 편람" or "경영실적보고서", use the mgmt column
- If there are no rnd or mgmt signals, use the general column
- The R&D program planning review system was created after the national R&D preliminary feasibility study was abolished in 2026
- Check the name and target size of the program planning review system in the competent ministry's notices at kickoff

## Substitution between tracks

- Internal agency KPI development engagements describe the indicator system with general column terms (e.g. "기관 성과지표 체계에 따라")
- Management evaluation response engagements describe ex-post analysis with mgmt column terms (e.g. 지적사항 이행)
- The performance analysis patterns in `references/headline-patterns.md` (indicator achievement, representative outcome sheet, etc.) use rnd column wording
- When a non-R&D engagement uses a performance analysis pattern, replace the terms with general column terms
