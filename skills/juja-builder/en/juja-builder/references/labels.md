# Document Labels

- Fixed strings printed into documents, manuscript notation the parser recognizes, docx language tags, and delivered file names are managed as labels
- The default labels produce Korean documents. Without a label file, the document is the same as before
- The source of the defaults is `LABEL_DEFAULTS` in the settings part of scripts/hwpx_report.py. If this document and the settings part disagree, the settings part rules
- A document in a language other than Korean is switched with one label file. The code has no per-language branch

## How to Supply Labels

- A label file is a JSON object. Write only the keys to change. Missing keys keep the default
- Set it with `build workspace --labels file.json` or `check <check> workspace --labels file.json`
    + A path set for a workspace is recorded under `labels` in state.json. Later check and build runs use the same labels without the option
    + `--labels none` clears the record
    + A single-manuscript build (`build manuscript.md output.docx`) applies the file to that run only, without a record
- Unknown keys, format errors, and placeholders that a key does not allow stop build and check with ERROR and a list of the errors
- The label file changes how manuscript notation is recognized, so it is part of the check all fingerprint. After changing the label file, rerun check all, then build
- Notation recognition (notation) also feeds the checks, so for manuscripts in another language set the label file before the first check

## Key Table

| Key | Meaning | Default | English example |
|---|---|---|---|
| `formats.chapter` | chapter heading format (TOC entries, page number matching) | the active profile value. Proposal and planning report `{r}. {t}`, pre-diagnosis report `제{n}장 {t}` | `Chapter {n}. {t}` |
| `formats.chapter_label` | number cell of chapter bands and divider pages | proposal and planning report `{r}`, pre-diagnosis report `제{n}장` | `Chapter {n}` |
| `formats.section` | section heading format | proposal and planning report `{s}. {t}`, pre-diagnosis report `{c}.{s} {t}` | keep the default |
| `formats.subsection` | subsection heading format | proposal and planning report `{g} {t}`, pre-diagnosis report `{c}.{s}.{ss} {t}` | keep the default |
| `formats.item` | item heading format | proposal and planning report `{i}) {t}`, pre-diagnosis report `{g} {t}` | keep the default |
| `letters.items` | letter sequence of the 가나다 level (a string or a list of strings) | `가나다라마바사아자차카타파하` | `abcdefghijklmnopqrstuvwxyz` |
| `letters.format` | letter notation of the 가나다 level. `{g}` in formats | `{x}.` | `({x})` |
| `toc.title` | table of contents title | `목  차` | `Contents` |
| `toc.tables` | list of tables title (pre-diagnosis report) | `표 목차` | `List of Tables` |
| `toc.figures` | list of figures title (pre-diagnosis report) | `그림 목차` | `List of Figures` |
| `caption.table.label` | word of numbered captions | `표` | `Table` |
| `caption.table.open`, `caption.table.close` | caption brackets. Also used for unnumbered captions `<title>` | `<`, `>` | keep the default |
| `caption.table.seq` | name of the docx caption number field (SEQ). label if absent | none (`표`) | none (`Table`) |
| `caption.figure.label` | word of numbered captions | `그림` | `Figure` |
| `caption.figure.open`, `caption.figure.close` | caption brackets | `[`, `]` | keep the default |
| `caption.figure.seq` | name of the docx caption number field | none (`그림`) | none (`Figure`) |
| `notation.source` | source line tokens (added only) | `출처`, `자료`, `주` (`주` only as `주:`. `(주)` abbreviates 주식회사 (Inc.), so it is excluded) | `Source`, `Note` |
| `notation.unit` | unit line tokens (added only) | `단위` | `Unit` |
| `notation.table` | table caption tokens (added only) | `표` | `Table` |
| `notation.figure` | figure caption tokens (added only) | `그림` | `Figure` |
| `language.latin` | Latin language tag of docx default runs | `en-US` | `en-US` |
| `language.east_asia` | East Asian language tag of docx default runs | `ko-KR` | `ko-KR` |
| `output.proposal` | delivered file name of the proposal | `제안서` | `proposal` |
| `output.report` | delivered file name of the pre-diagnosis report | `사전진단보고서` | `pre-diagnosis-report` |
| `output.plan` | delivered file name of the planning report | `기획보고서` | `planning-report` |

- Format placeholders are `{n}` chapter number, `{r}` Roman chapter number, `{c}` chapter, `{s}` section, `{ss}` subsection, `{g}` 가나다 letter (letters.format applied), `{i}` item number, `{t}` title
    + Placeholders allowed per key: chapter `{n}` `{r}` `{t}`, chapter_label `{n}` `{r}`, section `{c}` `{s}` `{t}`, subsection `{c}` `{s}` `{ss}` `{g}` `{t}`, item `{i}` `{g}` `{t}`
- formats override the formats of the active profile (the output type or `build --profile`)
    + The proposal and planning report formats (Ⅰ., 1., 가., 1)) do not depend on language except the 가나다 letters. Change the letters with letters
    + Change `제{n}장` of the pre-diagnosis report with formats.chapter and formats.chapter_label
    + Using the same label file for a proposal changes the proposal's chapter numbers too. Keep a file with formats for the pre-diagnosis report only
- notation adds tokens after the default tokens. Default notation such as `출처:`, `(출처)`, `<표>`, `[그림]`, and `(단위: )` stays recognized
    + An added token plays the same role in the same place. `Source: organization (year), material` and `(Source) organization` are source lines, `(Unit: KRW million)` is a unit line, `<Table> title` is a table caption
    + Matching is case-sensitive. If another spelling is needed, list it as well
- Caption text is `{open}{title}{close}` for unnumbered captions and `{open}{label} {chapter}-{number}{close} {title}` for numbered captions
- The default Latin tag en-US prevents line break defects in the LibreOffice render review. With Latin ko-KR, LibreOffice breaks English words (govern|ments) and numbers (3,|456) mid-token
- output is a file name without path separators. `--format` adds the extension

## English Example

- A complete example for the proposal and the planning report. Chapter numbers stay Roman

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

- For the pre-diagnosis report, add the formats entry below to the example above

```
  "formats": {"chapter": "Chapter {n}. {t}", "chapter_label": "Chapter {n}"},
```

- Resulting text: `Contents`, `List of Tables`, `<Table 1-1> title`, `[Figure 1-1] title`, `(a) subsection title`, chapter band `Chapter 1`, delivered file `납품/proposal.docx`

## Manuscripts in Another Language

- Manuscript notation may use the tokens added by the label file or the default Korean tokens. The directive lines `(장표: )`, `(폭: )`, and `(삽입: 모듈총괄표)` stay in Korean (they are not printed)
- Task labels ((목적), (산출물), and so on) are manuscript content, so write them in the manuscript language (for example (Purpose), (Deliverables))
- Skip the Korean-specific checks with `check all --skip` (SKILL.md Checks section). The skip and its reason are recorded in 05_점검기록.md and state.json
- The render review applies the same criteria. If a long chapter label (`Chapter 10`) wraps to two lines in the number cell of the chapter band or divider page, switch to a short label (`Ch. {n}`) or adjust `label_w` of `BAND_STYLE` and the profile's `chapter_band` in the settings part of proposal.py

## Items Outside the Labels

- Roman chapter numbers (Ⅰ, Ⅱ) and level symbols (□, ○, -, ·, ※). They do not depend on language
- Style names (장 제목, 논점, and so on) and the font name (나눔바른고딕). They appear in the style lists of 한/글 and Word and are not printed as body text
- hwpx package metadata (language `ko` and dates in content.hpf) and the style language code (langID 1042). Values of the python-hwpx blank document
- Workspace file and folder names (원고/, 납품/, 05_점검기록.md, and so on) and Korean markers of design files. Fixed markers the scripts read
- Cover, header, and document title. The values of `--cover`, `--header`, and `--title` are used as given
