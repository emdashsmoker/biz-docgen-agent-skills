---
name: blockwriter
description: "정책, 연구, 기획 보고서를 Markdown 원고 하나에서 HWPX(한/글) 또는 DOCX(Word) 파일로 조판하고 렌더링으로 검수하는 스킬. 코드로 생성하는 두 양식(chapter는 제N장 체계, flat은 장 없는 N. 체계) 위에 장, 절, 소절, 가나다, □, ○, -, ㆍ, ※ 계위와 표(캡션 자동번호, 단위 행, 출처 행, 머리글 배경, 열 단위 정렬, 셀 병합, 장표 처리), 그림, 각주, 첨자, 표지, 목차, 머리말, 쪽번호를 배치한다. 유저 HWPX 양식 추출과 빈칸 채우기, DOCX, XLSX, HWPX 문서의 원고화도 지원한다. 유저가 'hwpx', 'HWPX', '한글 문서', '한글 파일', '한글로 작성', '보고서 hwpx', '보고서 docx', 'Word 보고서', '보고서 만들어줘', '보고서 양식', 'md를 hwpx로', 'md를 docx로', 'docx를 hwpx로', 'hwpx 양식 추출', 'hwpx 렌더링', 'hwpx를 md로' 등을 언급하거나 .hwpx 또는 보고서형 .docx의 산출, 편집, 추출을 요청할 때 사용하며, 보고서형 Word 문서는 일반 docx 스킬보다 이 스킬을 우선한다. 원고 표기와 작성 규칙은 references/manuscript.md에 있다. 양식 수치, 조판 규범, DOCX 대응, 목차, 유저 양식, 검수 항목은 references/layout.md에 있다. 렌더러 확보, 렌더러 한계, 글꼴은 references/renderers.md에 있다."
license: AGPL-3.0-or-later with an output exception. Terms in LICENSE and NOTICE.md
---

# blockwriter

이름의 block은 목판(woodblock)에서 따왔다. 목판 인쇄는 글자를 새긴 판에 먹을 바르고 종이를 얹어 문질러 같은 모양의 책장을 거듭 찍어 낸다. 이 스킬은 코드로 만든 양식을 판으로 삼아 Markdown 원고를 찍고 같은 모양의 보고서를 거듭 산출한다.

- Markdown 원고 1개를 코드로 생성한 양식 위에 조판하여 HWPX 또는 DOCX 보고서 파일을 산출
- 두 형식은 같은 원고, 같은 양식 정의(scripts/form.py), 같은 조판 규범(scripts/config.py)을 공유
- DOCX, XLSX, HWPX 입력은 Markdown 원고로 옮긴 뒤 같은 경로로 조판
- 공문과 기안문은 지원 범위 밖

모든 명령은 `python3 scripts/report.py <명령>` 형식으로 실행한다. 명령 표기에서는 `python3 scripts/report.py`를 생략한다.

## 용어

- (원고) 조판의 입력이 되는 Markdown 파일. 표기 규칙은 references/manuscript.md
- (헤더) `#`으로 시작하는 Markdown 제목 줄. `#` 개수가 장, 절, 소절, 가나다를 정함
- (역할) 원고 요소의 종류. 장, 절, 소절, 가나다, 논점, 주장, 근거, 부연, 주석, 출처, 표, 그림 등이며 build는 역할마다 정해진 스타일을 적용
- (계위) 장부터 주석(※)까지 제목과 본문 기호의 상하 단계
- (산출 형식) build가 만드는 파일 형식. HWPX(한/글)와 DOCX(Word) 두 가지
- (양식) 역할별 스타일, 글꼴, 글머리, 쪽 설정의 묶음
    - (내장 양식) chapter와 flat 두 가지. scripts/form.py에 정의하며 build 때마다 산출 형식의 스타일로 생성
    - (유저 양식) 유저가 제공한 HWPX 보고서 양식. skeleton 명령이 스켈레톤과 프로파일 초안으로 변환
- (스켈레톤) 유저 양식에서 스타일 정의와 본문 구역의 쪽 설정만 남긴 빈 HWPX 문서
- (프로파일) 역할별로 적용할 양식 스타일 이름과 번호 형식을 적은 JSON. 내장 양식은 `chapter`, `flat` 이름으로 지정
- (검수 렌더러) 문서를 PDF와 쪽 PNG로 그려 검수에 쓰는 프로그램(rhwp, LibreOffice). 한/글과 Word의 배치를 근사하게 재현

## 준비

```bash
pip install -U python-hwpx python-docx lxml pillow openpyxl fonttools --break-system-packages
```

- 최신 버전 설치를 먼저 시도하고 설치된 최신 버전으로 작업
- 최신 API 변경으로 스크립트가 실패하면 스크립트를 최신 API에 맞게 수정
- 버전 고정은 수정할 수 없을 때의 마지막 수단. 고정하면 사유를 최종 보고에 기재
- 검수 렌더링에는 렌더러가 필요. HWPX는 rhwp 릴리스 바이너리, rhwp 소스 빌드, LibreOffice와 H2Orestart 순으로 확보하고 DOCX는 LibreOffice를 사용. 확보 절차는 references/renderers.md
- 쪽 PNG 생성과 목차 쪽번호 산정에는 poppler-utils(pdftoppm, pdftotext)가 필요. 없으면 render는 PDF까지만 산출하고 build는 목차 쪽번호를 비워 둠
- 내장 양식 글꼴은 나눔고딕이며 flat 제목만 나눔바른고딕. 두 글꼴 모두 한자는 네이버 배포본에만 있음. `fonts`로 설치 상태와 한자 포함 여부를 확인하고 `fonts --setup`으로 내려받기와 대체 글꼴을 설정. 글꼴 정책은 references/renderers.md

## 명령

| 요청 | 명령 |
|------|------|
| 장 체계 보고서 작성 | `build 원고.md 산출.hwpx --profile chapter` (DOCX는 `산출.docx`) |
| 장 없는 보고서 작성 | `build 원고.md 산출.hwpx --profile flat` (DOCX는 `산출.docx`) |
| 유저 양식으로 작성 (HWPX 전용) | `skeleton 양식.hwpx 스켈레톤.hwpx` 후 `build 원고.md 산출.hwpx --profile 스켈레톤.profile.json --skeleton 스켈레톤.hwpx` |
| 내장 양식을 빈 파일로 저장 | `form chapter 양식.hwpx` 또는 `form flat 양식.hwpx` |
| 양식 빈칸 채우기 (HWPX 전용) | `fill 문서.hwpx 치환.json [-o 산출.hwpx]` |
| 기존 HWPX 내용 열람 | `export 문서.hwpx 원고.md [--image-dir 폴더]` |
| 기존 HWPX 재편집 원고 | `export 문서.hwpx 원고.md --profile chapter` (계위 복원. 그림, 각주, 첨자는 복원하지 않음) |
| DOCX 원고화 | `docx2md 문서.docx`로 문단 유형 출력 후 `docx2md 문서.docx 원고.md --map 대응.json` |
| XLSX 원고화 | `xlsx2md 표.xlsx 원고.md [--allow-wide]` |
| 시각 검수 | `render 문서.hwpx [--engine auto\|rhwp\|soffice] [--rhwp 경로] [--outdir 폴더]`, `render 문서.docx [--outdir 폴더]` |
| 구조 검증 | `check 문서.hwpx [--expect "--expect-min-tables 2"]` (스키마, 이미지 매니페스트 정합, rhwp verify), `check 문서.docx` (구성 요약) |
| 글꼴 점검 | `fonts`, `fonts --setup` |

build 옵션

- 산출 형식은 산출 경로의 확장자(.hwpx, .docx)로 결정. 산출 경로를 생략하면 `--format hwpx|docx`(기본 hwpx)와 원고 파일 이름으로 결정
- (`--profile chapter|flat|프로파일.json`) 필수 인자. DOCX는 chapter와 flat만 허용
- (`--page-break chapter|section|none`) 새 쪽을 시작하는 제목 단위. chapter는 장(`#`)마다, section은 장과 절(`##`)마다 새 쪽에서 시작. none은 `---` 줄에서만 쪽을 나눔. 기본 chapter
    - (flat) `#`은 문서 제목 하나이므로 chapter는 none과 같이 `---` 줄에서만 쪽을 나눔. section은 N. 제목(`##`)마다 새 쪽에서 시작
- (`--long-table engine|split`) 머리글 행을 포함하여 25행을 넘는 표(장표)의 처리 방식. engine은 한 표를 쪽 경계에서 나누고 단위 행과 머리글 행을 쪽마다 반복. split은 머리글 행을 붙인 여러 표로 나눔. 기본 engine
- (`--merge auto|explicit|none`) 표 셀 병합 방식. auto는 선행 라벨 열의 연속 동일값과 `^`, `<` 지시를 병합하고 explicit은 지시만 병합. 기본 auto
- (`--numbered-square`) `□ 1. 제목` 줄을 □ 글머리 없이 번호가 붙은 제목으로 출력. 제목이 두 줄로 접히면 둘째 줄을 번호 뒤 글자에 맞춤
- (`--page-number`) 꼬리말 가운데 쪽번호 `- N -`. 기본 OFF. 여러 문서를 하나로 취합할 때 쪽번호가 겹치지 않게 하기 위한 기본값
- (`--toc`) 목차를 문서 앞에 삽입. 기본 OFF
    - (`--toc-depth 1|2|3`) 목차 깊이(1은 장, 2는 절, 3은 소절까지). 기본 2
    - 항목은 제목, 점선 탭, 쪽번호로 구성. 쪽번호는 `--page-number`와 함께 지정한 경우에만 기입
    - 쪽번호는 렌더링으로 산정한 근사값. build가 기입 후 다시 렌더링하여 대조 결과를 출력 (references/layout.md의 목차 절)
    - 목차 스타일이 없는 양식(flat 포함)은 경고 후 목차를 생략
- (`--cover "title=제목;subtitle=부제;date=작성 연월;org=기관명"`) 표지. 기본 OFF. 제목 24pt 굵게, 부제 16pt, 일자 14pt, 기관 16pt 굵게, 가운데 정렬
    - 제목이 길어 표지가 1쪽을 넘을 위험이 있으면 config.py의 표지 값(COVER_로 시작하는 빈 줄 수와 글자 크기)만 조정
- 표지와 목차는 앞 구역에 두고 본문은 새 구역으로 분리. 본문 쪽번호는 1부터 시작
- (`--header "텍스트;align=LEFT|CENTER|RIGHT"`) 머리말. 기본 OFF. 정렬 기본값은 우측. 본문 구역에만 적용
- (`--skeleton 스켈레톤.hwpx`) 유저 양식에서 추출한 스켈레톤 (HWPX 전용)
- (`--rhwp 경로`) 목차 쪽번호 산정에 쓸 rhwp 실행 파일 (HWPX)

fill 치환 JSON은 `{"replace": {"기존 문구": "새 문구"}, "cells": {"라벨 > right": "값"}}` 형식이다. `cells`의 키는 표에서 라벨 문구가 든 셀을 찾은 뒤 방향(left, right, up, down)을 따라 옮겨 간 셀을 가리킨다. 방향은 `>`로 이어 여러 번 쓸 수 있다(예 `"합계 > down > right"`). 라벨 문구가 문서의 표에 두 번 이상 나오면 셀을 특정할 수 없어 실패로 출력되므로 한 번만 나오는 문구를 라벨로 쓴다.

check의 `--expect` 값은 rhwp verify의 기대 조건 인자로 그대로 전달된다. 공백이 든 조건 값은 작은따옴표로 감싼다(예 `--expect "--expect-contains '가상 기획 수치'"`). 표 개수 조건에는 그림을 담은 1열 표도 포함된다. 문구 포함 조건(`--expect-contains`)의 검색 범위는 본문 문단과 표 셀 글자이며 각주와 캡션 글자는 들지 않는다. rhwp가 있고 `--expect`를 지정한 경우에만 기대 조건을 대조한다. HWPX check는 스키마 이슈, 이미지 매니페스트 불일치, 기대 조건 불일치 중 하나라도 있으면 종료 코드 1을 반환한다.

## 절차

- 문서 생성과 편집은 scripts/report.py 명령으로만 수행. 명령을 거쳐야 양식의 스타일, 글머리, 번호 참조가 문서에 그대로 유지됨
- 오류가 나면 메시지를 근거로 원고, 프로파일, 스크립트 중 원인을 찾아 고침. 내장 양식 생성이 실패하면 python-hwpx 버전과 설치 상태를 먼저 확인

1. (기획안) 아래 항목을 한 번에 유저에게 질문하고 답변을 받은 뒤 진행. 유저 요청에 답이 있는 항목은 다시 묻지 않음. 유저가 "바로 실행"을 명시하면 기본값으로 진행
    - (산출 형식) HWPX(한/글) 또는 DOCX(Word). 유저 양식을 쓰는 작업은 HWPX만 가능. 형식은 하나만 고르도록 권장. 두 형식을 함께 만들면 렌더링 검수와 수정이 형식마다 반복되어 작업 문맥(컨텍스트) 사용량이 커지고 검수 품질이 떨어질 수 있음. 유저가 두 형식을 원하면 이 내용을 1줄로 고지하고 그대로 진행
    - (용도) 풀보고서의 장 체계 문서는 chapter, 단독 문서와 풀보고서 삽입용 부분 원고는 flat. 표지와 목차는 용도와 관계없이 선택 요소
    - (양식 차이) 용도를 물을 때 함께 제시. chapter는 제N장, N.N, N.N.N, 가. 제목에 나눔고딕 굵게를 쓰고 캡션 번호가 장마다 다시 시작(표 1-3). flat은 문서 제목, N., N.N 제목에 나눔바른고딕 굵게, 가. 제목에 나눔고딕 굵게를 쓰고 캡션 번호가 문서 전체에 이어짐(표 3). 본문 계위 □, ○, -, ㆍ, ※와 본문 글꼴 나눔고딕은 두 양식이 같음. 목차 스타일은 chapter에만 있음
    - (쪽 나눔) chapter, section, none 중 택일. build가 `HITL: [쪽 나눔]` 줄로 요소 8개 미만인 짧은 절의 수를 알림. section에서는 짧은 절이 든 쪽마다 아래에 빈 공간이 크게 남음
    - (장표) engine, split 중 택일. build가 `HITL: [장표]` 줄로 해당 표를 알림
    - (유저 양식의 스타일 부재) build가 `WARN:`으로 프로파일에 없는 스타일을 알리면 가까운 스타일 파생, 양식에 스타일 추가, 기존 계위 흡수 중 택일
    - (선택 요소) 쪽번호, 목차, 표지, 머리말은 기본 OFF이므로 필요 여부를 질문. 목차는 깊이(장, 절, 소절), 표지는 제목, 부제, 일자, 기관, 머리말은 문구를 함께 질문. 머리말 정렬은 유저가 따로 요청할 때만 우측에서 변경
2. (원고) 아래 계위 규범과 references/manuscript.md의 작성 규칙으로 Markdown 원고 작성
3. (조판) build를 실행하고 출력 줄 머리에 따라 조치
    - (`LINT:`) 원고 결함. 원고를 고친 뒤 재실행
    - (`HITL:`) 유저가 고를 조판 선택지(쪽 나눔, 장표). build는 `--page-break`, `--long-table`을 지정하지 않은 경우에만 출력하므로 1단계에서 정한 항목은 옵션으로 지정하여 실행
    - (`WARN:`) 스타일 부재, 이미지 없음 등 조판 경고
4. (검수) check로 구조를 검증하고 render로 만든 쪽 PNG를 열람하여 references/layout.md의 검수 항목 점검과 자유 검수 수행. 검수 PDF와 PNG는 `--outdir`로 납품 폴더 밖에 저장
    - (열 폭 결함) 자동 산정 열 폭의 결함을 렌더 PNG에서 확인한 표만 원고에 열 폭 줄(references/manuscript.md)을 추가하여 재조판. 첫 조판은 열 폭 줄 없이 수행
5. (보고) 아래 항목을 유저에게 전달
    - 산출 경로, 고친 항목, 사용한 렌더러와 폴백 사유
    - (렌더러 한계) 검수 렌더러는 근사 렌더러이므로 한/글 또는 Word 표시와 다를 수 있다는 안내 1줄
    - (DOCX 목차) 쪽번호 있는 목차를 삽입한 경우 Word가 문서를 열 때 필드 갱신 여부를 묻고 "예"를 누르면 Word 기준 쪽번호로 목차가 갱신된다는 안내 1줄
    - (글꼴 안내) 유저가 문서를 여는 컴퓨터에서 `fonts`를 실행할 수 있는 환경(스킬이 그 컴퓨터에서 실행되거나 그 컴퓨터에 명령을 보낼 수 있는 환경)이면 실행. 양식 글꼴(나눔고딕, flat은 나눔바른고딕 추가)이 모두 설치되어 있고 한자가 모두 있으면 안내 생략. 설치되지 않았거나 한자가 빠진 글꼴이 있으면 해당 글꼴을 짚어 references/renderers.md의 유저 컴퓨터 글꼴 설치 절차를 전달
    - (원격 작업 공간) 유저 컴퓨터를 검사할 수 없는 환경이면 글꼴 안내와 설치 여부 질문을 생략. 유저가 글꼴이나 한자 표시 문제를 말하면 그때 설치 절차를 전달

## 원고 계위 규범

| 원고 표기 | 역할 | chapter | flat |
|------|------|------|------|
| `# 제목` | 장 | 제N장 제목, 새 쪽 | 문서 제목 (가운데, 20pt 굵게) |
| `## 제목` | 절 | N.N 제목 | N. 제목 |
| `### 제목` | 소절 | N.N.N 제목 | N.N 제목 |
| `#### 제목` | 가나다 | 가. 제목 | 가. 제목 |
| `□ 제목` | 논점 | □ | □ |
| `- 서술` | 주장 | ○ | ○ |
| `    - 서술` | 근거 | - | - |
| `        - 서술` | 부연 | ㆍ | ㆍ |
| `※ 부기` | 주석 | ※ | ※ |
| `출처: ` 등 출처 줄 | 출처 | 표나 그림 뒤면 출처 행, 본문 뒤면 직전 문단의 각주 | 같음 |

- 헤더 번호 제거와 자동 부여, 불릿 계위 판정, 인라인 서식, 각주, 표와 그림 표기, 출처와 단위 줄 처리는 references/manuscript.md
- □ 아래 서술, 키워드형과 문장형, 절 번호와 가나다 사용 기준도 references/manuscript.md

## 형식별 차이

- 두 형식은 글꼴, 크기, 굵기, 장평, 자간, 정렬, 여백, 줄 간격, 글머리 기호, 표와 그림 규범이 같음
- DOCX는 내장 양식(chapter, flat)만 지원. 유저 양식(`--skeleton`)과 fill은 HWPX 전용
- DOCX는 장, 절, 소절, 가나다 제목을 Word 기본 제목 스타일에 입혀 탐색 창과 목차 필드가 인식하게 함
- 단위 변환, 캡션 번호 필드, 목차 필드, 각주, 글꼴 표 기록 등 DOCX 대응 규칙은 references/layout.md

## 기존 문서의 원고화

- (DOCX) docx2md 1단계가 스타일명, 들여쓰기, 자동번호, 선두 기호 조합별 건수와 표본을 출력. 조합별 계위 대응을 유저와 확정한 뒤 2단계로 원고 생성. 표 캡션과 그림은 원고에서 보완
- (XLSX) xlsx2md가 시트마다 표 캡션 줄과 파이프 표를 생성. 열이 6개를 넘는 시트는 행열 전환 또는 표 분할을 유저에게 질의. 유저가 그대로 두기로 하면 `--allow-wide`로 경고를 끄고 진행. 캡션 제목, 단위 줄, 출처 줄은 원고에서 보완
- (HWPX) `export --profile`로 계위 원고를 만들고 수정한 뒤 build. 스타일 이름으로 역할을 찾지 못한 문단은 선두 기호와 번호 형식으로 역할을 추정

## 고지

- 본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.
- 한/글, 한컴오피스, HWPX는 한글과컴퓨터의 상표이며 이 도구는 한글과컴퓨터와 제휴 관계가 없는 독립 도구임
