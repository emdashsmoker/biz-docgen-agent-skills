# 문서 라벨

- 문서에 찍히는 고정 문자열, 원고에서 인식하는 표기, docx 언어 태그, 납품 파일명을 라벨로 관리
- 기본 라벨은 한국어 문서를 만듦. 라벨 파일이 없으면 종전과 같은 문서
- 기본값의 원천은 scripts/hwpx_report.py 설정부의 `LABEL_DEFAULTS`. 이 문서와 설정부가 어긋나면 설정부가 기준
- 한국어가 아닌 문서는 라벨 파일 1개로 전환. 코드에 언어별 분기는 없음

## 지정 방법

- 라벨 파일은 JSON 객체. 바꿀 키만 적음. 빠진 키는 기본값
- `build 작업폴더 --labels 파일.json` 또는 `check 점검 작업폴더 --labels 파일.json`으로 지정
    + 작업폴더에서 지정한 경로는 state.json의 `labels`에 기록. 이후 check와 build는 옵션 없이도 같은 라벨을 씀
    + 기록 해제는 `--labels none`
    + 단일 원고 build(`build 원고.md 산출.docx`)는 기록 없이 그 실행에만 적용
- 모르는 키, 형식 오류, 쓸 수 없는 자리 표시는 build와 check가 ERROR로 중단하고 오류 목록을 출력
- 라벨 파일은 원고 표기 인식을 바꾸므로 check all 지문에 포함. 라벨 파일을 바꾸면 check all 재실행 후 build
- 표기 인식(notation)이 판정에도 쓰이므로 다른 언어 원고는 첫 check 전에 라벨 파일을 지정

## 키 표

| 키 | 의미 | 기본값 | 영어 예시 |
|---|---|---|---|
| `formats.chapter` | 장 제목 서식 (목차 항목, 쪽번호 대조) | 활성 프로파일 값. 제안서와 기획보고서 `{r}. {t}`, 사전진단보고서 `제{n}장 {t}` | `Chapter {n}. {t}` |
| `formats.chapter_label` | 장 밴드와 간지의 번호 칸 | 제안서와 기획보고서 `{r}`, 사전진단보고서 `제{n}장` | `Chapter {n}` |
| `formats.section` | 절 제목 서식 | 제안서와 기획보고서 `{s}. {t}`, 사전진단보고서 `{c}.{s} {t}` | 기본값 유지 |
| `formats.subsection` | 항 제목 서식 | 제안서와 기획보고서 `{g} {t}`, 사전진단보고서 `{c}.{s}.{ss} {t}` | 기본값 유지 |
| `formats.item` | 목 제목 서식 | 제안서와 기획보고서 `{i}) {t}`, 사전진단보고서 `{g} {t}` | 기본값 유지 |
| `letters.items` | 가나다 계위의 글자 순서 (문자열 또는 문자열 목록) | `가나다라마바사아자차카타파하` | `abcdefghijklmnopqrstuvwxyz` |
| `letters.format` | 가나다 계위의 글자 표기. 서식의 `{g}` | `{x}.` | `({x})` |
| `toc.title` | 목차 제목 | `목  차` | `Contents` |
| `toc.tables` | 표 목차 제목 (사전진단보고서) | `표 목차` | `List of Tables` |
| `toc.figures` | 그림 목차 제목 (사전진단보고서) | `그림 목차` | `List of Figures` |
| `caption.table.label` | 번호 캡션의 낱말 | `표` | `Table` |
| `caption.table.open`, `caption.table.close` | 캡션 괄호. 무번호 캡션 `<제목>`에도 적용 | `<`, `>` | 기본값 유지 |
| `caption.table.seq` | docx 캡션 번호 필드(SEQ) 이름. 없으면 label | 없음(`표`) | 없음(`Table`) |
| `caption.figure.label` | 번호 캡션의 낱말 | `그림` | `Figure` |
| `caption.figure.open`, `caption.figure.close` | 캡션 괄호 | `[`, `]` | 기본값 유지 |
| `caption.figure.seq` | docx 캡션 번호 필드 이름 | 없음(`그림`) | 없음(`Figure`) |
| `notation.source` | 출처 줄 표기 (추가만) | `출처`, `자료`, `주` (`주`는 `주:`만 인식. `(주)`는 주식회사 약칭이라 제외) | `Source`, `Note` |
| `notation.unit` | 단위 줄 표기 (추가만) | `단위` | `Unit` |
| `notation.table` | 표 캡션 표기 (추가만) | `표` | `Table` |
| `notation.figure` | 그림 캡션 표기 (추가만) | `그림` | `Figure` |
| `language.latin` | docx 기본 글자의 라틴 언어 태그 | `en-US` | `en-US` |
| `language.east_asia` | docx 기본 글자의 동아시아 언어 태그 | `ko-KR` | `ko-KR` |
| `output.proposal` | 제안서 납품 파일명 | `제안서` | `proposal` |
| `output.report` | 사전진단보고서 납품 파일명 | `사전진단보고서` | `pre-diagnosis-report` |
| `output.plan` | 기획보고서 납품 파일명 | `기획보고서` | `planning-report` |

- 서식의 자리 표시는 `{n}` 장 번호, `{r}` 로마자 장 번호, `{c}` 장, `{s}` 절, `{ss}` 항, `{g}` 가나다 글자(letters.format 적용), `{i}` 목 번호, `{t}` 제목
    + 키마다 쓸 수 있는 자리 표시: chapter `{n}` `{r}` `{t}`, chapter_label `{n}` `{r}`, section `{c}` `{s}` `{t}`, subsection `{c}` `{s}` `{ss}` `{g}` `{t}`, item `{i}` `{g}` `{t}`
- formats는 활성 프로파일(산출 유형 또는 `build --profile`)의 서식을 덮어씀
    + 제안서와 기획보고서의 서식(Ⅰ., 1., 가., 1))은 가나다 글자 외에 언어와 무관. 가나다 글자는 letters로 바꿈
    + 사전진단보고서의 `제{n}장`은 formats.chapter와 formats.chapter_label로 바꿈
    + 같은 라벨 파일을 제안서에 쓰면 제안서의 장 번호도 바뀜. formats를 담은 파일은 사전진단보고서 전용으로 둠
- notation은 기본 표기 뒤에 표기를 추가. `출처:`, `(출처)`, `<표>`, `[그림]`, `(단위: )` 같은 기본 표기는 계속 인식
    + 추가 표기는 같은 자리에서 같은 역할. `Source: 기관(연도), 자료명`과 `(Source) 기관`은 출처 줄, `(Unit: KRW million)`은 단위 줄, `<Table> 제목`은 표 캡션
    + 대소문자를 구분. 다른 철자가 필요하면 목록에 함께 적음
- 캡션 문구는 무번호 캡션 `{open}{제목}{close}`, 번호 캡션 `{open}{label} {장}-{번호}{close} {제목}`
- language 기본값의 라틴 en-US는 LibreOffice 렌더링 검수의 줄바꿈 결함 방지. 라틴을 ko-KR로 두면 영문 낱말(govern|ments)과 숫자(3,|456) 중간에서 줄이 바뀜
- output은 경로 구분자 없는 파일명. 확장자는 `--format`이 붙임

## 영어 예시

- 제안서와 기획보고서용 완성 예시. 장 번호는 로마자 그대로 둠

```
{
  "letters": {"items": "abcdefghijklmnopqrstuvwxyz", "format": "({x})"},
  "toc": {"title": "Contents", "tables": "List of Tables", "figures": "List of Figures"},
  "caption": {"table": {"label": "Table"}, "figure": {"label": "Figure"}},
  "notation": {"source": ["Source", "Note"], "unit": ["Unit"], "table": ["Table"], "figure": ["Figure"]},
  "language": {"latin": "en-US", "east_asia": "ko-KR"},
  "output": {"proposal": "proposal", "report": "pre-diagnosis-report", "plan": "planning-report"}
}
```

- 사전진단보고서용은 위 예시에 아래 formats 항목을 더함

```
  "formats": {"chapter": "Chapter {n}. {t}", "chapter_label": "Chapter {n}"},
```

- 결과 예시는 `Contents`, `List of Tables`, `<Table 1-1> 제목`, `[Figure 1-1] 제목`, `(a) 항 제목`, 장 밴드 `Chapter 1`, 납품 파일 `납품/proposal.docx`

## 다른 언어 원고의 진행

- 원고 표기는 라벨 파일의 추가 표기나 기본 한국어 표기 중 어느 것이든 씀. 지시 줄 `(장표: )`, `(폭: )`, `(삽입: 모듈총괄표)`는 한국어 그대로 씀(문서에 찍히지 않음)
- Task 라벨((목적), (산출물) 등)은 원고 내용이므로 원고 언어로 씀(예: (Purpose), (Deliverables))
- 한국어 전용 점검은 `check all --skip`으로 생략(SKILL.md 점검 절). 생략과 사유는 05_점검기록.md와 state.json에 기록
- 렌더링 검수는 같은 기준으로 수행. 긴 장 라벨(`Chapter 10`)이 장 밴드나 간지의 번호 칸에서 두 줄로 접히면 짧은 라벨(`Ch. {n}`)로 바꾸거나 proposal.py 설정부 `BAND_STYLE`과 프로파일 `chapter_band`의 `label_w`를 조정

## 라벨 대상이 아닌 항목

- 로마자 장 번호(Ⅰ, Ⅱ)와 계위 기호(□, ○, -, ·, ※). 언어와 무관
- 스타일 이름(장 제목, 논점 등)과 글꼴 이름(나눔바른고딕). 한/글과 Word의 스타일 목록에 보이며 본문 글자로 찍히지 않음
- hwpx 패키지 메타데이터(content.hpf의 언어 `ko`와 일시)와 스타일 언어 코드(langID 1042). python-hwpx 빈 새 문서의 값
- 작업폴더의 파일명과 폴더명(원고/, 납품/, 05_점검기록.md 등)과 설계 파일의 한국어 표지. 스크립트가 읽는 고정 표지
- 표지, 머리말, 문서 제목. `--cover`, `--header`, `--title` 값을 그대로 씀
