# Proposal Vocabulary Dictionary

- When `check tone` flags unconventional vocabulary as FAIL, replace it with vocabulary from the replacement table
- With only a list of banned words, the model creates colloquial or figurative words as workarounds for the banned words. The table of conventional vocabulary by function gives the vocabulary for each position
- Korean words and example sentences in this file are manuscript vocabulary. Use them as written. English in parentheses is a gloss for reading and never goes into manuscripts

## Conventional Vocabulary by Function

| Function | Conventional vocabulary (frequent in proposals) | Example |
|----------|-------------------------------------------------|---------|
| Survey (조사) | 조사, 수집, 검토, 파악, 분석, 대조, 실사, 면담, 설문 | 국내외 사례를 조사하여 비교표를 작성 (survey domestic and international cases and write a comparison table) |
| Derivation (도출) | 도출, 선정, 설계, 수립, 작성, 정의, 분류, 산정 | 우선순위 평가 기준을 설계하여 과제 후보를 선정 (design priority evaluation criteria and select initiative candidates) |
| Verification (검증) | 검증, 확인, 검토, 자문, 협의, 확정, 보완 | 자문위원회 검토를 거쳐 지표 체계를 확정 (finalize the indicator system after advisory committee review) |
| Linkage (연계) | 연계, 반영, 활용, 적용, 전달, 종합 | 조사 결과를 전략 도출의 근거 자료로 활용 (use survey results as grounding material for strategy derivation) |
| Output (산출) | 산출물, 결과물, 보고서, 목록, 체계, 방안, 계획 | 최종 산출물은 기본계획서와 이행과제 정의서 (the final work products are the master plan and the implementation initiative definitions) |
| Securing (확보) | 확보, 구축, 마련, 조성, 강화, 제고, 확대 | 데이터 연계 방안을 마련하여 관리 효율을 제고 (prepare a data linkage plan and raise management efficiency) |
| Process (과정) | 단계, 절차, 순서, 회차, 시기, 기간 | 착수 후 3주 내에 조사 설계를 확정 (finalize the survey design within three weeks of kickoff) |
| Schedule (일정) | 수립, 편성, 배분, 착수, 완료, 납기, 보고 시점, 병행, 선행 | 중간보고 이전에 조사를 완료하도록 체계적 일정을 수립 (set a systematic schedule to complete the survey before the interim report) |
| Judgment (판단) | 기준, 근거, 요건, 원칙, 우선순위, 타당성 | 평가 기준과 배점을 표로 제시 (present evaluation criteria and points as a table) |

## Replacement Table

- `check tone` flags the words on the left. Replace them with the words on the right
- 밀도 and 체크 are outside code detection. For 입력 and 출력, code flags only combined forms such as "입력이", "입력으로", "입력되", "입력 자료", "입력값", "출력이", "출력으로", "출력물", and "출력값". Check other forms directly while writing
- The source of flagged words is TONE_FAIL in the settings part of scripts/proposal.py. If this table and the settings part disagree, the settings part rules

| Flagged words | Replacements | Note |
|---------------|--------------|------|
| 쓰임새, 쓰임 | 활용 방안, 활용처, 산출물 활용 | "결과의 쓰임새" → "결과의 활용 방안" |
| 짜임새, 얼개, 뼈대 | 구성, 체계, 구조 | "골격" is used only in design files |
| 밑그림 | 초안, 기본 방향, 개념 설계 | |
| 출발점 | 기반 마련, 근거 자료, 기초 자료 | "전략 수립의 출발점" → "전략 수립의 기반 마련" |
| 손질, 다듬, 매만지 | 보완, 수정, 정비, 개선 | |
| 채비 | 준비, 착수 준비, 사전 확보 | |
| 목표값 | 목표치 | "성과지표와 목표값" → "성과지표와 목표치" |
| 인계 | 전달, 반영 | Software design phrasing |
| 게이트, 관문 | 확인 시점, 검토 회차, 제출 시점 | Describe the actual act |
| 입력, 입력 자료, 입력값, 출력, 출력물, 출력값, 입력이 되다 | 활용 자료, 근거 자료, 산출물, OO에 활용 | Software design phrasing. Allowed only when describing an actual system design |
| 연결을 확보, 연계 구조, 산출물 연계, 매핑, 인터페이스, 파이프라인 | OO을 OO에 활용, 대응표, 대조, 처리 절차 | Software design phrasing |
| 과업의 답, 과업의 핵심 답, 답이 되, 답을 제시, 과업 방향, 전제조건, 수행 여건, 일정 정합, 근거 누적, 누락 없이, 빠짐없이 대응, 대응 관계, 도달 상태, 도달 시점 | (delete) Describe the resulting content directly | Exposure of framework language and internal judgment |
| 분석형, 조사형, 도출형, 지원형 Task, Task 배치, 수행내용 구성, 열 번호, 행 번호, 열은, 주차 단위 | (delete) | Exposure of design language. Defined in the SKILL.md Terms section |
| 역산, 채점, 평가위원, 통제배점, 배점 귀속, 완결조건, 섹션대장, 적대적, 미배치 | (not written in the body) | Internal logic vocabulary. "역산" in a schedule context also exposes the thinking process. Terms the RFP uses (for example 평가위원회) are excluded from the verdict when listed in the key wording dictionary (for the pre-diagnosis report, the `RFP 용어` table of 00_진단서.md) |
| 일정 역산, 납기 역산 | 체계적 일정 수립, 효율적 일정 편성, 납기를 고려한 일정 배분, 보고 시점에 맞춘 일정 관리 | Describe the result and character of schedule management |
| 일정 동기화, 보고 동기화, 회의 동기화, 과업 동기화, 일정 정렬 | 체계적 일정 수립, 효율적 일정 편성 | Coinages made to work around banned words |
| 밀도, 채움본 | (not written in the body) | Internal logic vocabulary |
| 이면 니즈, 표면 니즈, 표면 목적, 판단문, 문형, 구성 단위, 변별력, 결정 장소, 지시 어휘, 조판, 치환, 오리지널 파트, 공통 파트 | (not written in the body) Describe the actual content that belongs there (work product names, material names, follow-up procedure names) | Terms of the skill's instructions. Readers do not know these words |
| 마일스톤 | 보고 시점, 완료 시점 | Management loanword |
| 작업분해도, WBS, 워크패키지 | 과업 구성표, 세부 과업 | Management loanword |
| 임계경로 | 선행 과업 | Management loanword |
| 이터레이션 | 반복 회차 | Management loanword |
| 온보딩 | 업무 적응 지원 | Management loanword |
| 페인포인트 | 애로사항, 문제점 | Management loanword |
| 인사이트 | 시사점 | Management loanword |
| 딜리버리 | 납품, 제출 | Management loanword |
| 포인트 | 핵심, 요점 | Semi-colloquial word |
| 세팅 | 구성, 설정 | Semi-colloquial word |
| 케이스 | 사례 | Semi-colloquial word |
| 니즈 | 수요, 요구 | Semi-colloquial word |
| 픽스 | 확정 | Semi-colloquial word |
| 체크, 컨펌 | 확인 | Semi-colloquial word |
| 어필 | 부각 | Semi-colloquial word |
| 메리트 | 이점, 장점 | Semi-colloquial word |

## Label Vocabulary

- Use bracketed subheadings only on the ❍ and hyphen levels. The criteria for attaching them are in the SKILL.md Bracketed Subheadings section
- Take the words of a bracketed subheading from the name of the criterion that divides the enumeration group. For example, grade divisions use (공개 등급) (내부 등급), stage divisions use (기획 단계) (평가 단계), and target divisions use (국내 사례) (해외 사례)
- Labels in Task descriptions follow the references/methods.md Common Standards section

## Sentence Ending Vocabulary

- Use only nominal endings that make natural Korean sentences
- Recommended endings are -수행, -도출, -확보, -제시, -수립, -작성, -반영, -확정, -분석, -조사, -필요, -예정, -상태, -전망
- Examples of unnatural endings are "-구조로 우선", "-결론", "-훌륭", "-체계임을"
- Endings of verdict sentences are "-으로 확인", "-으로 집계", "-으로 나타남", "-인 상황", "-인 실정"
- Do not use the colloquial "것" ending. "남은 것" → "OO 잔존", "해야 할 것" → "OO 필요", "과업의 포인트인 것" → "OO이 과업의 핵심", "OO하는 것" → "OO 수행", "OO것임" → a nominal ending
- The "것" verdict of `check tone` targets a "것" ending at the end of a line

## Result Expression Conversion Table

- The left column holds expressions that reveal the author's judgment process. Rewrite them as on the right, as work products, timing, and effects the client receives

| Thinking-process expression | Result expression |
|-----------------------------|-------------------|
| 역산하여 일정을 편성 | 중간보고 시점까지 조사 결과표를 제출 |
| 검토하여 판단 | 기준표에 제시한 기준으로 선정 |
| 고려하여 배치 | 세부 과업별 산출물과 제출 시점을 조견표로 제시 |
| 이를 바탕으로 도출 | 조사 결과 표의 항목을 후보로 제시 |
| 필요성을 인식하여 | (delete, then describe the facts that ground the necessity) |
| 우선순위를 판단하여 | 평가 기준표의 배점과 산식으로 우선순위를 산정 |
| 적절히, 합리적으로, 효과적으로 | (delete, then replace with figures or criteria) |
| 3대 전략, 4가지 방안 | (delete the count) Present strategy items directly as □ |
| RFP 요구사항에 부합하는, 제안요청서의 취지에 맞는 | (delete) Use the original requirement wording in Task names and descriptions |
| 본 과업은, 본 제안은, 본 연구에서는 | (delete) Start with content. If a reference is needed, the real project name |
| RFP가 제시한, RFP가 요구한 | (delete, then describe the content directly) |
| 발주처는 OO을 확보, 발주처가 OO을 달성 | (delete the subject) Write target and state in the predicate |
| N년까지 OO 확정, 최종보고 즉시 적용 (implementation strategy sentences) | (move completion timing to the schedule chart) Describe the way of working and the change it makes |
| 발주처 협의, 발주처 담당자, 발주처 제공 자료 | Write the organization name from the Agency Naming section (00_제안전략서.md for proposals, 00_진단서.md for pre-diagnosis reports) |
| 아래 표는, 다음 표는 OO 예시 | (delete) Place a ❍ with the gist of the table before it. State whether it is an example with ※ under the table |
| 첫째, 둘째, 셋째, 첫 번째, 하나는 OO 다른 하나는, 마지막으로 | (delete) One ❍ per item. A table at four or more |
