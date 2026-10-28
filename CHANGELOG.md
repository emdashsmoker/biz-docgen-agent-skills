# Changelog

Dates are in UTC.

날짜는 UTC 기준으로 표기

<!--
Changelog rules
- (Timing) Record each pull request right after it is merged into main.
- (Scope) Check all main history since the last commit that changed CHANGELOG.md and record every merge that is still missing.
- (History command) TZ=UTC git log --first-parent --date=format-local:%Y-%m-%d origin/main
- (Date) Use the UTC date of the merge commit in YYYY-MM-DD format.
- (Date order) Keep the newest date at the top.
- (Entry unit) Write one entry for each change that users can notice.
- (Grouping) Combine same-day pull requests on the same topic into one entry and list every pull request number.
- (Splitting) Split a pull request that contains unrelated changes into separate entries.
- (Skill header) Group the entries of each date under ### headers named after the folders under skills/. Use ### Common for repository-wide changes and changes that apply to every skill. Repeat a change that applies to several skills under each of their headers.
- (Entry order) Put the Common header first and sort the other headers by skill folder name. List the entries under each header in pull request order.
- (English entries) List the English entries first under each header with the "-" bullet.
- (Korean entries) Leave one blank line after the English entries and list the same changes in the same order with the "*" bullet so that they render as a separate list.
- (English format) - Description that starts with the change type verb (#PR number)
- (Korean format) * Korean noun-ending description that ends with the change type word (#PR number)
- (Korean style) Write each Korean entry in formal note style as a simple sentence (단문) with a noun ending. Keep one subject-predicate relation per entry, turn other clauses into noun phrases, and split an entry that carries two messages. Avoid colloquial expressions and placeholder nouns such as 것, 곳, 거, 셈 and 부분.
- (Change types) Added (추가), Changed (변경), Fixed (수정), Removed (삭제), Action needed (필요)
- (Include) Changes to skill outputs, usage steps, or installation.
- (Exclude) Typo and wording fixes, demo image replacements, README changes unrelated to installation, internal refactoring without behavior changes, and commits that only change CHANGELOG.md.
- (Push) Commit on top of the latest main and push directly to main.
-->

## 2026-10-27

### ieum-deck
- Added a rule that strategy names end with an action noun such as 수립, 연계, 운영 or 제시, with rewrite examples for names that end with an output, meeting body or methodology name (#50, #52)
- Changed the strategy headline to substitute the strategy names as written in the pillar titles (#50)
- Changed the S07 strategy sample to pillar names that end with 정렬, 확보 and 설계 (#50)
- Changed the S17 roadmap sample lane "환류 체계" to "환류 체계 운영" so that every lane name ends with an action noun (#52)
- Added a rule that keeps tables listing risks or values secured by strategy, such as the strategy derivation table, out of the Sample of strategy slides, with a deep review item for such tables (#58)
- Changed the sample table note from "참고용 시안, 확정치 아님" to "참고용 예시 (미확정)" (#58, #60)
- Fixed the build record file name in the English templates.md that GitHub hid (#62)
- Fixed paragraph spacing that differed between sibling bullet boxes on the same tier, such as the boxes in one row, by sharing the smallest per-box spacing within each group (#64)
- Added a rule against colloquial style in headlines and body text, with example markers (#66)
- Changed the "및" rule for two listed nouns from labels only to all text, including headlines and body text (#66)
- Added exceptions that keep "와" and "과" in RFP original names, established names such as "학습과 성장", relations between two nouns and partners of an action (#66)
- Changed two-noun lists in the headline patterns, reference examples and sample slides to "및" (#66, #68)
- Added a rule that polite headlines end in 하십시오체, such as "수립합니다" (#70)

* 산출물명, 회의체명, 방법론명으로 끝나는 전략명의 재작성 예를 갖춘 동작 명사(수립, 연계, 운영, 제시 등) 종결 규칙 추가 (#50, #52)
* 기둥 제목의 전략명을 그대로 쓰는 추진전략 헤드라인 치환 방식 변경 (#50)
* S07 추진전략 견본을 정렬, 확보, 설계로 끝나는 기둥 이름으로 변경 (#50)
* S17 추진 로드맵 견본의 "환류 체계" 레인명을 "환류 체계 운영"으로 변경 (#52)
* 전략별 위험 요인이나 확보하는 가치를 정리한 표를 견본 표(Sample)에서 제외하는 규칙과 심층 검토 항목 추가 (#58)
* 견본 표 부기를 "참고용 시안, 확정치 아님"에서 "참고용 예시 (미확정)"으로 변경 (#58, #60)
* GitHub 화면에서 영어판 templates.md의 빌드 기록 파일명이 사라지던 오류 수정 (#62)
* 상자별 간격의 최솟값 공유로 같은 계층 형제 불릿 상자마다 문단 간격이 다르던 오류 수정 (#64)
* 구어체 표지 예시를 갖춘 헤드라인 및 본문의 구어체 미사용 규칙 추가 (#66)
* 두 명사 나열의 "및" 연결 적용 범위를 라벨 전용에서 텍스트 전체로 변경 (#66)
* RFP 원문 명칭, 관용 명칭(학습과 성장 등), 두 명사 사이의 관계, 동작의 상대에 쓰인 "와", "과"를 유지하는 예외 추가 (#66)
* 헤드라인 문형, 참조 문서 예시, 견본 슬라이드의 두 명사 나열을 "및" 연결로 변경 (#66, #68)
* 존댓말 헤드라인의 하십시오체 종결 규칙 추가 (#70)

### juja-builder
- Added a rule that strategy names end with an action noun such as 수립, 연계, 운영 or 제시, with rewrite examples in content-models.md and a failure pattern for names that end with an output, meeting body or methodology name (#50, #52)
- Added a kickoff question for the narrative length of the proposal background (detailed or brief), with a recommended value by engagement type (#54)
- Removed the background framework form name attached to the engagement type result in the kickoff questions (#54)
- Added a rule that keeps tables listing risk factors or values secured by strategy, such as the strategy derivation table, out of the manuscript (#56, #58)
- Added a row-by-row expansion definition of the derivation table (□ judgment statements and ❍), with a deep review item and a failure pattern for a leaked table (#56, #58)
- Changed the sample table note from "참고용 시안, 확정치 아님" to "참고용 예시 (미확정)" (#58, #60)
- Added exceptions to the two-item "A 및 B" rule that keep "와" and "과" in established names such as "학습과 성장", relations between two nouns and partners of an action (#66)

* 산출물명, 회의체명, 방법론명으로 끝나는 전략명의 실패 패턴과 재작성 예를 갖춘 동작 명사(수립, 연계, 운영, 제시 등) 종결 규칙 추가 (#50, #52)
* 과업 유형별 추천값을 갖춘 제안 배경의 서술 분량(상세, 간결) 착수 질의 추가 (#54)
* 착수 질의에서 과업 유형 판정 결과에 붙던 배경 골격의 구분 명칭 삭제 (#54)
* 추진전략 도출 표처럼 전략별 위험 요인이나 확보하는 가치를 정리한 표의 원고 미반영 규칙 추가 (#56, #58)
* 도출 표의 행 단위 전개 정의(□ 판단문과 ❍), 도출 표 유출의 심층 검토 항목, 실패 패턴 추가 (#56, #58)
* 견본 표 부기를 "참고용 시안, 확정치 아님"에서 "참고용 예시 (미확정)"으로 변경 (#58, #60)
* 2개 나열 "A 및 B" 규칙에 관용 명칭(학습과 성장 등), 두 명사 사이의 관계, 동작의 상대에 쓰인 "와", "과"를 유지하는 예외 추가 (#66)

## 2026-10-26

### ieum-deck
- Added kickoff question 16 that sets the line break unit (`meta.lineBreak`), with word-level breaking as the default and character-level breaking as the opt-out (#43)
- Added a finalize.py check that fails when slide paragraphs lack the line break unit, because LibreOffice review images cannot show PowerPoint line breaks (#43)
- Fixed the missing latinLnBrk attribute so that PowerPoint keeps English words whole at line ends along with Korean words (#43)
- Changed the proposal strategy format so that strategy pillars derive from a task trait, risk, strategy and value table while differentiation points feed only the features tiles, with a slot mapping, a duty removal test and a self-check in strategy.md (#45)
- Added a rule that pillar titles, items and results on the strategy slide take the positive form of the measure and the value, keeping risk wording in 00_strategy.md (#45, #47)
- Added the duty removal question to the distinctiveness row of the deep review (#45)
- Changed the S07 strategy sample to three output design principles with pillar items that fit one line (#45)

* 단어 단위 기본값과 글자 단위 선택지를 갖춘 줄바꿈 단위 착수 질의 16번(`meta.lineBreak`) 추가 (#43)
* LibreOffice 검수 이미지로 확인할 수 없는 PowerPoint 줄바꿈 단위의 미기록 문단 검사를 finalize.py에 추가 (#43)
* PowerPoint에서 한글 어절과 함께 영문 단어를 줄 끝에서 나누지 않기 위한 latinLnBrk 속성 누락 수정 (#43)
* 전략 기둥의 원천을 차별화 포인트에서 추진전략 도출 표(과업 특성, 위험 요인, 추진전략, 확보하는 가치)로 바꾼 제안전략 양식 변경 (#45)
* 전략 슬라이드의 기둥 제목, 항목, result 를 위험 어휘 없이 수단과 가치의 긍정형으로 쓰는 규칙 추가 (#45, #47)
* 심층 검토 변별력 항목에 의무 삭제 시험 질문 추가 (#45)
* S07 추진전략 견본을 결과물 설계 원칙 3개와 1줄 분량 기둥 항목으로 변경 (#45)

## 2026-10-25

### blockwriter
- Removed the description instruction that preferred blockwriter over a general docx skill for report-style Word documents (#41)

* 보고서형 Word 문서에서 일반 docx 스킬보다 blockwriter를 우선하도록 한 description 지시 삭제 (#41)

### ieum-deck
- Removed the reference to juja-builder and blockwriter from the font setting of the hwpx conversion test (#41)

* hwpx 변환 시험의 글꼴 지정 안내에서 juja-builder와 blockwriter 참조 삭제 (#41)

## 2026-10-23

### blockwriter
- Changed the start of document work to obtain the HWPX and DOCX renderers and run their render tests before the planning questions (#35)
- Added a test that renders a one-line DOCX sample after LibreOffice is installed (#35)
- Added the rhwp repository address and its tag query, asset list, download, source build and run check commands to the HWPX renderer item of SKILL.md (#36, #38)
- Added a procedure for rhwp commands refused by a permission check: stop other download routes, test rendering with LibreOffice and H2Orestart, and ask in the planning questions whether to allow rhwp (#36)
- Changed the handling of refused rhwp commands to ask whether to allow rhwp before falling back to LibreOffice and H2Orestart (#37)
- Added the rhwp permission question to the top of the planning questions, kept even when the user asks to run immediately (#37)

* 기획안 질문 전 HWPX 및 DOCX 렌더러의 확보와 렌더 시험을 마치도록 착수 순서 변경 (#35)
* LibreOffice 설치 후 한 줄 분량 DOCX 예시로 렌더링을 확인하는 시험 추가 (#35)
* SKILL.md의 HWPX 렌더러 항목에 rhwp 저장소 주소와 태그 조회, 자산 목록 수신, 내려받기, 소스 빌드, 동작 확인 명령 추가 (#36, #38)
* rhwp 명령의 권한 거부 시 다른 수신 경로의 중단, LibreOffice와 H2Orestart 렌더 시험, 기획안 질문의 rhwp 허용 질의로 이어지는 처리 절차 추가 (#36)
* rhwp 명령의 권한 거부 시 LibreOffice와 H2Orestart 대체 전에 rhwp 허용 여부를 묻는 처리 순서로 변경 (#37)
* 바로 실행 요청에도 생략하지 않는 rhwp 허용 질문을 기획안 질문 목록 맨 앞에 추가 (#37)

### ieum-deck
- Added a procedure that stops obtaining rhwp and asks whether to allow it when a permission check refuses an rhwp command during input conversion (#37)

* 입력 변환 중 rhwp 명령의 권한 거부 시 적용할 rhwp 확보 중단 및 허용 질의 절차 추가 (#37)

### juja-builder
- Added a procedure that stops obtaining rhwp and asks whether to allow it when a permission check refuses an rhwp command (#37)
- Added the rhwp permission question to the top of the kickoff questions (#37)

* rhwp 명령의 권한 거부 시 적용할 rhwp 확보 중단 및 허용 질의 절차 추가 (#37)
* 착수 질의 목록 맨 앞에 rhwp 허용 질의 추가 (#37)

## 2026-10-22

### Common
- Added a planning question that asks whether to deliver a PDF with the output file, together with a notice that the PDF is an approximate rendering (#34)

* 산출 파일과 함께 PDF를 전달할지 묻는 기획 질의와 근사 렌더링 안내 추가 (#34)

### juja-builder
- Changed the default delivery to HWPX or DOCX files without a PDF (#34)
- Changed the location of review PDFs and page PNGs to outside the delivery folder (#34)

* PDF 없이 HWPX 또는 DOCX 파일만 전달하는 방식으로 기본 납품 구성 변경 (#34)
* 검수용 PDF와 쪽 PNG의 저장 위치를 납품 폴더 밖으로 변경 (#34)

## 2026-10-21

### blockwriter
- Fixed the HWPX page number control being written before the column definition, which made Hangul drop the section page setup and shrink the body width after a re-save (#33)

* HWPX 쪽번호 컨트롤을 단 정의 앞에 기록하여 한/글 재저장 후 구역 쪽 설정이 풀리고 본문 폭이 줄던 결함 수정 (#33)

## 2026-10-18

### Common
- Added a step that attaches the rhwp and fonts repositories before accessing GitHub (#20)

* GitHub 접근 전 rhwp 및 fonts 저장소 연결 단계 추가 (#20)

### blockwriter
- Added a test that renders a one-line HWPX sample right after each HWPX renderer is obtained (#21)
- Changed runs to show the deprecation warnings of python-hwpx (#21)

* HWPX 렌더러 확보 직후 한 줄 분량 HWPX 예시로 렌더링을 확인하는 시험 추가 (#21)
* 실행 중 python-hwpx의 사용 중단 예고 경고를 표시하도록 변경 (#21)

### ieum-deck
- Added a test that converts a one-line HWPX sample right after each HWPX converter is obtained (#21)
- Added a LibreOffice conversion for layout-check PDFs whose pages come out blank (#21)

* HWPX 변환기 확보 직후 한 줄 분량 HWPX 예시로 변환을 확인하는 시험 추가 (#21)
* 배치 확인용 PDF의 빈 쪽 발생 시 LibreOffice로 변환하는 단계 추가 (#21)

### juja-builder
- Changed runs to show the deprecation warnings of python-hwpx (#21)
- Fixed python-hwpx calls that python-hwpx 7.0 removes, which would stop HWPX builds after the upgrade (#22)

* 실행 중 python-hwpx의 사용 중단 예고 경고를 표시하도록 변경 (#21)
* python-hwpx 7.0 삭제 예정 호출의 사용으로 업그레이드 이후 HWPX 파일 생성이 중단될 수 있는 오류 수정 (#22)

## 2026-10-17

### Common
- Added SHA256SUMS.txt files with the checksums of the install packages to each skill folder (#16)
- Added a README note on building a dependency skill with offline-deps-builder where network access is blocked (#17)

* 스킬 폴더별 설치용 패키지의 체크섬을 담은 SHA256SUMS.txt 파일 추가 (#16)
* 네트워크 차단 환경에서 offline-deps-builder로 의존성 스킬을 생성하는 README 안내 추가 (#17)

## 2026-10-16

### ieum-deck
- Fixed hyphen bullets that showed as empty boxes in PowerPoint (#13)

* PowerPoint에서 줄표 불릿이 빈 사각형으로 표시되는 오류 수정 (#13)

## 2026-10-15

### Common
- Added label settings that replace the fixed Korean labels printed in documents and slides (#9)

* 문서와 슬라이드의 고정 한국어 레이블을 변경할 수 있는 레이블 설정 추가 (#9)

### blockwriter
- Fixed flat HWPX documents that failed the skill's own schema check (#9)

* flat 양식 HWPX 문서가 스킬 자체 스키마 검사를 통과하지 못하는 오류 수정 (#9)

### juja-builder
- Fixed DOCX output that tagged Latin text as Korean and split English words and numbers in LibreOffice renders (#9)
- Fixed the default skeleton that kept the template author and dates in the HWPX document properties (#9)

* DOCX 출력에서 라틴 문자의 한국어 언어 태그로 LibreOffice 렌더링 시 영어 단어와 숫자가 분리되는 오류 수정 (#9)
* 기본 스켈레톤의 HWPX 문서 속성에 템플릿 작성자와 날짜가 잔존하는 오류 수정 (#9)

## 2026-10-14

### blockwriter
- Changed footnotes to left alignment so that long URLs no longer stretch the spacing of a line (#8)

* 긴 URL로 각주 줄의 간격이 벌어지지 않도록 각주를 왼쪽 정렬로 변경 (#8)

## 2026-10-13

### Common
- Added the first public release with the Korean and English editions of the skills

* 한국어판 및 영어판 스킬을 담은 최초 공개 버전 추가
