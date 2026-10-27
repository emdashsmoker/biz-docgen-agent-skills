# Company profile (filled in by the user)

- company.md is the input form that keeps the bidder's information in one place
- Fill table values only from material the user provided
- Leave values you could not confirm as `[회사 확인]`
- List any remaining `[회사 확인]` in the completion report as confirmation requests
- The conversion script finds content by the first word of each title (기본, 연혁, 조직, 재무, 실적) and by the "헤드라인" and "관리 방법론" titles
- Do not edit the titles
- Adjust the number of table rows to the company's size
- Copy this form into the work folder and fill it in there (the form in the skill folder stays as is)
- After filling it in, generate the common part with `python3 scripts/company2slides.py <work folder>/company.md <work folder>/common-slides.json`
- Headings, table labels, keys and phrases below are Korean deck text and stay in Korean

## 기본 정보

| 항목 | 값 |
|---|---|
| 회사명 | 제안사 |
| 대표자 | [회사 확인] |
| 설립연도 | [회사 확인] |
| 임직원 수 | [회사 확인] |
| 주소 | [회사 확인] |
| 홈페이지 | [회사 확인] |
| 사업 분야 | [회사 확인] |
| 인증 | [회사 확인] |

- (Example) `| 사업 분야 | 정책연구, 전략기획, 성과분석 |`
- Separate business areas with commas
- The first 2 areas are used in the headline of the general status slide

## 연혁

| 연도 | 내용 |
|---|---|
| [회사 확인] | [회사 확인] |
| [회사 확인] | [회사 확인] |

- (Example) `| 2014 | 기업부설연구소 설립 (성과분석 분야) |`
- The slide shows up to the first 8 rows

## 조직

| 본부 | 팀 | 전문성 |
|---|---|---|
| [회사 확인] | [회사 확인] | [회사 확인] |

- (Example) `| 정책연구본부 | 성과분석팀 | 성과지표 개발 및 성과 측정 |`
- Teams of the same division are grouped into one panel
- The division in the first row is labeled as the assigned division

## 재무 (단위 천원)

| 구분 | [연도 1] | [연도 2] | [연도 3] |
|---|---|---|---|
| 총자산 | [회사 확인] | [회사 확인] | [회사 확인] |
| 자본총계 | [회사 확인] | [회사 확인] | [회사 확인] |
| 매출액 | [회사 확인] | [회사 확인] | [회사 확인] |
| 영업이익 | [회사 확인] | [회사 확인] | [회사 확인] |

- (Example) head row `| 구분 | 2023 | 2024 | 2025 |`, value row `| 매출액 | 5,200,000 | 5,900,000 | 6,400,000 |`
- If the first-year and last-year values in the 매출액 row are numbers, the change is used in the headline (a 경영 상태 phrase in the 헤드라인 section takes precedence)

## 실적

| 연번 | 발주기관 | 과제명 | 기간 | 개월 | 계약금액 |
|---|---|---|---|---|---|
| 1 | [발주기관] | [과제명] | 0000.00-0000.00 | [회사 확인] | [금액] |

- More than 16 rows are split across several slides

## 헤드라인

- The phrase after each key in parentheses becomes the headline of the matching bidder status slide
- An empty phrase means the headline is written from table values (일반 현황 uses founding year and business areas, 조직 uses division and team counts and headcount, 경영 상태 uses the change in 매출액, 수행 실적 uses the number of records)
- Do not edit the keys in parentheses
- (일반 현황)
- (조직)
- (경영 상태)
- (수행 실적)

## 관리 방법론

- Each phrase becomes the headline of the matching management slide
- Edit the phrases to fit company policy
- Do not edit the keys in parentheses
- (진도) 주 단위 실적 집계로 계획 대비 편차 구간별 대응 기준 적용
- (품질) 산출물별 품질 기준에 따른 주 단위 점검으로 품질 수준 관리
- (보고) 정기 회의 및 수시 보고로 진행 상황을 발주기관과 공유
- (산출물) 단계별 제출 시점에 맞추어 산출물을 발주기관에 제출
- (보안) 물리, 기술, 관리 보안의 통제 범위 구분으로 과업 자료 보호
- (개인정보) 개인정보 처리 단계별 보호 조치로 조사 자료 보호
- (비상) 비상 상황 보고 순서의 사전 지정으로 초기 대응 시간 단축
- (사후지원) 과업 종료 후 무상 사후 지원으로 산출물의 현장 정착 지원
- (추가제안) 방법론 및 분석 도구 이전으로 발주기관의 자체 수행 역량 보완
