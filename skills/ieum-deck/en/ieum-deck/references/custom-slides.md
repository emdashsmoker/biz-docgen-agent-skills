# Custom slides

- A custom slide reuses the shape layout extracted from an individual slide of a PPTX the user provides
- The storyboard calls it with `"template": "own:N"` (N is the slide number in the source PPTX)
- Registration requires a PPTX from the user and confirmation of the right to use it
- The distributed skill contains no custom slide data
- The whole procedure works with composite recipes and parametric templates even without registered custom slides

## Scope

- What is reused is the shape layout of individual slides

| Category | Elements |
|---|---|
| Used as in the source | Shape position and size, line and fill colors, table and chart structure, positions of text boxes and images |
| Replaced with the skill style | Font (NanumGothic), band (section number, headline, marker), colors set in `colorMap`, bullet characters of symbol fonts (Wingdings, Symbol) |
| Not extracted | Shapes and backgrounds on the slide master and layouts |

## Registration procedure

1. Check layouts
    + `python3 scripts/own_extract.py --inspect <source.pptx>`
    + The output lists the slides using each layout name and the placeholder idx values
2. Write the config file
    + Write `deck-config.json` following the config key table
    + Extracting without a config file extracts the original text as is
    + Without a config file, every slide has band mode full
3. Extract coordinates
    + `python3 scripts/own_extract.py <source.pptx> <own-deck.json> --config deck-config.json`
    + If identifying text caught by `identityCheck` remains, a list is printed after extraction
4. Generate the slot list
    + `python3 scripts/own_catalog.py <own-deck.json> <own-slots.md>`
    + The slot list records, per slide, the slot keys, the start of the original text, table sizes, image slots and chart slots
5. Check the reproduction
    + Build a storyboard holding every `own:N` once without slots
    + Convert the build to PNG with `render.sh`
    + Convert the source PPTX to PDF
    + Contrast the source and the reproduction with `python3 scripts/compare.py <source.pdf> <png_dir> <out_dir> 1:1,2:2,...`
    + Open the contrast images starting from the slides with the largest difference ratio
    + Correct mismatched slides with the config file (`dropAtoms`, `dropTexts`, `layoutModes`, `bandPlaceholders`)
6. Register
    + Put the own-deck.json path in `meta.ownDeck` of the storyboard (a path relative to the storyboard file is allowed)
    + To use the same custom slides in several storyboards, set the environment variable `IEUM_DECK_OWN`
    + `meta.ownDeck` takes priority over the environment variable

- Using `own:N` without registration stops the build
- Using `own:N` without registration is a lint FAIL
- Using a number that is not among the registered custom slides is a lint FAIL

## Config keys

| Key | Format | Use |
|---|---|---|
| `bandPlaceholders` | `{"placeholder idx": "one of secNo, secTitle, tracker, headline, marker, pageNo"}` | Maps source placeholders to skill band roles. The builder retypesets mapped placeholders as the band |
| `layoutModes` | `{"layout name": "one of full, noMarker, headerOnly, blank"}` | Band mode per layout. Layouts not listed use full |
| `identityText` | Regex | Identifying text such as the company name. Matching shapes get an identity tag |
| `identityCheck` | Regex | Criterion for checking identifying text left after extraction |
| `generalize` | `[{"pattern", "replace", "slides": [N]}]` | Rules that turn identifying text into placeholders. Without `slides`, the rule applies to every slide |
| `identityPicSlides` | `[N]` | Slides where pictures count as identifying elements such as logos |
| `zeroTableSlides` | `[N]` | Slides where numbers in tables become 0 (real financial figures, etc.) |
| `dropAtoms` | `{"N": ["shape name"]}` | Shapes excluded from playback |
| `dropTexts` | `{"N": ["full text"]}` | Text shapes excluded from playback (full text match) |
| `roles` | `{"role": [N]}` | Basis for lint to judge the function of a slide |
| `descriptions` | `{"N": "use description"}` | Slide use written into the slot list document |
| `colorMap` | `{"source RGB": "tokens.js COLOR key"}` | Source colors that change along with the theme |

- Put `__COMPANY__` as the replacement text in the company name position and the build substitutes `meta.company`
- When `generalize` turns facts such as real names, track record amounts and years into placeholders such as `[회사 확인]`, lint checks the remaining placeholders

## Roles

- lint judges the function of a slide by the template name
- For custom slides, register slide numbers per function in `roles` (the `own:N` number alone cannot tell the function)
- For example, if source slide 19 is a module overview, register `{"roles": {"module_overview": [19]}}`

| Role | Slide to register | lint judgment |
|---|---|---|
| `module_overview` | Module overview table | Counted as a module overview slide |
| `org_project` | Project organization chart | Counted as the organization chart, and staff consistency with the staffing table is checked |
| `people_table` | Staffing table | Counted as the staffing table, and staff consistency and empty middle rows are checked |
| `pm_profile` | Project lead profile | Staff consistency and the fact source are checked |
| `company_fact` | Company overview, organization, finance, track record | The fact source (`factSource`) is checked |
| `collaboration` | Expert collaboration structure | Counted as an organization-type slide |

## Slot substitution

- Check slot keys in the matching `## own:N` section of `own-slots.md`
    + (Text key) `"~start of original text"` is the text box whose original text starts with it (whitespace ignored, recommended)
    + (Index key) `t{k}` is the appearance order among shapes with text
    + (Table cell) `tb{k}.r{i}c{j}` is row i, column j of the k-th table (from 0)
    + (Image) The `img{k}` value is a path or data URI
    + (Chart) The `ch{k}` value is a chart spec (`{categories, series}`)
- A value of `""` omits the box
- When a column box in a row is omitted, the remaining columns take back the full original width
- Omitting a box in a vertical list keeps the other boxes at their size, so fill the items instead
- If more than half of a box would stay empty, choose another custom slide or composite recipe with a matching item count
- Replace the original chart data, table values and item text with engagement content
- The upper limit of slot text is the original line count
- The lower limit of slot text is a 70% fill ratio
- Replacement text exceeding the box capacity is a lint WARN
- Fix an overflowing slot by cutting characters or items

## Playback corrections

- Text kept as in the original absorbs the width difference between the source font and NanumGothic by shrinking based on measured width (minimum 9pt)
- Sibling boxes with the same original font size use the same shrink ratio
- Replaced text keeps the 11pt body minimum
- When replaced text overflows, only paragraph spacing shrinks (the font size stays)
- Slides that went through shrinking are excluded from the 11pt minimum check of check_layout
- The exclusion uses the registration info in `<file name>.build.json` left by the build
- `<file name>.build.json` sits in the same folder as the pptx
- When an icon-size image slot is left empty, a shape-built icon matching the nearby label text is placed automatically (the keywords are matched in Korean)
    + (Lock) 물리, 출입 (physical, access)
    + (Shield) 기술 보안 (technical security)
    + (Checklist) 관리 보안, 점검 (administrative security, inspection)
    + (Calendar) 일정, 보고 (schedule, reporting)
    + (Disk) 데이터 (data)
    + (Dashboard) WBS, 진도 (WBS, progress)
    + (Document shredder) 파쇄 (shredding)
    + (Gear) 시사점, 도구 (implications, tools)
    + (Person) 인원 (headcount)
- Leaving the logo slot empty omits the logo
- Leaving a large image slot empty replaces it with a placeholder box
- Leaving the illustration spot next to a table empty absorbs the empty area by extending the table or adding a topic icon
- Text inside a donut chart is placed in order by splitting the hole area vertically
- The donut ring thickness is kept with a white center circle (the proportion holds even if the renderer ignores the hole size setting)

## Using recipes alongside

- If a custom slide fits the content, use `own:N` first
- If no custom slide fits, use a composite recipe or a parametric template
- Custom slides and recipes share the band, font and color tokens
- The style holds even when one deck mixes custom slides and recipes
- The slide variety check counts each `own:N` number as a different layout type
