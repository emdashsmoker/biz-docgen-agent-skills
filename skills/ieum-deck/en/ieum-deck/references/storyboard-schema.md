# storyboard.json schema

- The model writes one intermediate output: the storyboard
- build.js always typesets the same PPTX from the same storyboard
- Colors and fonts come from `meta.theme`, `meta.themeColors` and `scripts/tokens.js`
- The build starts only when lint.py exits with code 0 (any remaining WARN fails)

## meta

| Field | Description |
|---|---|
| title, author, company | File metadata. company is the company name text. Without a logo, the cover and closing slides show the company name |
| kind | proposal_new, proposal_convert, general (report meeting deck, general planning PPT), report (report-style PPT), brief (briefing deck). A value starting with proposal, or an rfp entry, makes lint run the RFP checks and the score weight checks |
| layout | 16:9 (default), A4, 10.83, 4:3. On page sizes narrower than 16:9, shorten box text by the body width ratio (A4 87.7%, 10.83 81.2%, 4:3 75.0%) |
| headlineStyle | noun (noun-ending style, default), polite (polite style) |
| marker | Marker shape. square (default), bar, triangle |
| pointLabel | Label text of the Point band (default "수행 Point"). Can also be set per slide |
| labels | Object that sets the fixed template and block labels, language tags and extra note tokens for the whole deck. The form is {template or block: {slot: label}} (meta.labels section below). Omitted, the Korean default labels apply |
| lineBreak | Line break unit. word (word-level, default), char (character-level). finalize.py writes it on every paragraph property (eaLnBrk, latinLnBrk) |
| theme | navy (default), mono. Custom colors go in themeColors |
| themeColors | Custom theme colors. Put a 6-digit base color hex code in base and the build computes the full theme except textMuted (e.g. {"base": "1B4332"}). Color keys written alongside take priority over computed values (the color key list and contrast minimums are in the themeColors color keys section below). Without navyRamp, the chart series colors are the final navy, navyPastel, navyPastel2 and a computed 4th color. A format error gives a lint FAIL and a build error. A contrast below the minimum gives a lint WARN |
| track | Wording track. rnd, mgmt, general |
| final | If true, lint checks remaining placeholders as FAIL (set right before the completion report) |
| ownDeck | Path to the custom slide own-deck.json. A path relative to the storyboard file is allowed. If unset, the IEUM_DECK_OWN environment variable is used (`references/custom-slides.md`) |
| pageLimit | Page limit (slide count) set by the contracting agency. Setting it allows task_multi bundle slides |
| structure | module (default), plan (R&D plan presentation), sections (non-R&D open call presentation, report-style PPT, briefing deck). plan and sections check full item coverage instead of the module and Task checks |
| chapters | Chapter list. e.g. ["Ⅰ. 제안개요", ...] |
| rfp.tasks | [{id: "T1", text, module}] Every RFP work item (과업 세부내용). With structure plan, list the plan items. With sections, list the RFP required items. The ID is for internal tracking in the section ledger |
| rfp.moduleTasks | [{id: "M1-T2", title, rfp: ["T1", "T3"], rfpNamed}] Tasks designed by the bidder. rfpNamed is true when title is the name set by the RFP (exempt from the sample module name check) |
| rfp.evalItems | [{id: "A-1", name, score, quantitative}] Detailed evaluation items |
| rfp.wording | [{standard, variants: []}] Standard spelling of key wording and the variant spellings to replace |

### meta.labels

- Sets label slot values that would otherwise repeat on every slide (cover label, gantt headers, module overview row labels and so on) once per deck
- The resolution order is the slide slot value, then meta.labels, then the default (`assets/labels.json`)
- The keys are template or composite block names and slot names (all keys, defaults and an English example are in the label slots section of `references/templates.md`)
    + common.pointLabel: Point band label (meta.pointLabel takes precedence when set)
    + language.latin, language.east_asia: language tags of the PPTX text (default en-US, ko-KR for runs that contain Hangul)
    + notation.source: extra tokens recognized as note lines (the built-in tokens ※, 출처:, 자료:, Source:, Note: stay)
- Any key may be omitted (omitted keys keep the default)
- Unknown names and type errors are lint FAILs
- Example: `"labels": {"cover": {"label": "Proposal"}, "contents": {"title": "Contents"}, "gantt": {"groupHead": "Group", "taskHead": "Task", "reportHead": "Reports"}, "language": {"latin": "en-US"}}`

### themeColors color keys

- The contrast minimum is the luminance contrast (WCAG) between the color key fill and the text color typeset on it

| Color key | Where it is used | Text on it | Contrast minimum |
|---|---|---|---|
| navy | Label cells, chevrons, markers, 1st chart series (navyRamp 0) | White | 4.5 |
| navyDeep | Conclusion band, question banner, roof and base | White | 4.5 |
| navyPastel | Pyramid 2nd tier, dark funnel band, market size middle circle, 2nd chart series (navyRamp 1) | White | 3.0 |
| navyPastel2 | Pyramid 3rd tier, light funnel band, market size outer circle, 3rd chart series (navyRamp 2) | Body text color | 3.0 |
| navyRamp 3 | 4th chart series, top funnel band | Body text color | 3.0 |
| tintNavy, tintHead, tintBg | Pyramid tiers 4-5, header cells, background tint | Body text color | 4.5 |
| textMuted | AS-IS head cell, schedule bars, text color of sources, footnotes and axis ends | White (on a white background when used as text color) | 3.0 |

- The matrix focus quadrant and tint-filled grid cells with color navy put navy text on a tintHead fill
- When navy and tintHead have a contrast below 4.5, slides that draw these two elements get a build warning (colors keep the specified values)

## slides[] common fields

| Field | Description |
|---|---|
| id | Unique ID. S001 format recommended |
| template | Template name (`references/templates.md`). Layout samples for composite are in `references/recipes.md`. For a registered custom slide, "own:N" |
| secNo | Section number. "1." format recommended. The builder corrects "01" or "1" to "1." |
| section, chapter | Section title in the band and the chapter tracker on the right. For module slides, section takes the `[Module 1] 모듈명` format |
| headline | Conclusion sentence in 1-2 lines (50 characters per line, 100 for 2 lines. On A4, 43 characters per line. On 10.83, 40 characters per line. On 4:3, 37 characters per line. Hangul-equivalent characters). Omit it for templates without a band (cover, contents, divider, end) and for bandMode blank slides |
| accent | One emphasized phrase inside the headline (red) |
| marker | Marker text. Over 30 characters (Hangul equivalent) is a lint FAIL. An empty value also omits the marker shape |
| bandMode | Forced band mode. full (default), noMarker, headerOnly, blank |
| slots, panels, blocks | Content per template (`references/templates.md`) |
| source | Source line. String or array |
| footnotes | Footnote array. Numbered 1), 2) automatically and placed above the source line |
| markerNote | Subtitle to the right of the marker (unit, reference date, etc.) |
| rfpTasks, moduleTasks, evalItems | Lists of matching IDs. lint checks full coverage and score attribution |
| allowCount | true when the headline uses a count set by the RFP (exempt from the number declaration check) |
| notes, digest | Speaker notes, --digest summary sentence |
| factSource | Source of company facts. Name of the user-provided material or the confirmation date |
| byLayout | Text for specific page sizes. Format: `{"4:3": {"slots.regions.1.block.items": [...]}}`. The key is the page size name (comma-separated for several). The value maps dot paths (array items numbered from 0) to replacement values. Only values under a key matching the build page size are replaced. A missing path gives a build error and a lint FAIL |

- A proposal storyboard (kind starts with proposal, or meta.rfp exists) requires meta.rfp.tasks (lint FAIL if missing)
- If a proposal storyboard has structure module, meta.rfp.moduleTasks is also required (lint FAIL if missing)
- The module ID is taken from the moduleTasks id prefix (M1 in M1-T2)
- The template of a module overview slide is module_overview or a custom slide in the module_overview role
- The moduleTasks of a module overview slide list every Task of that module
- The moduleTasks of module overview slides are excluded from the Task slide appearance count
- Place the project organization chart (org) and the staffing table together
- lint recognizes as staffing tables: staff_card, and table and composite slides with "투입인력" in the marker or section title (in English, "Staffing", "Key staff", "Project staff" or "Staff plan")
- lint recognizes names regardless of job title in: the pm, qa and team member cells of the organization chart, the name cells of tables whose header row has a name column (성명, 이름, Name), rows labeled 성명, and staff_card name, taking the name before the cell text
- Other text is recognized when it is "[인력A]" or "name + consulting firm or research institute title" (e.g. 수석컨설턴트, 수석위원, 책임연구원, Senior Manager)
- English names are recognized as 2-3 words starting with a capital ("Jane Kim"); in free text, only when a title follows a comma, as in "Jane Kim, Senior Consultant"

### Table fields

- Fields that hold a table use head (header row text array), rows (row array), align (per-column horizontal alignment array) and colW (column width ratio array)
- These fields are the slots of the table template, the table of illustrative, the sample.table of task, and the table blocks of free and composite
- align is written for every table with "right", "center" and "left", and its length equals the column count (a different length gives a build warning)
- The align rules (quantity columns right, identifier and short text columns centered) and the default alignment when omitted are in `references/templates.md` table typesetting

## Section ledger ledger.json

- Structure: {"slides": [{"id", "chapter", "section", "headline", "rfpTasks": [], "moduleTasks": [], "evalItems": [], "template", "status"}]}
- The ledger slide list matches the storyboard slide list one to one
- lint compares only the list and order of slide ids (a mismatch is a FAIL)
- Update the other fields, such as headline, mapped IDs and status, together whenever the storyboard changes

## Minimal example

```json
{"meta": {"title": "○○ 용역 제안발표자료", "kind": "proposal_new", "layout": "16:9", "headlineStyle": "noun", "track": "general",
  "rfp": {"tasks": [{"id": "T1", "text": "성과평가 현황 조사"}], "moduleTasks": [{"id": "M1-T1", "title": "현황 조사", "rfp": ["T1"]}],
          "evalItems": [{"id": "A-1", "name": "과업 이해도", "score": 10, "quantitative": false}], "wording": [{"standard": "성과평가 지표", "variants": ["성과지표체계"]}]}},
 "slides": [
  {"id": "S001", "template": "cover", "slots": {"title": "○○ 용역", "client": "발주기관", "date": "2026. 09."}},
  {"id": "S002", "template": "purpose", "secNo": "1.", "section": "배경 및 목적", "chapter": "Ⅰ. 제안개요", "headline": "본 과업은 ...수립을 목적으로 추진", "marker": "과업의 배경 및 목적", "evalItems": ["A-1"], "slots": {"leads": [{"title": "(제도 변화) ...", "sub": ["...", "..."]}], "purpose": "...", "issues": ["(자료 접근) ..."]}},
  {"id": "S003", "template": "composite", "secNo": "1.", "section": "[Module 1] 현황 조사", "chapter": "Ⅲ. 사업수행계획", "headline": "...", "marker": "이해관계자 면담 설계", "moduleTasks": ["M1-T1"], "rfpTasks": ["T1"], "slots": {"recipe": "interview_plan", "cols": [1, 1, 1], "regions": [{"title": "면담 개요", "block": {"kind": "labeled", "rows": [{"label": "목적", "text": "..."}]}}, {"title": "면담 방식", "block": {"kind": "bullets", "items": ["..."]}}, {"title": "진행 절차", "block": {"kind": "flow", "dir": "v", "nodes": [{"text": "..."}]}}]}},
  {"id": "S010", "template": "task", "secNo": "1.", "section": "[Module 1] 현황 조사", "chapter": "Ⅲ. 사업수행계획", "headline": "...", "marker": "Task 1. 현황 조사", "moduleTasks": ["M1-T1"], "rfpTasks": ["T1"], "slots": {"rows": [["조사 대상", "..."]], "sample": {"items": ["..."]}, "point": "..."}}
 ]}
```
