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
