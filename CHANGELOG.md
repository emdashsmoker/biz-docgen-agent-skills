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
