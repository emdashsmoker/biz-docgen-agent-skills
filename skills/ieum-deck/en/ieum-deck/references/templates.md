# Template list

- Templates are grouped into parametric templates, the composite template, the free template and custom slide templates (`own:N`)
- Parametric templates handle slides with a fixed structure: cover, contents, background and purpose, strategy, module overview, schedule, project organization
- The composite template handles analysis and method slides with a cell grid and blocks (layout samples are the recipes in `references/recipes.md`)
- The free template places diagrams that templates and recipes cannot hold directly by coordinate ratios
- Custom slide templates are used only when custom slides are registered (`references/custom-slides.md`)
- The band fields are common to all body templates (secNo, section, chapter, headline, marker, source, accent)
- The page size is set with `meta.layout`
- The builder converts coordinates for each page size
- Text volume in the samples is based on 16:9 (text volume for narrower page sizes is in the page size item of the SKILL.md design system)
- Some sample slides also carry shortened text for the 4:3 and A4 page sizes in `byLayout`

## Selection rules

- Slides with a fixed structure (cover, contents, divider, background and purpose, goal and scope, features, strategy, process, module overview, schedule, project organization) use the matching parametric template
- For analysis, survey design, methods and management plans, first look for a recipe with a matching purpose in `references/recipes.md`
- Simple structures that no recipe covers (full-width table, chart with findings, cards, steps) use table, chart_text, chart_two, cards and steps
- The visual slot of chart_text and chart_two is for charts only
- Typeset slides that put a table, diagram or image in the visual slot with composite
- Replace the chart data, table values and item text of the samples (`assets/proposal-templates.json`, `assets/recipe-demos.json`) with engagement content
- 3-8 free template slides per deck are recommended (more than 8 is a lint WARN)

## Variety criteria

- The variety criteria apply with the same values to every output type (conditions are in the SKILL.md slide variety section)
- Up to 3 slides of the same layout type can run in a row (4 in a row is a lint WARN)
- Task slides choose a different layout type for each Task (if 3 or more Task slides all share one layout type, lint FAIL)
- The number of body layout types is at least 30% of the body slide count (minimum 3 types; below that is a lint WARN)
- One layout type takes at most 40% of the body slides (above that is a lint WARN)

## Table typesetting

- Write several items in a cell as an array (with two or more items, the builder applies bullets and left alignment)
- A bullet marks an item boundary, so text wrapped onto several lines still counts as one item
- Example: `"rows": [["조사 단계", ["문헌 분석", "통계 검토", "전문가 자문"], "1단계"]]`
- A line break inside a string is also typeset as an item break (a bullet per item)
- Bullets on single-item cells are given per line. Write the target lines in the table object as `bulletRows` (array of body row numbers) and `bulletCols` (array of column numbers)
    + The criteria (comparison line condition, whole table condition) are in the `references/writing-rules.md` tables section
    + Numbers start at 0. A row number is the position in `rows` (header row excluded), and a column number is the cell position in the row array (`{"merged": true}` cells included)
    + `bulletRows` leaves out the cells of `labelCols` (array of label column numbers, `[0]` when omitted). A table without a label column uses `"labelCols": []`
    + The builder applies bullets and left alignment to single-item cells in the given lines (empty cells, cells hidden by merging and Harvey ball cells excluded)
    + Example: `"head": ["구분", "A안", "B안", "C안"], "rows": [["장점", ["구축 비용 절감", "기존 체계 연계"], ["확장 용이", "유지보수 단순"], "도입 기간 단축"]], "bulletRows": [0]`
- The cell typesetting rules are common to every template that uses tables (table, task, illustrative, and the table block of free and composite)
- Column widths are computed automatically from the one-line width of the longest cell text in each column
    + Data columns are number columns, Harvey ball columns and symbol columns of two characters or less (role codes, etc.)
    + Two or more consecutive data columns of the same kind get the same width
    + When the one-line width sum is smaller than the table width and 3 or more same-kind data columns run in a row, the spare width goes only to that group (a group forming the table body, such as role codes, years or alternatives)
    + Without such a group, the spare width is split across all columns in proportion to their one-line widths
    + When the one-line width sum exceeds the table width, the longest columns shrink first to the same width (short columns stay on one line, and the word width is kept)
- Column alignment is set for every table at the storyboard stage with `align` (an array of per-column horizontal alignments)
    + Values are "right", "center" and "left"
    + The rules for judging alignment are in the `references/writing-rules.md` tables section
    + Example: `"head": ["연번", "과제명", "기간", "개월", "계약금액"], "align": ["center", "center", "center", "right", "right"]`
- The `align` array has the same length as the column count (a different length gives a build warning)
- Tables without `align` and columns missing from `align` use the default alignment
    + Columns with bullet cells (multi-item cells, cells in given lines) and diagnostic question columns are left-aligned
    + Other columns with only single-item cells are centered, including number columns and Harvey ball columns
    + A table whose judged alignment matches the default alignment may leave out `align`
- The cells of a comparison line are all single-item or all multi-item (a single-item cell outside the given lines follows the column alignment without a bullet)
- Vertical alignment is centered for the whole table
- Set `colW` (width ratios) only when a width unrelated to the text is needed, such as empty fill-in cells
- If the table text fill (the per-column one-line width sum as a share of the table width) is below 60%, a build warning appears
    + Fix it in this order: enrich cell text (add subject, criterion, figures), add information columns (owner, cycle, criterion, output), shrink the cell width
    + Tables with placeholder cells (`[회사 확인]`, etc.) are excluded from the check
- Table cell values ● (held), ◐ (partly held) and ○ (not held) are typeset as circle shapes in the cell center
- Show the Harvey ball legend with the `legend` slot (table template) or a cell note (composite)
- The Harvey ball circle color is the body text color
- Each row height starts from the height its line count needs, and the spare height goes to the lowest rows first until they reach the same height
- Row height caps: 0.5 inch for text-only single-line rows, the height holding 1.3x line spacing for multi-line rows (0.8 inch or less), 0.8 inch for tables with Harvey balls
- Multi-line cells widen line spacing up to 1.3x as far as the row height allows
- The header row height is 0.4 inch (or the height of a two-line header)
- For the table and illustrative templates, when the table hits the row height cap and is shorter than the body, the title and table group are centered vertically in the body
- For rows or columns repeating the same value, decide on merging by the relation of neighboring rows
- Merging uses `merged`. The first merged cell is `{"text": "기획", "rowspan": 3}` (`colspan` for horizontal merges), and cells hidden by the merge are `{"merged": true}`

## Parametric templates

- The height cap of side-by-side panels (bullets, compare, conclusion, cards, the chart_text findings panel) is the height with item spacing widened up to 18pt
- Item spacing in a bullet box widens within the spare height measured in PowerPoint line height (1.4x the font size)
- Panel groups and the Point band are centered vertically in the body
- The 14pt panel title bar (bullets, compare, conclusion, cards, chart_text findings panel, strategy pillar, features tile, staff_card role) is 0.42 inch high (0.09 inch above and below the text line)
- The gap between the row label box (module_overview, task_multi, roadmap) and the content box is 0.14 inch
- compare is typeset as a row-matched comparison when the gap count equals the AS-IS item count and the TO-BE item count
    + Each row gets an AS-IS box, a gap arrow and a TO-BE box
    + Text is 14pt Bold for items, 12pt for evidence, 13pt Bold for gaps (reduced one step at a time if it exceeds the body height)
    + The two boxes share one width fitted to the longest text line, and the group is centered in the body
    + Column titles are AS-IS gray, GAP light theme color, TO-BE theme color (change the GAP title with `gapHead`)
- bullets, cards and conclusion panels are typeset with 14pt items and 12pt evidence (bullets and cards shrink to 11pt if the height runs short)
    + Panels share one width fitted to the longest text line, and the panel group is centered in the body
    + The Point band and the conclusion band have the same width as the panel group
    + If the Point text of bullets or cards runs past 2 lines in the band, the panel group and the band are widened together (up to the body width)
- swot makes the center strategy cells (SO, WO, ST, WT) wider than the left and right factor columns and typesets the four strategy cells in the same format
    + Arrows converging from the four factor cells to the center strategy cells sit between the factor columns and the strategy cells

| Group | template | Use | slots fields | Variable range |
|---|---|---|---|---|
| Cover and divider | cover | Cover. One horizontal line above and one below the title. The title sits exactly between the two lines. client holds only the contracting agency name. Choose the client position with clientPos | title, label, date, client, logo, company | - |
| Cover and divider | contents | Contents | items[] | 2-7 |
| Cover and divider | divider | Divider | no("Ⅰ"), title, items[] | Sections 1-8 |
| Cover and divider | end | Closing | title, company | - |
| Proposal overview | purpose | Background and purpose | leads[{title, sub[], note}], purpose, issues[], leftHead, rightHead, purposeHead, issueHead, client, clientPos | Leads 2-4. Each lead has a one-sentence title and 2-3 evidence items. The purpose box label is purposeHead (default "목적") |
| Proposal overview | scope | Vision, goal, module scope, outputs | vision, goal, goalHead, visionTag, scopeTag, outputTag, modules[{title, items[]}], outputs[text or per-module text array] | Modules 2-5. The goal label text is goalHead (default "본 과업의 최종 목표"). An OUTPUT label sits left of the output row (change the structure labels VISION, SCOPE and OUTPUT with visionTag, scopeTag and outputTag). If outputs is a list of arrays as long as the module count, items align under the module columns as multi-item bullets. If it is a text list, 1-2 items are centered in cells of module column width, 3-5 items take one line, 6-10 items take two lines with up to 5 cells per line |
| Proposal overview | features | Question banner and capability tiles | question, tiles[{title, items[]}] | Tiles 2-4, 1-4 items per tile |
| Proposal overview | strategy | House shape with roof (goal), strategy pillars and base (conclusion) | goal, strategies[{title, items[], result}], conclusion | Strategies 2-4, 4-5 items per strategy (enough to fill the pillar). Pillars share one width. The roof and base are 0.2 inch wider than the pillar group on each side. The gap between tiers is 0.16 inch. Text: roof 16pt (shrinks to 14pt if long), pillar titles and base 14pt, pillar items 12pt |
| Proposal overview | process | Module chevrons and Task boxes | modules[{id, title, tasks[]}], idFormat, titleFormat | Modules 2-7, 2-6 Tasks per module. Put the module number in id (title holds only the module name). Without id, idFormat applies (default "Module {n}"), and the chevron text follows titleFormat (default "M{n}. {t}"). Task boxes are spread so the last box bottom meets the body bottom (box spacing capped at 1.5x the even spacing). Modules are joined with L-shaped connectors. With 6 or more modules, every chevron gets the same auto-adjusted height and font |
| Execution plan | module_overview | Module overview table | tasks[{title, process[], data[], output[]}], rowLabels | Tasks 2-6. List every output in the output array when there are several. All three rows use left-aligned bullets even with a single item (treated as a table where the comparison line condition and the whole table condition always hold. Table typesetting section) |
| Execution plan | task | Task design table and measured sample | leftHead, head[], rows[[item, content]], bulletRows[], bulletCols[], labelCols[], sample{head, table or items or image or chart, tag}, point | Rows 3-6. The design table column titles are head (default "항목", "내용"). Bullet lines for single-item cells of the design table are bulletRows, bulletCols and labelCols (table typesetting section). The sample tag is sample.tag (default Sample) |
| Execution plan | task_multi | Task bundle matrix (for page limits) | tasks[{id, title, items[]}], rowLabels[], freeLabel, idFormat, point | Tasks 2-4. items use the "label : value" format (row alignment condition). The label of the row collecting items not in this format is freeLabel (default "주요 내용"). Without id, idFormat applies (default "Task {n}") |
| Analysis and comparison | bullets | Panels in 1-4 columns | panels[{head, items or text, headFill, fill}], point | Columns 1-4 |
| Analysis and comparison | table | Full-width table | title, legend, head[], rows[][], align[], bulletRows[], bulletCols[], labelCols[], point | Rows 1-16. Column alignment is align, and bullet lines for single-item cells are bulletRows, bulletCols and labelCols (table typesetting section) |
| Analysis and comparison | chart_text | Chart with findings | chartTitle, chart{type, barDir, categories, series, numFmt}, findings[{head, items}] | Findings 1-3. The chart fields are the same as the chart block in `references/recipes.md` |
| Analysis and comparison | chart_two | Two charts side by side | left{title, chart, items}, right{title, chart, items} | - |
| Analysis and comparison | compare | AS-IS, TO-BE, gap | asis{head, items}, tobe{head, items}, gap[], gapHead | Items 2-4. Write each item as a title (text) of about 20 characters and add 1-2 evidence sub-items (sub). Write each gap as an improvement means of about 10 characters per item and match the item count (a one-sentence gap goes in a single gap entry typeset in the strip under the two panels) |
| Analysis and comparison | swot | SWOT | S[], W[], O[], T[], so[], wo[], st[], wt[], labels{S, W, O, T, SO, WO, ST, WT} | 1-4 per cell. The factor cell titles are labels (default "강점 (S)", "약점 (W)", "기회 (O)", "위협 (T)"). The strategy cell titles change with SO, WO, ST and WT of labels |
| Analysis and comparison | cards | N columns of cards | cards[{title, items or text}], point | 2-8 |
| Analysis and comparison | steps | Chevron steps with descriptions | steps[{title, items[]}], stepLabel, point | 3-5. Set the prefix with stepLabel (default STEP, "" shows the title only). Item spacing is spread to the box height automatically. The description box height is capped at 1.3x the item height. The group is centered vertically in the body |
| Analysis and comparison | illustrative | Output example | title, table or image, tag | The tag is tag (default Illustrative) |
| Analysis and comparison | conclusion | Synthesis with conclusion band | panels[{head, items}], conclusion | Panels 2-4. Write panel items as judgment sentences of about 20 characters and add evidence figures as sub-items (sub) |
| Schedule and organization | roadmap | Yearly roadmap by strategy | periods[], lanes[{title, tasks[{text, from, to}]}], laneHead, note | Lanes 2-5. The lane header text is laneHead (default "전략") |
| Schedule and organization | gantt | Schedule | months, weeks, groups[{name, tasks[{name, from, to}]}], reports[{name, at}], groupHead, taskHead, reportHead, monthFormat | 6-12 months. The category column header is groupHead (default "구분"), the task column header is taskHead (default "과업"), the report row group name is reportHead (default "보고회"), and the month header is monthFormat (default "{n}M"). When the row height cap (0.32 inch) leaves spare height, the table is centered vertically in the body |
| Schedule and organization | org | Project organization chart | client, clientNote, pm, pmTitle, qa, qaTitle, advisory, advisoryTitle, advisoryNote, teams[{name, members[], share}], note | Module boxes 2-8 (7 or more are placed in 2 rows automatically). Boxes show staff only |
| Schedule and organization | staff_card | Staff cards | people[{role, name, career[], records[], photo}], recordsHead | 2-6 (used from 4 people). Without photos, the photo column is omitted. The track record strip label is recordsHead (default "주요 실적") |
| Schedule and organization | orgchart | Company organization chart (CEO, advisory board, management support, divisions, teams, staff table, partner network) | ceo, advisory{name, note}, staff{name, note}, units[{name, teams[]}], people[{label, count, ratio}], peopleHead[], network[], leftHead, rightHead, netHead | Divisions 2-8, 1-6 teams per division. Spare height goes to box height, item spacing and connector length in that order. The group then moves down by the remaining height to sit centered vertically |
| Free layout | composite | Cell grid and blocks (`references/recipes.md`) | recipe, cols or rows, regions[{title or caption, block or blocks, note}], flow, rowFlow, numbered, dividers, point, conclusion | Recipe samples have 1-6 cells |
| Free layout | free | Free placement by coordinate ratios | blocks[{kind, x, y, w, h (0-1 ratios), ...}] (at the slide top level or under slots) | 3-8 per deck |
| Free layout | digest | --digest summary | (automatic) | - |

- The placement rules for the project organization chart and the company organization chart follow the SKILL.md project organization section

## Label slots

- The fixed labels of templates and blocks resolve in this order: the slide slot value, then `meta.labels`, then the default (Korean)
    + An empty slot takes the value of the same template (or block) and slot in `meta.labels`
    + Without a `meta.labels` value, the default below is typeset (the default table is `assets/labels.json`)
    + A deck without `meta.labels` is typeset with the same Korean labels as before
- For English decks and non-proposal outputs, set the labels shared by the deck once in `meta.labels` and set only the labels that differ per slide in the slots
- The form of `meta.labels` is `{template or block: {slot: label}}`
    + Nested slots use dotted keys (e.g. `"task": {"sample.head": "..."}`)
    + List labels (rowLabels, head, peopleHead) have the same count as the default
    + Object labels (labels) are merged per key (only the given keys change)
    + In format labels (idFormat, titleFormat, monthFormat), `{n}` is the number and `{t}` the title
    + Any key may be omitted (omitted keys keep the default)
- The Point band label resolves from the slide pointLabel, then meta.pointLabel, then meta.labels.common.pointLabel, then the default
- lint reports unknown template, block and slot names and value type errors as FAIL (a format label missing `{n}` or `{t}` is a WARN)

| Template or block | Slot | Default |
|---|---|---|
| common | pointLabel (the slide pointLabel and meta.pointLabel take precedence) | 수행 Point |
| common | company (the slide company and meta.company take precedence) | 회사명 |
| cover | label | 제안발표자료 |
| contents | title | 목차 |
| end | title | 감사합니다 |
| purpose | leftHead, rightHead, purposeHead, issueHead | 배경 및 필요성, 과업의 목적, 목적, 주요 이슈 및 해결방안 |
| scope | goalHead, visionTag, scopeTag, outputTag | 본 과업의 최종 목표, VISION, SCOPE, OUTPUT |
| process | idFormat, titleFormat | Module {n}, M{n}. {t} |
| module_overview | rowLabels | 단계, 추진과정, 활용자료, 산출물 |
| task | leftHead, head, sample.head, sample.tag | Task 수행 설계, [항목, 내용], 실측 표본 (※ 시안), Sample |
| task_multi | freeLabel, idFormat | 주요 내용, Task {n} |
| compare | asis.head, tobe.head, gapHead | AS-IS, TO-BE, GAP |
| swot | labels{S, W, O, T, SO, WO, ST, WT} | 강점 (S), 약점 (W), 기회 (O), 위협 (T), SO, WO, ST, WT |
| steps | stepLabel ("" shows the title only) | STEP |
| roadmap | laneHead | 전략 |
| gantt | groupHead, taskHead, reportHead, monthFormat | 구분, 과업, 보고회, {n}M |
| org | client, pmTitle, qaTitle, advisoryTitle | 발주기관, 총괄책임자 (PM), 품질관리자 (PL), 자문위원회 |
| staff_card | recordsHead | 주요 실적 |
| orgchart | ceo, leftHead, rightHead, peopleHead, netHead | 대표이사, 조직 구성, 인력 구성, [구분, 인원, 비중], 주요 협력 네트워크 |
| illustrative | title, tag | 참고자료 및 산출물 예시, Illustrative |
| valuechain block | stageLabel, support.label, base.label | 단계, 지원 기능, 공통 기반 |
| porter block | supportLabel, primaryLabel, ownerLabel | 지원 활동, 본원적 활동, 담당 부서 |
| goalsystem block | labels{vision, purpose, goal, performance, strategies, tasks, quant, qual} | 비전, 사업 목적, 사업 목표, 성과 목표, 전략분야, 전략과제 및 세부과제, 정량, 정성 |
| house block | labels{mission, vision, goals, tasks, base} | 미션, 비전, 전략목표, 전략과제, 핵심가치 |
| logicmodel block | labels{issue, goal, beneficiary, input, activity, output, outcome, assumption} | 1. 문제/이슈, 2. 목표, 3. 수혜자, 4. 투입, 5. 활동, 6. 산출, 7. 성과/영향, 8. 가정 |
| canvas block | labels{partners, activities, resources, value, relationships, channels, segments, cost, revenue} | 핵심 파트너, 핵심 활동, 핵심 자원, 가치 제안, 고객 관계, 채널, 고객 세그먼트, 비용 구조, 수익원 |
| language | latin, east_asia | en-US, ko-KR |
| notation | source | [] (no extra tokens) |

- (language) Language tags of the PPTX text (run lang, chart c:lang)
    + latin is the tag of ordinary runs and charts, east_asia the tag of runs that contain Hangul
    + finalize.py applies the values of the build record (`<file name>.build.json`) (the defaults give the same result as before)
- (notation) Extra tokens recognized as note lines. Write them without the colon (e.g. `["Fuente", "Nota"]`)
    + The built-in tokens (※, 출처:, 자료:, Source:, Note:) stay recognized
    + Extra tokens also make only items starting in the "token:" form notes, and the lint note notation check includes them
- The scope structure labels (visionTag, scopeTag, outputTag) are typeset at 10pt, so write them in uppercase Latin letters (other text gets the check_layout 11pt minimum WARN)
- The company name is content, so set it with `meta.company`. Without it, the placeholder is the `common.company` label (default "회사명")
- The fixed text that is not a label slot is placeholders that show only while the content is empty, and numbering symbols unrelated to language
    + Image placeholder box text (이미지, 사진, 표본 화면, 산출물 화면, 로고) and staff placeholders ([인력A], [인력]) disappear once the content is filled
    + The stand-in text of empty custom slide image slots ([기관명], "접수 → 검토 → 승인 → 처리 → 통보", and a description when the source text contains "파쇄") and the sample items of empty chart slots (항목 A, B, C) also disappear once the slot is filled
    + Contents Roman numerals (Ⅰ-Ⅶ), circled numbers (①-⑩), 1., 1-1. and 1) numbering and the ※ mark stay fixed

### English label example

- A complete `meta.labels` example for English decks (the same keys as `assets/labels.json`)
- For a deck where only some slides are in English, set only the labels of the templates those slides use, or set them in the slots of those slides

```json
{"meta": {"labels": {
 "common": {"pointLabel": "Key point", "company": "Company name"},
 "cover": {"label": "Proposal"},
 "contents": {"title": "Contents"},
 "end": {"title": "Thank you"},
 "purpose": {"leftHead": "Background and need", "rightHead": "Purpose of the project", "purposeHead": "Purpose", "issueHead": "Key issues and solutions"},
 "scope": {"goalHead": "Final goal of the project", "visionTag": "VISION", "scopeTag": "SCOPE", "outputTag": "OUTPUT"},
 "process": {"idFormat": "Module {n}", "titleFormat": "M{n}. {t}"},
 "module_overview": {"rowLabels": ["Stage", "Process", "Data used", "Outputs"]},
 "task": {"leftHead": "Task design", "head": ["Item", "Details"], "sample.head": "Measured sample (※ draft)", "sample.tag": "Sample"},
 "task_multi": {"freeLabel": "Key content", "idFormat": "Task {n}"},
 "compare": {"asis.head": "AS-IS", "tobe.head": "TO-BE", "gapHead": "GAP"},
 "swot": {"labels": {"S": "Strengths (S)", "W": "Weaknesses (W)", "O": "Opportunities (O)", "T": "Threats (T)", "SO": "SO", "WO": "WO", "ST": "ST", "WT": "WT"}},
 "steps": {"stepLabel": "STEP"},
 "roadmap": {"laneHead": "Strategy"},
 "gantt": {"groupHead": "Group", "taskHead": "Task", "reportHead": "Reports", "monthFormat": "M{n}"},
 "org": {"client": "Client", "pmTitle": "Project manager (PM)", "qaTitle": "Quality manager (QM)", "advisoryTitle": "Advisory committee"},
 "staff_card": {"recordsHead": "Key projects"},
 "orgchart": {"ceo": "CEO", "leftHead": "Organization", "rightHead": "Staff", "peopleHead": ["Group", "Staff", "Share"], "netHead": "Partner network"},
 "illustrative": {"title": "Reference and output examples", "tag": "Illustrative"},
 "valuechain": {"stageLabel": "Stage", "support.label": "Support functions", "base.label": "Common base"},
 "porter": {"supportLabel": "Support activities", "primaryLabel": "Primary activities", "ownerLabel": "Owner"},
 "goalsystem": {"labels": {"vision": "Vision", "purpose": "Purpose", "goal": "Goal", "performance": "Performance goals", "strategies": "Strategic areas", "tasks": "Strategic tasks\nand sub-tasks", "quant": "Quant.", "qual": "Qual."}},
 "house": {"labels": {"mission": "Mission", "vision": "Vision", "goals": "Strategic goals", "tasks": "Strategic tasks", "base": "Core values"}},
 "logicmodel": {"labels": {"issue": "1. Problem/issue", "goal": "2. Goal", "beneficiary": "3. Beneficiaries", "input": "4. Inputs", "activity": "5. Activities", "output": "6. Outputs", "outcome": "7. Outcomes/impact", "assumption": "8. Assumptions"}},
 "canvas": {"labels": {"partners": "Key partners", "activities": "Key activities", "resources": "Key resources", "value": "Value propositions", "relationships": "Customer relationships", "channels": "Channels", "segments": "Customer segments", "cost": "Cost structure", "revenue": "Revenue streams"}},
 "language": {"latin": "en-US", "east_asia": "ko-KR"}
}}}
```


## free blocks

- (Content boxes) panel{head, items}, bullets{items, fill, line}, text{text, sz, bold, align, fill, line}, label{text, fill}, box{text, fill, line}
- (Data) table{head, rows, align}, chart{type, categories, series, numFmt}
- (Flow) chevron{steps, allChevron}, callout{label, text}, arrow{dir: right or down}, line{color, pt, arrow, dash}
- (Other) image{src, caption, label}, circle{text, fill}, grid{cols, rows, cells[{r, c, span, text, fill: navy or tint}]}
