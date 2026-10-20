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
- (Skill header) Group the entries of each date under ### headers named after the folders under skills/. Use ### Common (공통) for repository-wide changes and changes that apply to every skill. Repeat a change that applies to several skills under each of their headers.
- (Entry order) Put the Common (공통) header first and sort the other headers by skill folder name. List the entries under each header in pull request order.
- (English entries) List the English entries first under each header with the "-" bullet.
- (Korean entries) Leave one blank line after the English entries and list the same changes in the same order with the "*" bullet so that they render as a separate list.
- (English format) - Description that starts with the change type verb (#PR number)
- (Korean format) * Korean noun-ending description that ends with the change type word (#PR number)
- (Change types) Added (추가), Changed (변경), Fixed (수정), Removed (삭제), Action needed (필요)
- (Include) Changes to skill outputs, usage steps, or installation.
- (Exclude) Typo and wording fixes, demo image replacements, README changes unrelated to installation, internal refactoring without behavior changes, and commits that only change CHANGELOG.md.
- (Push) Commit on top of the latest main and push directly to main.
-->

## 2026-10-18

### Common (공통)
- Added a step that attaches the rhwp and fonts repositories before accessing GitHub (#20)

* GitHub 접근 전 rhwp 및 fonts 저장소 연결 단계 추가 (#20)

### blockwriter
- Added a test that renders a one-line HWPX sample right after each HWPX renderer is obtained (#21)
- Changed runs to show the deprecation warnings of python-hwpx (#21)

* HWPX 렌더러 확보 직후 한 줄짜리 HWPX 예시의 렌더링을 확인하는 시험 추가 (#21)
* 실행 중 python-hwpx의 사용 중단 예고 경고를 표시하도록 변경 (#21)

### ieum-deck
- Added a test that converts a one-line HWPX sample right after each HWPX converter is obtained (#21)
- Added a LibreOffice conversion for layout-check PDFs whose pages come out blank (#21)

* HWPX 변환기 확보 직후 한 줄짜리 HWPX 예시의 변환을 확인하는 시험 추가 (#21)
* 배치 확인용 PDF의 쪽이 비어 있을 때 LibreOffice로 변환하는 단계 추가 (#21)

### juja-builder
- Changed runs to show the deprecation warnings of python-hwpx (#21)
- Fixed python-hwpx calls that python-hwpx 7.0 removes, which would stop HWPX builds after the upgrade (#22)

* 실행 중 python-hwpx의 사용 중단 예고 경고를 표시하도록 변경 (#21)
* python-hwpx 7.0에서 삭제되는 호출로 인해 업그레이드 이후 HWPX 조판이 중단될 수 있는 오류 수정 (#22)

## 2026-10-17

### Common (공통)
- Added SHA256SUMS.txt files with the checksums of the install packages to each skill folder (#16)
- Added a README note on building a dependency skill with offline-deps-builder where network access is blocked (#17)

* 스킬 폴더별 설치용 패키지의 체크섬을 담은 SHA256SUMS.txt 파일 추가 (#16)
* 네트워크 접근이 차단된 환경에서 offline-deps-builder로 의존성 스킬을 만드는 README 안내 추가 (#17)

## 2026-10-16

### ieum-deck
- Fixed hyphen bullets that showed as empty boxes in PowerPoint (#13)

* PowerPoint에서 줄표 불릿이 빈 네모로 표시되는 오류 수정 (#13)

## 2026-10-15

### Common (공통)
- Added label settings that replace the fixed Korean labels printed in documents and slides (#9)

* 문서와 슬라이드에 고정으로 인쇄되던 한국어 레이블을 바꿀 수 있는 레이블 설정 추가 (#9)

### blockwriter
- Fixed flat HWPX documents that failed the skill's own schema check (#9)

* flat 양식 HWPX 문서가 스킬 자체 스키마 검사를 통과하지 못하는 오류 수정 (#9)

### juja-builder
- Fixed DOCX output that tagged Latin text as Korean and split English words and numbers in LibreOffice renders (#9)
- Fixed the default skeleton that kept the template author and dates in the HWPX document properties (#9)

* DOCX 출력이 라틴 문자를 한국어로 지정하여 LibreOffice 렌더링에서 영어 단어와 숫자가 끊기는 오류 수정 (#9)
* 기본 스켈레톤이 HWPX 문서 속성에 템플릿 작성자와 날짜를 남기는 오류 수정 (#9)

## 2026-10-14

### blockwriter
- Changed footnotes to left alignment so that long URLs no longer stretch the spacing of a line (#8)

* 긴 URL로 각주 줄의 간격이 벌어지지 않도록 각주를 왼쪽 정렬로 변경 (#8)

## 2026-10-13

### Common (공통)
- Added the first public release with the Korean and English editions of blockwriter, ieum-deck and juja-builder

* blockwriter, ieum-deck, juja-builder 스킬의 한국어판 및 영어판을 담은 최초 공개 버전 추가
