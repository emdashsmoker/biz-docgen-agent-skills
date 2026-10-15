# composite recipes

- The composite template typesets one analysis slide with a cell grid and blocks
- The storyboard holds only grid ratios, block kinds and text
- `scripts/composite.js` computes the cell and block coordinates
- A recipe is a sample of a grid and block combination that recurs in planning and consulting slides
- The sample slide of each recipe is in `assets/recipe-demos.json`
- Samples are looked up by the `slots.recipe` value
- The lint slide variety check counts `composite:<recipe name>` as one layout type

## Procedure

1. Find the content type of the slide in the use column of the recipe list
2. Find the sample with the same `recipe` value in `assets/recipe-demos.json` and copy its `slots`
3. Replace the sample text and sample figures (○○, example figures) with engagement content
4. Fill every item in the required content column (ask the user for items without material)
5. Check overflow and fill with the build warnings and the `check_layout.py` result

- Match the cell count to the number of content units
- Match the item count in a block to the material volume
- If no recipe fits, combine grids and blocks directly
- Leave `recipe` empty for a directly combined composite
- composite slides without `recipe` count as the same layout type when the grid cell count and the block kind combination are the same
- When a direct combination repeats within one deck, give it a recipe name of lowercase letters and underscores
- Company fact recipes (`company_profile`, `finance_status`, `record_cards`, `infra_tiles`, `pm_profile`, `case_card`) carry `factSource` (lint WARN if missing)

## Grid

| Field | Description |
|---|---|
| `slots.cols` | Array of cell width ratios for a one-row grid. e.g. `[1, 1.2]` |
| `slots.rows` | Multi-row grid. `[{"h": row height ratio, "cols": [cell width ratios]}]` |
| `slots.regions` | Array of cell content. Listed from the top-left cell in row order |
| `regions[].title` | Cell title. Shown as centered text with a gray underline |
| `regions[].caption` | Cell caption. Shown as one bold left-aligned line (set only one of this and `title`) |
| `regions[].block` | One block for the cell |
| `regions[].blocks` | Array of blocks stacked top to bottom in the cell. `h` per block is the height ratio (default 1) |
| `block.caption` | Caption above a block. Used as a per-block title when several blocks are stacked in one cell (the caption of an `image` block is typeset as a description under the image) |
| `regions[].note` | Note under the cell. The builder adds ※ if it is missing |
| `slots.flow` | If true, right arrows between cells in the same row |
| `slots.rowFlow` | If true, down arrows between rows |
| `slots.numbered` | If true, ①, ②, ③ numbers before cell titles |
| `slots.dividers` | If true, gray divider lines between cells and rows (quadrant chart layout). Vertical lines at the same position in each row join into one line (crossing the horizontal line) |
| `slots.point` | Point band text under the body (the label is the slide `pointLabel`, then `meta.pointLabel`, then `meta.labels.common.pointLabel`). Use it only for judgment criteria, formulas, follow-up links, selection reasons, timing or principles that are not in the headline or body |
| `slots.conclusion` | Conclusion band text under the body |

- A build warning appears when the cell count differs from the `regions` count
- Gaps between cells and rows are fixed by constants at the top of `composite.js`
    + 0.3 inch between cells (0.6 inch with `flow` or `dividers`)
    + 0.3 inch between rows (0.45 inch with `rowFlow`, 0.5 inch with `dividers`)
    + 0.2 inch between blocks in one cell
- (Natural height) The height a block aims for when row heights are set
- (Holding height) The upper limit to which a block can grow without leaving its boxes empty
- Blocks that measure content height (`table`, `bullets`, `text`, `stack`, `labeled`, `grid`, `vsteps`, `chevrons`, `flow`, `numbers`, `valuechain`, `zones`) take 1.6x the content height as the natural height
- `summary` takes the unenlarged content height as the natural height
- `tree` and `governance` compute the natural height from the default box height and connector length
- `timeline` computes the natural height from the event box text, and `funnel` from the per-stage criteria text
- `pyramid`, `matrix` and `cycle` take the preferred height as the natural height
- Diagram blocks (`chart`, `flowchart`, `logicmodel`, `goalsystem`, `house`, `porter`, `canvas`, `market`, `image`) fill the cell height
- For rows without a diagram block, the builder sets the height from the content height
- Row height ratios (`rows[].h`) distribute height among rows with diagram blocks
- Blocks grow up to the holding height that keeps their boxes filled
    + `table` up to the row height cap (0.5 inch for text-only single-line rows, the height holding 1.3x line spacing for multi-line rows (0.8 inch or less), 0.8 inch for tables with Harvey balls)
    + `stack`, `labeled`, `grid`, `vsteps`, vertical `flow` and `zones` up to the gap between boxes
    + `tree` up to the connector length and the gap between second-level boxes
    + `governance` up to the chain box height (0.62 inch) and the arrow segment (0.6 inch)
    + `funnel` up to a stage band height of 0.9 inch
    + `matrix` until the quadrant plane is close to square (plane width at most 1.25x the height, plane and legend group centered in the cell)
    + `pyramid` and `cycle` up to the shape size
    + Other text box blocks up to 1.2x the natural height
- A row grows only to the height all its cells can fill (the minimum of the cells' holding heights)
- A cell whose holding height is below the row height is centered vertically in the height left under the cell title
- A cell holding only one table is extended to match the top and bottom of neighboring cells when it is at most 0.3 inch shorter than the row height
- The cell note (`note`) sits right under the cell content
- When a row has a cell with a note, neighboring cells also raise their content bottom by the note height so the cell bottoms in the row line up
- Spare height goes to diagram rows, block holding heights, gaps between rows (capped at 0.55 inch) and vertical centering margins, in that order
- When a diagram block and a text box block are stacked in one cell, the text box block gets its content height first and the diagram block gets the rest
- When a cell is shorter than the height its block content needs, the build warns of overflow risk (fix by cutting items or adjusting the grid)
- When large spare height makes the group look small, add elements that carry more information, such as a weight column or a Harvey ball column
- If the Point band only repeats the headline or summarizes the body, delete the band and give the body more height
- Put one-line formulas or caveats in `footnotes`
- `check_layout.py` warns when the group is under 70% of the body height
- Fix body vertical fill warnings by adding items or changing the layout type
- Source (`source`) and footnotes (`footnotes`) use the common slide fields

## Blocks

| kind | Use | Fields |
|---|---|---|
| `table` | Row and column comparison | `head[]`, `rows[][]`. Cell values are strings, item arrays, or ● ◐ ○ (Harvey balls). Column widths and alignment are computed automatically (`references/templates.md` table typesetting) |
| `bullets` | Item list | `head` (optional), `items[]` |
| `text` | One-sentence message | `text`, `style` (navy, tint, box, plain. Default box) |
| `stack` | Vertical stack of titled boxes | `items[{head, items or text, headFill, fill}]`. The value of `headFill` and `fill` is tint |
| `summary` | Synthesis box (a shape holding a conclusion strip and response items inside one border) | `lead` (one-sentence conclusion), `items[{head, items or text}]` |
| `labeled` | Rows with a label on the left and content on the right | `rows[{label, items or text}]`, `labelW` (ratio of the cell width) |
| `grid` | Label column and cell grid | `head[]` (optional), `rows[{label, cells[], sz}]`, `labelW`, `style` (hierarchy typesets a hierarchy chart). Cell values are strings or `{text or items, fill, span, bold, color, shape, numbered}`. The `fill` value is navy or tint. The `shape` value db is a storage cylinder. The `color` value is navy. If `numbered` is true, the leading number of each item (1-1. etc.) replaces the bullet. `sz` is the font size (pt) of rows given a hierarchy. If `flow` is true, right arrows between cell columns (showing the gap from current state to target) |
| `vsteps` | Vertical steps with per-step descriptions | `steps[{title, items or text}]`, `arrows` (default true), `label` (prefix before the step number. "" omits the number) |
| `chevrons` | Horizontal chevrons with per-step descriptions | `steps[{title, items or text}]` |
| `flowchart` | Flowchart | `lanes[]` (actors, optional), `nodes[{id, type, text, lane, col, fill}]`, `edges[{from, to, label, route}]`. The `type` value is start, end, process or decision. The `fill` value is tint (work done by a system). The `route` value is hv (horizontal first, default) or vh (vertical first) |
| `zones` | Zone diagram (system architecture) | `zones[{title, items[]}]`, `band{label, items[]}` (optional). Component values are strings or `{text, fill, shape}`. The `shape` value db is a storage cylinder, and the `fill` value tint marks a component of a different nature |
| `valuechain` | Value chain (support function strip, stage chevrons, per-stage rows, common foundation strip) | `stageLabel`, `stages[]`, `support{label, bands[{title, items or text}]}` (optional), `rows[{label, cells[]}]`, `base{label, text}` (optional), `labelW`. Cell values are strings or `{text or items, mark}`. Cells with `mark` true get a tint fill and bold text |
| `goalsystem` | Program goal system (vision, purpose and goal strips with performance goals, strategic areas and strategic task columns) | `vision`, `purpose`, `goal`, `performance[{title, quant, qual} or {title, items}]`, `strategies[{title, text}]` (text optional), `tasks[[{title, text}]]`, `labels` (changes the row labels and the quant and qual prefixes, optional). The performance goal, strategic area and strategic task group with the same index forms one column |
| `house` | Vision house (mission strip, vision roof, strategic goal pillar heads, strategic task pillar bodies, core value base) | `mission`, `vision`, `pillars[{title, items}]`, `base[]` (core values, optional), `numbered` (default true), `labels` (row label changes, optional) |
| `porter` | Classic value chain (support activity strips, primary activity columns, owner department row, arrowhead on the right) | `support[{title, text or items}]`, `primary[{title, items, owner, mark}]`, `supportLabel`, `primaryLabel`, `ownerLabel`, `tip` (text inside the arrowhead). Activities with `mark` true get a shaded owner cell |
| `logicmodel` | Program logic model (fixed layout) | `issue[]`, `goal[]`, `beneficiary[]`, `input[]`, `activity[]`, `output[]`, `outcome[]`, `assumption[]`, `labels` (changes item titles with the same keys, optional) |
| `canvas` | Business model canvas with 9 blocks (fixed layout) | `partners`, `activities`, `resources`, `value`, `relationships`, `channels`, `segments`, `cost`, `revenue` (each a text array), `numbered` (filling order numbers), `labels` (changes block titles with the same keys, optional) |
| `market` | Market size TAM, SAM, SOM (three nested circles and description rows) | `levels[{label, name, value, items[]}]` (from the outer circle to the inner circle) |
| `flow` | Box flow joined by arrows | `nodes[{title, items or text, fill}]`, `dir` (h or v). The `fill` value is navy |
| `matrix` | 2×2 matrix with placed items | `x{label, low, high}`, `y{label}` (the y axis is set as vertical text, so put the direction in the label. Example: "기대 효과 (위로 높음)"), `quadrants[top-left, top-right, bottom-left, bottom-right]`, `items[{label, x, y}]`, `focus` (index 0-3 of the emphasized quadrant), `legend`, `numbered` |
| `pyramid` | Tier pyramid | `levels[]` (from the top tier), `side[]` (per-tier descriptions, optional) |
| `cycle` | Cyclic stages | `stages[{title, text}]`, `center` |
| `tree` | Two-level tree | `root`, `children[{text, children[]}]`, `top` (a higher body above the root, optional), `sides[{side, text, dash}]` (bodies left and right of the root, optional). The `side` value is left or right. If `dash` is true, the line is dashed |
| `timeline` | Time axis with per-point event boxes (progress to date, history) | `events[{when, title, items or text, mark}]`. Events with `mark` true (the current point) get a filled marker and a tinted box |
| `funnel` | Funnel (stage-by-stage selection from candidates to the final set) | `stages[{label, value, cells[] or items}]` (from the top stage), `head[]` (description column titles, optional), `funnelHead` (funnel column title, optional). The band holds the stage name and target count, and the cells on the right hold per-stage descriptions. With `head`, `cells` are typeset in column order |
| `governance` | Governance chart (central management chain with review and partner bodies on both sides) | `spine[]` (bodies in the order R&D funds flow), `sides[{at, side, text, dash}]`. `at` is the index (from 0) of the chain body to connect, the `side` value is left or right, and `dash` true gives a dashed line (partnership) |
| `numbers` | Key figure tiles | `items[{value, label, note}]` |
| `chart` | Native chart | `chart{type, barDir, categories, series, grouping, highlight, numFmt}`. `numFmt` is the number format of data labels and the value axis (e.g. "0.0" shows one decimal place. If unset, bar and line charts round to integers) |
| `image` | Image or placeholder box | `src` (path or data URI), `caption` (description under the image), `label` (placeholder box text) |

- Set deck-wide values of block labels (the label fields of valuechain and porter, and labels of goalsystem, house, logicmodel and canvas) under the block name keys of `meta.labels` (label slots section of `references/templates.md`)
- Line breaks in block body items (`items`, and `text` of cells, rows and steps) are typeset as item breaks (a bullet per item)
- Line breaks in labels, titles, conclusion strips (`lead`) and `text` block text are typeset as new lines
- `x` and `y` of a `matrix` item set the position in the quadrant as a 0-1 ratio (0 is low, 1 is high)
- With `items`, a `matrix` typesets number markers and a legend on the right
- If `legend` is false and `numbered` is true on a `matrix`, only number markers are typeset (list the items by number in a neighboring table)
- `span` in a `grid` is read as the correspondence with cells in the row below
- The horizontal gap between cells of a plain `grid` is 0.14 inch (the same as the gap between the row label and the cells)
- If a `grid` has `style` hierarchy, labels show as gray text (vision system, goal system, target model)
- The gap between cells in a hierarchy grid is 0.2 inch (tiers are separated by white space)
- `zones` puts one component name in one component box
- `zones` puts dashed divider lines between zones
- The boxes under `chevrons` are placed automatically with the left edge at the chevron tail corner and the right edge at the chevron shoulder (the point where the tip starts to narrow)
- `flowchart` symbols are ovals for start and end, rectangles for process, diamonds for decision
- In `flowchart`, lane is the row number and col is the column number (from 0)
- If `flowchart` omits lanes, unlabeled rows go up to the largest lane
- Give each `flowchart` symbol its own (lane, col) cell (symbols in the same cell overlap, which is a build warning. An omitted col means column 0)
- A connection to the symbol directly left in the same row is a straight line, and the branch label sits in the gap between the two symbols
- A return connection (to a symbol on the left in the same row) routes under the symbols
- When two connectors run along the same segment, change the `route` of one of them
- Write the value chain of agency functions with `porter`, and the supply-stage value chain of an industry with `valuechain`
- Put a `summary` cell right of the value chain diagnosis cell to list the improvement directions or securing tasks drawn from the diagnosis (value_chain, industry_chain)
- In `porter`, the support activity strips, primary activity columns and owner department row end on the right at the base of the arrowhead
- In `porter`, list 4-5 primary activity columns with 3-4 main tasks per column
- In `porter`, the support activity strips are fixed as thin one-line strips and the primary activity columns take the spare height (the primary activities are the main area)
- In `porter`, write support activity descriptions at 80-95% of the strip width
- In `porter`, the arrowhead keeps a 0.1 inch gap from the activity group, and with a neighboring cell on the right, a 0.2 inch gap between the tip and that cell
- In `valuechain`, the support function strip sits above the primary function chevrons across the full stage width
- In `valuechain`, the common foundation strip sits under the per-stage rows across the full stage width (write content that splits by stage as rows)
- `valuechain` row cells are placed automatically with a width from the chevron tail corner to the shoulder
- In `valuechain`, the support function strip and the common foundation strip align their left and right ends with those of the per-stage row cells
- `logicmodel` item names, numbers and layout follow the logic model structure of the Korean Detailed Guidelines for Preliminary Feasibility Studies of National R&D Programs (국가연구개발사업 예비타당성조사 수행 세부지침, 2024) exactly
- In `logicmodel`, issue and assumption with 2 or more items place the items side by side inside a full-width box, split by vertical divider lines
- In `logicmodel`, the goal and beneficiary boxes are typeset at the same width as in the original guideline
- In `logicmodel`, goal and beneficiary are wide boxes, so each item carries a baseline, target date and target size
- `canvas` follows the original business model canvas layout (top 5 columns: key partners, key activities and key resources, value propositions, customer relationships and channels, customer segments. Bottom 2 cells: cost structure, revenue streams). Block names and positions stay as in the original
- The `numbered` numbers of `canvas` are the canvas filling order (customer segments 1, value propositions 2, channels 3, customer relationships 4, revenue streams 5, key resources 6, key activities 7, key partners 8, cost structure 9)
- Write the `governance` chain top to bottom in the order R&D funds flow (lead ministry, specialized agency, program office, R&D institution)
- The first body in the `governance` chain is typeset with a theme color fill
- The side bodies of `governance` sit at the same height as the chain body they connect to
- In `governance`, solid lines show review and dashed lines show partnership (put the line meanings in the cell note `note`)
- If a side body box of `governance` is narrower than the longest word of the body name, the chain box width shrinks to make room for the side boxes (a build warning appears if it is still short)
- `top` and `sides` of `tree` are used to place a higher ministry, the operating lead and working support bodies around the root, as in a committee operating structure (put the line meanings in the cell note `note`)
- `goalsystem` and `house` are typeset with a row label column on the left (gray bold text) and hierarchy rows
- `goalsystem` uses the same format as the hierarchy grid (`grid` style hierarchy): vision in a theme color cell, program goal in a tint cell, other cells white, white space between tiers
- The vision of `house` is shown as a theme color trapezoid roof
- The performance goals of `goalsystem` split quantitative and qualitative goals into `quant` and `qual`
- Write each `house` pillar as a strategic goal title with 2-3 strategic tasks, with 3-4 pillars
- `house` automatically numbers strategic goals 1. and strategic tasks 1-1. (the numbers replace bullets)
- The core values (`base`) of `house` are optional
    + With values, the base is split into one cell per value
    + Without values, a floor strip closes the pillars at the bottom
- Show storage (databases, document stores) as cylinders by setting the `shape` value db on `grid` cells and `zones` components
- `timeline` points run left to right in time order. 3-6 events
- `timeline` serves both progress to date (year and month) and execution schedules (weeks, submission dates)
- `funnel` has 3-5 stages. Upper stages are typeset in lighter colors and lower stages in darker colors
- The target count on a light `funnel` band is typeset in the theme color (body text color when the contrast with the band color is below 3:1)
- The `funnel` description columns hold the same items for every stage, such as selection criteria, method and participants (the first stage gets counts per collection channel)
- Use `funnel` for procedures where the target count shrinks, such as candidate task selection and representative outcome selection
- For a layout with a synthesis column right of per-area analysis cells, join the two cells with `flow` and write the synthesis column as one `summary` (pest_scan, benchmark_cases, findings_synthesis)
- `summary` puts a one-sentence conclusion in the theme color strip at the top and 2-4 response items below, separated by thin divider lines
- Name each `summary` item after its response content (e.g. 재원 분담 조정, 전문 인력 확보)
- Write 2-3 content lines per `summary` item
- Write `summary` item content at 90-100% of one line of the box width (a build warning appears when it runs past one line)
- `summary` fills the cell height to match the neighboring analysis cell
- When a wide `summary` cell makes the item text look short, reduce the synthesis column ratio in `cols` (e.g. analysis cell 2.8, synthesis cell 1)
- A cell that synthesizes the result of a staged procedure (chevrons, flow) goes right of the procedure as a `summary` (workforce_estimation)
- With as many `bullets` cells in the row under `numbers` as there are figures, the per-figure implications match column by column (key_numbers)
- Placing a `matrix` next to a `table` with a number column matches the quadrant placement and the per-item actions by number (priority_matrix, risk_plan)
- `market` places abbreviations and sizes inside three bottom-aligned circles
- The description rows on the right of `market` hold the market name, definition and estimation basis
- The sizes in `market` carry the reference year and source
- `market` description rows split the circle height into equal shares, and each abbreviation inside a circle sits at the middle height of its row, so one horizontal connector links them
- The `market` description cell width fits the longest text, and the circle, connector and description cell group is centered in the cell (text wider than the cell uses the full cell width)
- When a `market` or `matrix` without a cell title is centered narrower than the cell, the left and right ends of the conclusion band and the Point band align with those of the diagram
- Fill the `market` description rows with three items per market: definition, formula, and growth trend or target scope
- Write a cell with no correspondence to the row below as one full-width cell (e.g. the mission, vision and goal of a vision system)
- A build warning appears when a `chart` cell is narrower than 2.4 inch or shorter than 1.2 inch (label overlap)
- Chart type selection and label rules for `chart` follow the chart item of the SKILL.md design system
- Two or more items given as an `items` array are typeset left-aligned with bullets
- A single item (`text`, or `items` with one item) is typeset centered without a bullet, even when it wraps onto several lines
- A box holding two or more items gets a build warning when the average share of item lines in the inner box width is below 65% or the longest line's share is below 80% (box text fill)
- `summary` is a conclusion cell, so its minimums are 90% average and 95% for the longest line (fit the column width to the longest item and write the other items at a similar length)
- Write bullet box item text at 80-95% of one line of the box width
    + Short text adds subject, criterion and figures
    + Long text splits into two items
- If a box text fill warning comes from the cell width, reduce the `cols` ratio or add cells

## Recipe list

- Groups are classified by the function of the slide content
- The group order is current state diagnosis, analysis results, strategy, program planning, organization diagnosis, IT planning, performance management, project management, bidder introduction
- The order within a group follows the order in which the engagement produces outputs
- The layout column lists block kinds in cell order
- With two or more rows, rows are marked (top), (middle), (bottom)
- With two or more blocks in one cell, they are joined with `+` from top to bottom
- Use the topic-specific headline forms in `references/headline-patterns.md`

### Current state diagnosis

| Recipe | Use | Layout | Options | Required content |
|---|---|---|---|---|
| `issue_tree` | Break a key question into issues and sub-issues, matching a hypothesis and analysis method to each issue | tree, table | - | One key question, issues split by a single criterion, hypothesis per issue, verification method, responsible module |
| `interview_plan` | Show the purpose, targets, format and procedure of stakeholder interviews or focus group interviews on one slide | labeled, stack, flow | Cell title numbers | Interview purpose, targets and headcount, format, question areas, path for using the results |
| `survey_design` | Show the sample and questionnaire structure of a fact-finding, perception or demand survey | table, table | - | Population, sample size and sampling method, survey method, survey period, questionnaire areas and sample questions |
| `verify_steps` | Show step-by-step checks and criteria for the reliability of collected material or track records | vsteps, table | - | Verification steps and what each checks, check documents by type, handling of mismatches |
| `pest_scan` | Synthesize external trends, opportunities and threats in the political, economic, social and technology areas into one response agenda | grid, summary | Arrows between cells | Main trends per area (source and reference date), implication per trend (opportunity or threat), one-sentence synthesis agenda, response tasks per agenda |
| `history_timeline` | Arrange the main milestones of a policy, program or agency in time order to show current tasks | timeline | - | Dates (year and month), event names, content per event, current point marker, tasks drawn from the history |
| `benchmark_cases` | Contrast similar domestic and overseas cases on the same comparison items and synthesize success factors into implications for the engagement | grid, summary | Arrows between cells | Case selection criteria, overview per case (actor, period), approach, outcomes (figures and sources), success factors, one-sentence application direction and application tasks per direction |
| `value_chain` | Lay out agency functions as a classic value chain of support and primary activities to identify overlaps and gaps and show improvement directions | porter, summary | - | Support activities, primary activities with main tasks per activity, owner department per activity, overlap and gap markers, improvement directions |
| `industry_chain` | Diagnose the key items, domestic supply level and shortfall factors of each supply stage of an industry and derive securing tasks per stage | valuechain, summary | - | Supply stages, key items per stage, domestic supply level, shortfall factors, weak stage markers, securing tasks per stage and common foundation tasks |
| `gap_analysis` | Derive improvement directions from the difference between the current state and a benchmark | grid | Point | Current diagnosis results, benchmark (laws, best practices, target level), gap items, improvement directions |

### Analysis results

| Recipe | Use | Layout | Options | Required content |
|---|---|---|---|---|
| `key_numbers` | Highlight 2-4 key figures that ground a judgment, with an implication per figure | (top) numbers (bottom) bullets, bullets, bullets | - | 2-4 figures, source and reference date per figure, implication per figure, overall direction |
| `analysis_four` | Present several indicators together by placing 4 visuals in quadrants split by divider lines | (top) chart, chart (bottom) chart, chart | Cell dividers | 4 indicators, visual and caption per indicator, source and reference date |
| `market_sizing` | Narrow the total, serviceable and obtainable market with nested circles to show the target market size | market | Point | Definitions of TAM (total market), SAM (serviceable market) and SOM (obtainable market), size and reference year, estimation basis, estimation approach (top-down, bottom-up) |
| `interview_findings` | Organize stakeholder opinions gathered through interviews, surveys and advisory sessions by topic to derive implications | labeled, table | - | Survey overview (targets, size, method, period), main opinions and respondent groups per topic, implications |
| `findings_synthesis` | Gather the key findings and implications of per-area analyses on one slide and link them to strategic issues | grid, summary | Arrows between cells | Analysis areas, key findings per area, implications, one-sentence strategic issue and tasks per issue |

### Strategy

| Recipe | Use | Layout | Options | Required content |
|---|---|---|---|---|
| `strategy_derivation` | Pick items related to the agency mission from higher-level plans and link them to strategic goals | stack, stack, stack | Arrows between cells, cell title numbers | List of higher-level plans, items related to the agency mission, derived strategic goals, linking rationale |
| `strategy_review` | Arrange the current mission, vision, strategic goals and strategic tasks in a vision house, assess them by diagnostic criteria and show redesign directions | house, table | - | Current vision house (mission, vision, strategic goals, strategic tasks), diagnostic criteria (fit, linkage, validity, feasibility) and diagnostic questions, judgment per criterion, improvement directions |
| `env_to_strategy` | Synthesize internal and external analysis results into a SWOT and link them to strategic directions | stack, grid, stack | Arrows between cells, cell title numbers | Internal analysis implications (strengths and weaknesses), external analysis implications (opportunities and threats), SWOT combination strategies, strategic directions |
| `vision_system` | Link mission, vision, goals, strategies and strategic tasks in one system | grid | - | One-sentence mission, one-sentence vision, one row of goals, 3-4 strategies, tasks per strategy, inherited numbering (task cells use numbered) |
| `alignment_pyramid` | Show the tier structure that aligns top-level goals with organizational and individual goals | pyramid, table | Point | Tiers (company, department, individual), goals and indicators per tier, evaluation cycle, use of evaluation results, alignment method |
| `task_funnel` | Show how a list of candidate tasks narrows by per-stage criteria to the final tasks, with results per stage | funnel | Point | Target count per stage, counts per collection channel, selection criteria per stage, method and participants, follow-up handling of final tasks and management of dropped tasks |
| `priority_matrix` | Move evaluation criterion scores onto a 2×2 matrix to set the start order of tasks or programs | table+table, matrix | - | Evaluation criteria and weights, score per task, quadrant meanings, judgment results |
| `option_evaluation` | Compare several alternatives on the same evaluation criteria and weights to show the selected option and the reason | labeled, table | Point | Overview per alternative, evaluation criteria and weights, evaluation per alternative (● ◐ ○), weighted total score, selected option and reason |
| `task_definition` | Present one action task's goal, background, content, governance, period, budget, performance indicators and expected effects in a definition sheet format | labeled, table+table | - | Task number and name (marker), task goal, background, main content, governance (lead, support), period (0000-0000), yearly budget and funding source, indicator baselines and yearly targets, expected effects (pointLabel 기대효과) |

### Program planning

| Recipe | Use | Layout | Options | Required content |
|---|---|---|---|---|
| `business_goal_system` | Link a program's goal system on one slide, from vision, program purpose and program goal to performance goals, strategic areas, strategic tasks and detailed tasks | goalsystem | - | Vision, program purpose, program goal, performance goals with quantitative and qualitative indicators per goal, strategic areas, strategic tasks and detailed tasks (one column per strategy) |
| `goal_hierarchy` | Make the program purpose concrete as measurement criteria centered on performance goals and outcome indicators, using the goal system (purpose, goals, performance indicators) of the preliminary feasibility study guidelines | (top) grid (bottom) table | - | One purpose (strategic goal), goals to achieve the purpose (performance goals), performance indicators per goal (mainly outcome indicators, supplemented by output indicators), target values and dates, measurement method |
| `logic_model` | Show the program logic from issue to assumption with the logic model structure of the preliminary feasibility study guidelines | logicmodel | - | Issue, goal, beneficiary, input, activity, output, outcome and impact, assumption (fixed item layout) |
| `business_model` | Show customers, value proposition, delivery channels, revenue and cost structure in the original 9-block layout | canvas | - | Customer segments, value propositions, channels, customer relationships, revenue streams, key resources, key activities, key partners, cost structure (fixed block names and positions) |
| `project_breakdown` | Break a program into sub-programs and detailed tasks and show performance indicators, periods and size estimation basis per detailed task | tree, table | - | Hierarchy of program, sub-programs (R&D, R&D infrastructure) and detailed tasks, indicators and targets per detailed task, period and sequence, size estimation basis (number of tasks, unit cost) |
| `governance_tree` | Place the R&D fund and management chain (vertical) and the review and partner bodies (horizontal) in one diagram to separate the roles of each body | governance, table | - | Hierarchy of the management chain bodies, review bodies, partner bodies, role per body |
| `funding_plan` | Show the yearly input plan per funding source, the financing plan per funding body and the confirmation documents | table, table | - | Funding sources (national, local, private), amount per year, total check, financing plan and confirmation documents per source, conversion basis for in-kind contributions |
| `feasibility_review` | Show the scientific and technological, policy and economic feasibility analysis items of the preliminary feasibility study and the planning response material per item | stack, stack, stack | Cell title numbers, conclusion band | Analysis items per feasibility type (second-level items of the guidelines), planning response material per item, overall evaluation method (analytic hierarchy process) |
| `econ_analysis` | Show the procedure and decision indicators for cost estimation, benefit estimation, present value conversion and sensitivity analysis | vsteps, table | Point | Cost categories (R&D, research facilities and equipment, research management) and costs after the program period, benefit formula and variable basis, reference date and analysis period, social discount rate, decision indicators (B/C as the base, NPV, IRR), conditions for substituting cost-effectiveness analysis, sensitivity analysis |
| `impact_io` | Apply input-output coefficients to the final demand from program spending and output trading to compute production, value added and employment inducement effects (kept apart from economic analysis benefits) | labeled, table | Point | Final demand types (program spending, commercialization sales) and industry allocation basis, coefficient source and reference year, formula and result per effect, principle of excluding these from benefits |

### Organization diagnosis

| Recipe | Use | Layout | Options | Required content |
|---|---|---|---|---|
| `job_analysis` | Show the job analysis procedure with staff participation and step-by-step verification, and the areas where results are used | (top) chevrons (bottom) grid | - | Analysis steps (preparation, provisional job classification, job survey, job description writing, confirmation and maintenance), activities per step, staff participation and verification method, areas of use |
| `workforce_estimation` | Show the appropriate staffing estimation procedure that runs macro, micro and comparative estimates in turn and synthesizes the results, with output forms | (top) chevrons, summary (bottom) table, table | - | Estimation procedure (macro, micro, comparative) and source data, synthesis of results (range check, items reflected), output forms (working hours analysis, staff size per year) |
| `raci_matrix` | Show the responsible, accountable, consulted and informed bodies per task in a table | table, labeled | - | Task list, body list, role code per body (one A per task), code definitions |
| `org_redesign` | Link organization diagnosis results to redesign directions, the redesign plan and the confirmation procedure | labeled, stack, grid+labeled | Arrows between cells, cell title numbers | Results per diagnostic method (environment and strategy, functions and jobs, workload, staff opinions), redesign directions, redesign plan (current vs. proposed, staff size), follow-up, confirmation procedure |
| `financial_feasibility` | Judge the financial feasibility of a business with financial projections, return on investment analysis and break-even point (BEP) analysis per scenario | vsteps, chart+table | Point | Projection assumptions (sales, costs, investment), return on investment and payback period, BEP timing per scenario, decision criteria (target return, payback period, BEP timing) |

### IT planning

| Recipe | Use | Layout | Options | Required content |
|---|---|---|---|---|
| `process_redesign` | Contrast the current and improved procedures as flowcharts to show improvement points | (top) flowchart (bottom) flowchart | - | Flowchart symbols (ovals for start and end, rectangles for process, diamonds for decision), actors, current and improved steps, system-performed task markers, improvement effects |
| `target_model` | Show the ISP target model design areas (business process, information system architecture, data architecture, technology and security architecture) as tiers | grid, table | - | IT goals, To-Be business process, To-Be information system architecture (application services), To-Be data architecture (storage as cylinders), To-Be technology and security architecture, design documents per area |
| `requirements` | Show the procedure that confirms business and IT requirements as an information system requirements specification, and the requirement categories | (top) flow (bottom) table | - | Requirements analysis procedure and outputs, requirement categories (functional, non-functional, technical, project support), definition per category, ID code rules |
| `system_architecture` | Place the components of the access, processing and resource zones and the elements common to all zones | zones | Point | Zone split, components per zone (one component per box, storage as cylinders), elements common to all zones (security, etc.), communication principles between zones |
| `data_management` | Show the collection method, preprocessing method and management criteria per data type | table, stack | - | Data types, collection method, preprocessing, management criteria (retention, access rights, quality) |
| `poc_plan` | Show the period and goal per pilot verification stage and the evaluation criteria against a comparison method | (top) timeline (bottom) table, labeled | - | Period and goal per stage, evaluation items and criteria, comparison target, judgment method |
| `operation_governance` | Show the operating organization, operating cycle and user capability plan together | stack, flow, stack | Cell title numbers | Dedicated organization and roles, activities per operating cycle, user training and support |

### Performance management

| Recipe | Use | Layout | Options | Required content |
|---|---|---|---|---|
| `kpi_development` | Show the procedure for deriving indicator candidates, verification, weighting and definition sheet writing, with the definition sheet items | (top) chevrons (bottom) table | - | Candidate derivation channels, verification criteria (validity, measurability), weighting method, definition sheet items and writing criteria |
| `bsc_kpi` | Show strategic goals, performance indicators, weights, target values, measurement methods and owner departments per balanced scorecard perspective | table | - | Perspectives, strategic goals per perspective, indicators per strategic goal, weights (total 100), target values, measurement method, owner department |
| `performance_framework` | Design the analysis areas of national R&D program performance analysis (adequacy of input and process, efficiency of output, effectiveness of outcomes) with analysis items, indicators and measurement plans per outcome type | (top) chevrons (bottom) table | - | 3 analysis areas and analysis items per area, outcome types (scientific, technological, economic, social, infrastructure), analysis items per type, indicators, confirmation documents, comparison benchmarks |
| `representative_outcome` | Show the procedure for selecting representative outcomes from the overall performance analysis and writing them up as the introduction sheet items of the performance evaluation guidelines | funnel, table | - | Selection criteria and number selected (3-5), target count and selection method per stage, introduction sheet items (per that year's performance evaluation guidelines) and length |
| `feedback_plan` | Build a feedback plan by linking overall analysis results to shortfalls, improvement measures and action plans per analysis area | (top) grid (bottom) table | - | Overall analysis results per area (strengths and shortfalls), shortfalls per area, improvement measures, action plan and timing, owner department, confirmation procedure |
| `pdca_cycle` | Show the plan, do, check, act cycle with timing, lead and outputs per stage | cycle, table | - | 3-6 cycle stages, activities per stage, timing and lead per stage, outputs per stage, cycle period |

### Project management

| Recipe | Use | Layout | Options | Required content |
|---|---|---|---|---|
| `collaboration_structure` | Show a planning committee governance in which the ministry, program office and planning contractor split roles to run a steering committee, divisions and division committees | tree, table | Point | Role split among the lead ministry, program office and planning contractor, steering committee and division tiers, field committees per division, operating method per body, member composition criteria (expertise, coverage, balance) |
| `advisory_plan` | Show the timing, agenda and format of each advisory session and the draft advisory committee roster | grid, table | - | Timing and agenda per session, format (in person, written), member roster (name, affiliation, title, field), roster confirmation procedure |
| `progress_control` | Show the trend of actual against plan and the response criteria per deviation band | chart, table+labeled | - | Cumulative progress of plan and actual, deviation bands, response per band, reporting path |
| `quality_plan` | Show the flow of output quality checks and the quality criteria per output | (top) flowchart (bottom) table | - | Check flow (check, judge, fix, record), outputs checked, quality criteria, check cycle, checker |
| `report_plan` | Show the reporting cycle basis and the content, cycle, outputs and attendees per report type | (top) numbers (bottom) table | - | Reporting cycle basis, regular and milestone reports, cycle, outputs, attendees, reporting principles |
| `deliverable_plan` | Show submitted outputs, submission format and acceptance criteria per stage in a stage grid, with submission and handover principles | grid, labeled | - | Outputs per stage, submission format and copies, acceptance criteria per stage, recipient, file naming rules, resubmission deadline, final handover method |
| `security_plan` | Show physical, technical and administrative security measures and activities at each point of execution | (top) bullets, bullets, bullets (bottom) table | Cell title numbers | Security areas, measures per area, activities at kickoff, execution and closing, check method, owner |
| `privacy_plan` | Show protection principles and measures per personal data processing stage in a table, with the protection responsibility structure | table, stack | - | Processing stages (collection, use, retention, destruction), protection principle per stage, protection measures, check records, privacy officer, handler designation, training |
| `emergency_plan` | Show the time-bound reporting sequence in an emergency and the initial actions per situation type | (top) chevrons (bottom) table | - | Time-bound reporting sequence and actions, situation types, initial actions per type, recovery time objective, owner, post-incident review |
| `risk_plan` | Show the risk management procedure and, per risk factor, likelihood, impact, preventive response and action on occurrence as a risk register | flow, table | - | Risk management procedure (identify, assess, respond, review) and cycle, risk factors, likelihood and impact (● ◐ ○), preventive response, action on occurrence |
| `budget_plan` | Show the program budget and estimation basis per cost item, with the amount and share per funding source | table | - | Cost items, estimation basis (unit cost, quantity, period), amount per funding source (government contribution, private cash, in kind), total and share check |
| `comment_response` | Contrast each comment from report meetings, advisory sessions and reviews with how and where it was reflected | table | Point | Comment source and date, comment summary, what was reflected, where (chapter, section), reason and alternative for comments not reflected |
| `output_utilization` | Match each engagement output with its use plan and expected effects | grid | Point | Official output name, user and use plan, expected effects |
| `aftercare` | Show the aftercare period, response standards and support programs | (top) numbers (bottom) table | - | Support period, response time, support scope, content per program |
| `additional_offer` | Show support offered beyond the engagement scope, the delivery method and the expected effects | table | - | Offer items, content per item, timing and method of delivery, expected effects, note on consultation with the contracting agency |

### Bidder introduction

| Recipe | Use | Layout | Options | Required content |
|---|---|---|---|---|
| `company_profile` | Show the bidder's basic information and main history on one slide | labeled, table | - | CEO, founding year, headcount, address, business areas, certifications, history by year (user-provided material) |
| `finance_status` | Show financial indicators for the last 3 years and the credit rating | table, image | - | Total assets, total equity, sales and units for 3 years, credit rating certificate image (user-provided material) |
| `record_cards` | Show several track records in similar fields as cards of contracting agency, project name and period | (top) numbers (bottom) grid | - | Number of records and cumulative contract value, contracting agency, project name, period and contract value per record (user-provided material) |
| `case_card` | Show the overview, work done and screens of one similar engagement | labeled, image | - | Engagement name, contracting agency, period, main work, outcomes (user-provided material), screens or photos |
| `infra_tiles` | Show databases, analysis tools and in-house material to be used in the engagement as tiles | (top) bullets, bullets, bullets (bottom) bullets, bullets, bullets | - | Resource categories, holdings list (user-provided material), how each is used in the engagement |
| `pm_profile` | Show the career, expertise and key track records of the project lead | image, labeled | - | Photo (optional), name and title, education, career, fields of expertise, key track records (user-provided material) |
