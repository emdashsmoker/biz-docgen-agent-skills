---
name: "ieum-deck"
description: "English edition of the Korean ieum-deck skill. Designs planning and consulting decks as one storyboard.json and typesets editable PPTX with pptxgenjs, mainly for Korean public-sector proposal and report meeting decks, also for private plans, internal reports and training material. Slides come from parametric templates and composite recipes, and user PPTX slides can be registered as custom slides. Page size, color theme and headline style are set at kickoff. Use when the user mentions 'PPT', 'slides', 'deck', 'presentation', 'proposal deck', 'report meeting deck', 'RFP response PPT', 'storyboard' or 'ieum-deck', and for PPT requests with an RFP, manuscript or sources attached, without asking the purpose. Read storyboard-schema.md and templates.md after kickoff, strategy.md at RFP analysis, methods.md and wording.md before the execution plan, headline-patterns.md, skeletons.md and recipes.md for the storyline, writing-rules.md for the storyboard, custom-slides.md for custom slides, review.md at review."
license: AGPL-3.0-or-later with an output exception. Terms in LICENSE and NOTICE.md
---

# ieum-deck (English edition)

## About this English edition

- This skill is an English translation of the Korean original ieum-deck
- The Korean edition is the original and the reference version
- This edition may work differently from the intent of the original, and output quality may differ from the original
- The writing rules, examples and lint checks are written for Korean deck text
    + Quoted Korean strings in this edition are functional values (default template labels, placeholders, lint patterns, example headlines) and stay in Korean
    + Decks are typeset with Korean default labels, and `meta.labels` switches the labels and language tags for decks in other languages (English decks section). Korean note tokens such as 출처: stay recognized
    + Decks in other languages use the same build pipeline and fonts, and the Korean-specific writing rules and checks do not cover them
    + For English decks, follow the English decks section (meta.labels, common part translation, length limits)

## Overview

- (ieum-deck) A deck skill that connects planning logic into a one-line storyline and typesets it into editable PPTX (ieum is the Korean word "이음", meaning a link)
- (Purpose) Takes over deck structure design and typesetting so the user can focus on planning logic and content review
- (Goal) Produce an editable deck draft from an RFP, manuscript or source material that passes lint, structural checks and visual review
- (Scope) Centered on public-sector proposal decks and report meeting decks, also applied to private planning decks, internal reports and training material
- The output is a native PPTX that can be edited afterwards (shapes, text boxes, tables, charts, images)
- The model records slide content in `storyboard.json`
- `scripts/build.js` always typesets the same PPTX from the same storyboard
- Design values are managed in one place, `scripts/tokens.js`

## Usage notice

- In the first run of the skill in a task, present the notice text to the user once, right before the kickoff questions
- Present the notice text as written, without summarizing or omitting anything
- Record that it was shown in `noticeShown` of `state.json` so it is not repeated when the same task resumes

### Notice text

- (Runtime environment) The skill handles large documents and multi-step work, so the model tier and token limits affect output quality
    + Using the top model of each model provider is recommended to get the intended quality
    + One deck consumes many tokens, so checking plan limits or API costs before starting is recommended
- (Nature of the output) The output is a draft that needs review before submission
    + Facts, figures and logic written by an AI model may contain errors
    + Before submission, the user reviews every slide and makes the final corrections
    + Planning judgments and final decisions are made by the user (the skill assists with writing and typesetting)
- (Limits of the included information) Information on institutions, evaluation practices and methodologies in the skill reflects the interpretation at the time of writing and may differ from current standards
    + Check current institutions and contracting agency standards in the announcements and guidelines of the responsible agencies at kickoff
    + If the included information differs from current standards, apply the current standards
- (Responsibility) The user is responsible for the consequences of submitting and using the output
    + This covers the results of bidding, evaluation and contracts and the legal liability that follows
    + The skill author does not guarantee the accuracy of the output or bidding results

## Terms

| Term | Definition |
|---|---|
| Slide | One page of a deck. Volume is counted as N slides |
| Chapter, section | Contents units. A chapter is `chapter` in the storyboard, a section is `section` |
| Band | The top area of a slide. Holds the section number, section title, chapter tracker and headline |
| Headline | The one conclusion sentence in the middle of the band |
| Marker | The subheading on the first line of the body. Typeset with a square shape |
| Point band | A strip below the body holding a label cell and one sentence ("수행 Point" by default). Shows judgment criteria, formulas, follow-up links, selection reasons, timing or principles that are not in the headline or body |
| Template | The typesetting method named by the `template` value in the storyboard |
| Parametric template | A fixed-structure template whose layout changes with the number of items (`references/templates.md`) |
| Recipe | A sample combination of grid and blocks for the composite template (`references/recipes.md`) |
| Layout type | The template name of one slide. composite is distinguished by recipe name (without a recipe, by the number of grid cells and the combination of block kinds) |
| Sample | A set of example slides used by replacing text and figures (`assets/*.json`) |
| Custom slide | A slide that reuses the shape layout extracted from an individual slide of a user PPTX as the `own:N` template. Font and band follow the skill style (`references/custom-slides.md`) |
| Argument part | Slides written anew for each engagement (background, strategy, execution plan, deliverables) |
| Common part | Bidder introduction and project management slides whose content stays the same across engagements |
| Placeholder | Text that marks an unconfirmed value in square brackets. Examples: `[회사 확인]`, `[확인 필요]`, `[N]명` |
| Section ledger | `ledger.json`, which records the mapping of RFP work items, Tasks and evaluation items per slide |
| Body slide | Any slide except the cover, contents, dividers and closing. The denominator for layout variety and score attribution ratios |
| Fill ratio | The share of the inner height of a bordered box taken by text |
| Body vertical fill | The share of the body area height taken by the content group |
| Table text fill | The share of the table width taken by the sum of one-line widths of cell text per column |
| Box text fill | In a box holding two or more items, the share of the inner box width taken by the one-line width of item lines (judged by the average and by the longest line) |
| Synthesis box | The composite `summary` block, which holds a one-sentence conclusion strip and matching items in one border. Used as the box that synthesizes analysis results to the right of analysis cells |
| Wording track | The scope of institutional terms. rnd, mgmt or general in `meta.track` |

## Scope

- The main use is public-sector proposal decks and report meeting decks
- Private planning decks, internal reports, training material and general PPT are produced with the same procedure and templates
- Templates and recipes are the common skeleton of planning slides, so they apply regardless of the kind of contracting agency
- Uses other than proposals also proceed through the kickoff questions without asking whether the use fits
- The module skeleton is set by the engagement type identification in `references/methods.md`
    + (Business planning skeleton) Planning of new businesses, services and products
    + (Strategic planning skeleton) Mid- to long-term plans, organizational strategy, roadmaps
    + (Performance analysis and evaluation skeleton) Performance diagnosis, indicator design
    + (Problem solving skeleton) Identifying causes of current problems and deriving improvements. Includes engagements centered on status surveys, trend surveys and demand surveys
    + (Informatization skeleton) System development planning, IT planning
    + (Support program operation skeleton) Calls for operating agencies in business support, commercialization and startup programs
    + (R&D plan presentation skeleton) Calls for new national R&D projects, R&D plan presentations
    + (Non-R&D call presentation skeleton) Calls for demonstration, consulting, voucher and demand-based support programs
- Technology development planning studies, pre-planning and detailed planning combine the business planning skeleton with the contents of an R&D plan
- Company R&D projects and commercialization support applications use the application variant of the business planning skeleton
- Service planning and IT planning adapt the skeleton to the subject (market and user research, feature definition, architecture, launch plan)
- RFP analysis, score attribution and the section ledger apply only to public-sector proposals
- Wording track selection applies to public-sector proposals and report meeting decks (other output types use general)

## Output types

| Type | Input | Volume | Path |
|---|---|---|---|
| Proposal deck (conversion) | Qualitative proposal (HWPX, DOCX, PDF, MD) and RFP | 30-45 slides for a 20-minute presentation, 45-60 slides for 30 minutes. Values set by the contracting agency take precedence | Extract headlines from the conclusion sentences of the manuscript. Replace the manuscript numbering (`가-2`, `[1-2]`) with Task IDs (`M1-T2`). Keep the replacement map in the section ledger |
| Proposal deck (new) | RFP | Same as conversion | Design in the order RFP analysis, proposal strategy, storyline |
| Report meeting deck | Report manuscript or topic, storyboard of the previous stage | Kickoff 40-55 slides, interim 30-40, final 50-60 | Refine the `md2storyboard.py` draft |
| Report-style PPT | Report Markdown, HWPX conversion | No upper limit. One slide per section | `md2storyboard.py --kind report` |
| Briefing deck | Report manuscript, research results, meeting material | 5-12 slides. One slide per chapter | `md2storyboard.py --kind brief [--max N]` |
| General planning PPT | Topic, manuscript, material | Requested volume | Apply the methods skeleton matching the engagement type. Skip the RFP procedure |

## Procedure

```
0 Kickoff questions (user confirmation 1)  Present the usage notice, then ask all kickoff question items at once. Apply defaults only when the user explicitly says "run right away"
1 Input conversion                          python3 scripts/parse_input.py <RFP or manuscript> <work folder/output.md> [--pdf] → md (for hwpx, --pdf also creates a PDF for checking layout)
                                            python3 scripts/extract_images.py <source> <img_dir> → candidate images and manifest.json (pdf, hwpx, pptx, docx)
2 RFP analysis and proposal strategy        00_rfp.md, 00_strategy.md (format in references/strategy.md). The conversion path extracts them back from the manuscript. Skip if not a proposal
3 Structure confirmation (user confirmation 2)  Present 00_storyline.md (one-line storyline, message per chapter, headline per slide). For public-sector proposals, also present ledger.json (section ledger) and the score attribution table → start step 4 after approval
4 Storyboard writing                        Write the argument part first. Copy the common part (common-slides.json made by company2slides.py) last and place it at its position in the contents
5 lint                                      python3 scripts/lint.py storyboard.json [--ledger ledger.json] [--layout A4] → exit code 0 is the condition for building
6 Build                                     node scripts/build.js storyboard.json out.pptx [--layout A4] → python3 scripts/finalize.py out.pptx → python3 scripts/validate.py out.pptx
7 Structural check                          python3 scripts/check_layout.py out.pptx → in-depth review (references/review.md) → fix → rebuild
8 Visual review and delivery                bash scripts/render.sh out.pptx png_dir 60 → view all PNGs → fix → bash scripts/topdf.sh out.pptx
```

- Check dependencies with `python3 scripts/setup_deps.py --check` before any other step
- Install missing dependencies with `python3 scripts/setup_deps.py`
- Accumulate the output of each step as files
- Responses contain only file paths, progress status and items that need confirmation
- Deliver files for review and delivery files with the file delivery tool of the runtime environment
    + (Reason) In runtime environments where the work folder is not visible to the user, a path alone does not let the user open the file
    + (When) Presenting and re-presenting the step 3 structure confirmation (00_strategy.md, 00_storyline.md), step 8 delivery (PPTX, PDF), and file requests from the user
    + When re-presenting, deliver only the changed files
    + With a tool that delivers only files from a designated folder, place a copy in that folder and deliver it (the reference version is the original in the work folder)
    + In runtime environments without a delivery tool, give the file path
- Deliver the delivery files (PPTX, PDF) after viewing all PNGs
- The completion report lists file paths, viewed contact sheet file names, unresolved issues and remaining user confirmation items
- Record the progress point in `state.json` for session handover

## Kickoff question items

1. (Output type) Proposal deck conversion, proposal deck new, report meeting deck (kickoff, interim, final), report-style PPT, briefing deck, general planning PPT
2. (Execution structure) The output type sets the default structure, so confirm only for documents not in the list of the execution structure selection section
3. (Subject term) Choose from 본 과업, 본 연구, 본 과제, 본 사업, 본 프로젝트, 본 보고서. If the RFP uses a term, use the RFP term
4. (Page size) 16:9 (default), A4 landscape (printed submission), 10.83×7.5, 4:3
5. (Headline style) Noun-ending style (default) or polite style. The body uses the noun-ending style regardless of the choice
6. (Color theme) Choose navy (navy blue, default), mono (black and gray) or a user-specified color. A user-specified color is taken as a color code (for example #1B4332) or a color name (for example dark green)
7. (Engagement type and wording track) Only for public-sector proposals and report meeting decks
    + Engagement types are strategic planning, business planning, performance analysis and evaluation, problem solving, informatization (check whether it is a statutory ISP), support program operation, R&D plan presentation, non-R&D call presentation, mixed
    + Wording tracks are rnd (national R&D performance evaluation, R&D program planning review, R&D business planning), mgmt (public institution management evaluation), general (institutional self-evaluation, non-R&D preliminary feasibility study, general services)
8. (Presentation time and volume) If the contracting agency sets a page limit, record it in `meta.pageLimit`
9. (Contents designation) If the RFP designates contents or an evaluation item order, use that order. For general use, propose contents that fit the topic
10. (Company profile and logo) Whether company.md in the work folder (form `assets/company.md`) has been written, and the logo file path. Without a logo, use the company name as text
11. (Company facts) Whether similar projects, organization and team expertise, staff careers, financials and certifications are provided. Items not provided are output as the `[회사 확인]` placeholder
12. (Consortium) Participation, share per organization, person-months (M/M)
13. (Contracting agency practice) Task ID notation (`Module 1 - Task 2` or `M1-T2`), headers with evaluation items, path-style headers ("주제 〉 세부")
14. (Document language and labels) Korean labels (default) or another language. For another language, set the template labels and language tags in `meta.labels` (English decks section)

## Company facts

- (Scope) Bidder overview, organization and team expertise, similar projects, staff careers, financials, certifications
- Cite company facts only from material the user provided
- Confirm whether they are provided with kickoff question 11
- Leave items not provided as the `[회사 확인]` placeholder
- A placeholder marks that material was not provided
- Copy `assets/company.md` to the work folder and write it there (the template and samples in the skill folder stay as they are)
- Generate the common part with `python3 scripts/company2slides.py <work folder>/company.md <work folder>/common-slides.json`
- Headlines of the bidder status slides are written from the table values in company.md
- To set a headline directly, write the text in the headline section of company.md
- company2slides.py prints the number of remaining placeholders
- Complete company.md until no placeholders remain
- On fact slides, write the material name or confirmation date in `factSource`
    + (Templates) features, staff_card
    + (Recipes) company_profile, finance_status, record_cards, infra_tiles, pm_profile, case_card
    + (Custom slides) Slides whose role is company_fact, people_table or pm_profile
- Missing `factSource` is a lint WARN
- Remaining placeholders are a lint WARN
- Setting `meta.final` to true right before the completion report turns remaining placeholders into lint FAIL
- The completion report lists unconfirmed items and confirmation requests

## Level of institutional framework

- (Framework-based) In national R&D engagements (wording track rnd: performance evaluation response, R&D program planning review response, R&D business planning), the institutional framework sets the procedure and deliverables
    + Apply the skeleton of `references/methods.md` and the institutional wording of `references/wording.md` as defaults
    + Add or remove only the items the RFP designates in the skeleton
- (Conditional framework) For informatization engagements, the framework applies depending on whether it is a statutory ISP
    + A prior ISP for building an information system above a certain amount is a legal obligation
    + Statutory cases use the procedure and deliverable names of the ISP·ISMP common guide as they are
    + In statutory cases, the framework sets the four-stage skeleton (environment analysis, current state analysis, target model design, integrated implementation plan), the requirement classification scheme, the cost estimation standards and the security design of the national network security framework
    + Even in statutory cases, module names and splits, Task composition, survey design and priority criteria for implementation tasks are at the discretion of the contracting agency
    + IT planning outside the statutory scope (engagements the contracting agency orders for its own needs) is structured within the scope set by the RFP
    + Identify statutory cases from the legal basis, budget and deliverable list in the RFP
    + If the identification is unclear, confirm in the kickoff questions
- (Discretionary) Management strategy, organizational diagnosis, new business discovery, facility feasibility, non-R&D support program performance analysis and problem solving engagements differ in structure by contracting agency and engagement
    + Use the methods skeletons as reference examples
    + Derive modules and Tasks from the RFP work details and the key issues in `00_strategy.md`
    + Get user approval of the derived modules and Tasks at the step 3 structure confirmation
    + Copying module names of example skeletons and using institutional terms outside the wording track (전략계획서, 자체평가, 효과성 분석 and so on) are defects (lint WARN)
- The national R&D preliminary feasibility study is an abolished framework
- Its successor frameworks are the R&D program planning review (research-type programs), and the program implementation review and design suitability review (construction-type programs)
- The non-R&D preliminary feasibility study is a current framework
- Confirm at kickoff whether each is current, to avoid mixing the names and procedures of the two frameworks

## Input conversion

- Convert every input format to Markdown with `scripts/parse_input.py`
    + (pdf) Appends pdfplumber tables to the markitdown body. Falls back to pdftotext on failure
    + (docx, pptx) Falls back to python-docx or python-pptx if markitdown fails
    + (hwpx) Tries python-hwpx export_markdown, HwpxDocument.text.markdown, then direct extraction from the body XML
    + (hwp) Converts with pyhwp hwp5txt. On failure, advise saving as hwpx and retrying
- The first two hwpx paths recover table structure
- Direct extraction from the hwpx body XML recovers only paragraph text, including table cells
- A document from which no Hangul is recovered is judged a scan or a subset-font document
- For scans and subset-font documents, tell the user that OCR is needed
- To check table and figure layout by eye, also create a PDF with `--pdf`
- If the conversion result is broken, find another conversion method and compare with the original
    + (Signs of breakage) Partly broken Hangul, lost columns in tables with merged cells, lost table structure, scrambled paragraph order
    + (Alternatives) Other text extraction tools, rendering source pages as images and reading them by eye
    + Record the conversion methods used and the compared range in the completion report
- The order for obtaining a PDF converter for hwpx is the rhwp release binary, an rhwp source build, then the LibreOffice H2Orestart extension
- Move to the next option only after actually trying to obtain the previous one and failing
- (Conversion test right after obtaining) Right after obtaining a converter at any rank, make a one-line hwpx reading `안녕하세요!` with python-hwpx in a temporary folder outside the work folder and test the conversion
    + Create it with `python3 -c "from hwpx import HwpxDocument; d = HwpxDocument.new(); d.add_paragraph('안녕하세요!'); d.save_to_path('변환시험.hwpx')"`
    + Convert it with `parse_input.py 변환시험.hwpx <temp folder>/output.md --pdf` and check from the PDF's Producer value that the converter of that rank was used (parse_input.py falls back to LibreOffice when rhwp fails)
    + Turn the PDF page into an image with pdftoppm and check that `안녕하세요!` is visible. rhwp writes a blank-page PDF when the document's fonts are missing (this file uses Hamchorom, the default font of Hangul), so a produced PDF alone is not a pass
    + If the test fails, count that rank as failed even though the converter was obtained, and move to the next rank
- (GitHub repository attach) If the execution environment has a tool that attaches a GitHub repository to the session, call it before the first GitHub access of options 1 and 2
    + Pass the owner `edwardkim` and the repository name `rhwp` as separate values
    + Apply any access route the tool's reply names to the steps below
    + Skip this step when no such tool exists or the call is refused
- (Option 1, rhwp release) Get the asset for the current platform (OS, CPU) from the releases of https://github.com/edwardkim/rhwp and place it on PATH
    + GitHub addresses split into web page paths and file download paths
    + Some runtime environments pass the file download path (`releases/download/<tag>/<file name>`) and the git protocol even when the web page paths (`releases/latest`, `releases/expanded_assets`, `api.github.com`) return 403
    + Judge option 1 as failed when downloading from the file download path fails
    + Find the tag as the highest version tag in the output of `git ls-remote --tags --refs https://github.com/edwardkim/rhwp`
    + Only when git access is blocked, read the tag from the end of the final redirect address of releases/latest
    + Get the asset list by downloading `https://github.com/edwardkim/rhwp/releases/download/<tag>/SHA256SUMS.txt` with `curl -fL` and reading the file name column
    + If SHA256SUMS.txt does not exist, check `releases/expanded_assets/<tag>` and then the GitHub API `/repos/edwardkim/rhwp/releases/tags/<tag>`
    + If the highest version tag has no release (SHA256SUMS.txt returns 404), retry with the next version tag
    + Download the chosen asset from `https://github.com/edwardkim/rhwp/releases/download/<tag>/<file name>` with `curl -fL`
    + Verify the downloaded file with `sha256sum -c`
    + If verification fails, stop obtaining it
    + Give the extracted executable the execute permission
    + Check the installation with `rhwp --version`
- (Option 2, rhwp source build) Possible in runtime environments where release assets are blocked but the git protocol passes
    + Explore the repository obtained with `git clone` directly and decide how to build it
    + Check the build procedure in the repository's build settings, workspace layout, toolchain settings, CI settings and development documents at kickoff time (rhwp changes often)
    + Build only the CLI binary target that has the PDF export function
    + The binary is for checking only, so choose a profile or feature set with a short build time
    + Place the built binary on PATH as `rhwp`
    + Check operation with `parse_input.py <hwpx> --pdf`
    + The clone can reach several GB, so check free disk space before starting (the clone folder can be deleted after building)
    + If git access is blocked or the build fails, move to option 3
    + Record the reason for moving in the final report
- After obtaining rhwp, find the PDF output command in `rhwp --help` (export-pdf as of v0.8.6)
    + If the command name differs, replace RHWP_PDF_COMMAND at the top of `scripts/parse_input.py`
    + If the argument format differs, fix the call in hwpx_to_pdf
    + On conversion failure, parse_input.py prints a warning and switches to LibreOffice
    + Check which converter was actually used from the Producer value of the PDF
- (Option 3, LibreOffice H2Orestart) Use when options 1 and 2 both fail
- If every option fails, tell the user and use Markdown only

## Reusing source images

- If source submissions (pdf, hwpx, pptx, docx) exist, extract insertion candidates with `scripts/extract_images.py`
- The extraction thresholds are 64px on a side, 2KB in size and 8,192px in area
- Bullets and background fragments are excluded from the candidates
- The thresholds are low to recover small CI and agency logos
- For logo candidates, open the logo kind entries of the manifest first and check them
- If there are many candidates, raise the thresholds with `--min-px` and `--min-kb`
- manifest.json records the size, ratio and kind (photo, logo, map, diagram) of each image
- The source page number is recorded only for images taken from a PDF (hwpx, docx and pptx hold no page breaks)
- Images taken from hwpx, docx and pptx record their path inside the ZIP (member)
- Check how an image is used where the body XML references the member file
- (Adopt) Photos of similar projects, site photos, maps, company and agency logos, architecture diagrams that are hard to reproduce with templates and recipes
- (Do not adopt) Methodology diagrams, charts, module and Task structure diagrams, images of captured tables
- Typeset non-adopted kinds again with templates and recipes
- A person makes the adoption decision
- The script only presents the candidate list
- Set adopted images as paths in `src` of image blocks in composite and free (custom slides use the `img{k}` slot)
- Relative image paths are relative to the folder of the storyboard file
- The bidder checks the copyright and usage rights of source images

## Execution structure selection

- The default structure is modules and Tasks (`meta.structure` value module)
- Apply the default structure of each output type without asking
    + (plan) The plan chapter structure of R&D plan presentations
    + (sections) The RFP chapter structure of non-R&D call presentations, and the report section structure of report-style PPTs and briefing decks
    + (module) Proposal decks, report meeting decks, planning studies, general planning PPTs
- Confirm in the kickoff questions only for documents not in the list and documents that do not seem to fit the default structure
- Signs that the module and Task structure does not fit
    + The contracting agency designates the contents
    + An institutional form designates the items
    + Execution units are split by year, division or target
    + A manuscript whose section structure is fixed is being converted
- (Example confirmation question) "This document seems to fit the plan chapter structure better than the module and Task structure. Which should we use?"
- If the user does not answer or the judgment is unclear, proceed with the default structure

### Types that use a chapter structure

- R&D plan presentations and non-R&D call presentations use the chapter structure of the plan and the RFP as it is
- Execution units in R&D plan presentations are written as `[1차년도]`, `[세부과제 1]`
- Execution units in non-R&D call presentations are written as `[수행부문 1] 부문명`
- Both types manage full coverage of plan items or RFP items with the section ledger (if `meta.structure` is plan or sections, lint checks full item coverage instead of the module and Task checks)
- List plan items and RFP items in `meta.rfp.tasks`
- Slides map to those items with `rfpTasks`
- (Planning study exception) Survey and planning projects ordered with an R&D budget
    + Contents follow the R&D plan
    + Content design uses the business planning skeleton
    + `meta.structure` is module

## Full Task coverage

### ID scheme

- RFP work item IDs (`T1`) are used only for internal tracking in the section ledger
- Task IDs (`M1-T2`) are identifiers designed by the bidder
- Task IDs appear in section titles and markers
- The section ledger keeps the mapping of RFP work item IDs, Task IDs and slide IDs
- The slide list of the section ledger maps one to one to the slide list of the storyboard

### Placing RFP work items

- Place every RFP work item in `meta.rfp.moduleTasks[].rfp` (omissions are lint FAIL)
- If the number of designed Tasks is below 60% of the number of RFP work items, record the reason for merging in `00_strategy.md` (lint WARN)

### Module overview slides

- Place one per module (none or two or more is lint FAIL)
- The template is `module_overview` (columns are Tasks, rows are process, data used, deliverables)
- For a custom slide used as a module overview, write its number under the module_overview role of the registration settings (`references/custom-slides.md`)
- Show every Task of the module (omissions are lint FAIL)
- Module overview slides are excluded from the Task slide appearance count

### Task slides

- Every Task appears in `moduleTasks` of at least one slide (non-appearance is lint FAIL)
- lint names Tasks without slides as missing numbers (for example T2 when only T1, T3 and T4 have slides)
- Number Tasks in a module consecutively from T1 (gaps are lint WARN)
- Slide items are survey target, data source, survey scale, analysis method, deliverable and one measured sample
- Section titles use the format `[Module 1] 모듈명` (the square brackets keep it from colliding with the period of the section number)
- Markers use the format `Task 2. Task명`
- Module items in the contents and dividers also use the format `[Module 1] 모듈명`

### Task slide layout

- Design a different layout that fits the content of each Task
- The Task slide layout check applies when there are three or more Task slides
- If all Task slides use the same layout, lint FAIL
- If the number of layout types is below half the number of Task slides (at least 2 types), lint WARN
- If three or more Task slides of one module all use the same layout, lint WARN
- Replace chart data, table values and item text of samples with engagement content
- If the number of items in a sample does not fit the engagement, adjust the number of items
- If it still looks awkward after adjusting, choose another recipe
- General layouts without topic restrictions
    + (chart_text) One chart and implications
    + (chart_two) Two charts and findings per chart
    + (table) Full-width table
    + (analysis_four) Four charts in quadrants
    + (key_numbers) Key figures and implications
    + (illustrative) Sample deliverable table with the Illustrative tag
- Examples by Task content
    + (Surveys and statistical analysis) chart_text, chart_two, analysis_four, key_numbers, market_sizing, pest_scan
    + (Cases and history) benchmark_cases, history_timeline
    + (Data comparison and lists) table, composite with two tables side by side
    + (Interviews and surveys) interview_plan, survey_design, interview_findings
    + (Analysis synthesis and screening) findings_synthesis, task_funnel, option_evaluation, strategy_review
    + (Procedure and stage design) verify_steps, kpi_development, steps
    + (Structure and system diagnosis) value_chain, industry_chain, alignment_pyramid, logic_model, business_model, swot, env_to_strategy
    + (Tasks and definition sheets) task_definition, project_breakdown
- For content not in the examples, choose a recipe with a matching purpose in `references/recipes.md`
- The parametric `task` is a layout that holds the Task design table (survey target, data source, survey scale, analysis method, deliverable) and a measured sample on one slide

### Volume

- One Task per Task slide is the default
- Use the `task_multi` group only when the contracting agency limits volume (without `meta.pageLimit`, lint FAIL)
- With a volume limit, group up to 2-4 Tasks per slide (3-4 is lint WARN, 5 or more is lint FAIL)
- `task_multi` is a matrix with Tasks as columns and item labels (data used, method, deliverable) as rows
- For row alignment, write items in the "label : value" format (`"활용자료 : 평가 규정"`)
- Even with a volume limit, mix matrix, table and step layouts
- 2-8 slides per module (outside the range is lint WARN)

## Project organization

### Templates

- The project organization chart uses the `org` template
- The staffing table uses the `table` template
- The staffing table columns are number, role, name, affiliation, major, degree, participation period, participation rate, career
- Write staff one per table row
- Include "투입인력" in the marker or section title so lint recognizes the staffing table
- Use `staff_card` to show the careers and track records of four or more people as cards
- staff_card omits the photo column when there are no photos

### Project organization chart layout

- The reporting line is a vertical arrangement in the order contracting agency, project lead (PM), quality manager (PL), module teams
- The quality manager is internal staff, so place it between the project lead and the module teams
- The advisory committee connects horizontally to the right of the project lead
- The number of module boxes matches the number of designed modules (fewer is lint FAIL)
- Module boxes are placed automatically in one row up to six and in two rows from seven (for large engagements and consortiums)

### Leader titles

- Use the leader titles written in the RFP
    + (Examples of overall leader titles) 총괄책임자, 연구책임자, 과제책임자, 사업책임자, PM
    + (Examples of quality leader titles) 품질관리자, 품질책임자, PL, QA 책임자
- If the RFP has no leader titles or the engagement does not designate leaders separately, confirm in the kickoff questions
    + (Example confirmation question) "What should the overall leader and the quality leader of this engagement be called? Without a designation, I will write 총괄책임자 and 품질관리자"
    + If the user does not answer, use 총괄책임자 (PM) and 품질관리자 (PL)
- Use one title per role within a deck (mixing is lint WARN)

### Staff consistency

- Place the project organization chart and the staffing table together (only one of them is lint FAIL)
- The staff sets of the two slides match (staff on only one side is lint FAIL)
- Staff recognition formats of lint
    + (Staff cells) In the pm, qa and team member cells of the organization chart, the name cells of tables whose header row has a name column, rows labeled with a name, and the name of staff_card, the name at the front of the cell is recognized regardless of the job title (for example 김수연 in "김수연 부사장")
    + (Other text) `[인력A]` and "name + consulting firm or research institute job title" are recognized (for example 수석컨설턴트, 수석위원, 책임연구원, 시니어 매니저, Partner)

### Company organization chart

- The company organization chart uses the `orgchart` template
- The organization slide created by company2slides.py is a bullets layout with expertise per team
- If an organization structure diagram is needed, replace that slide with `orgchart`
- The capacity is 2-8 divisions and 1-6 teams per division
- With nine or more divisions, only the first eight are typeset (build warning)
- Management support (left of the CEO) and the advisory committee (right of the CEO) are placed in the same row as the CEO to keep the reporting line to one horizontal line
- The organization chart shows only division names and team names
- Every team is typeset as its own box without abbreviation
- The maximum of 8 divisions and 6 teams is supported in a full-width layout without the staff table
- On slides with the staff table, if there are seven or more divisions, the organization chart width is enlarged to 76% of the body width
- If vertical space is still short after enlarging, build warning
- Present staff composition with the `people` table

## Contents

- Design the contents according to the RFP and the purpose of the document
- Without an RFP designation, start from the chapter structure 제안개요, 제안업체 현황, 사업수행계획, 사업관리부문 (`references/skeletons.md`)
- Choose only the sections the engagement needs from the skeleton's section candidates

## Score attribution

- Attribute every non-quantitative detailed evaluation item to `evalItems` of at least one slide (zero is lint FAIL)
- Quantitative evaluation items (credit rating, number of track records) are excluded from slide assignment
- If the slide share of an evaluation item is half or less, or twice or more, of its score weight share, lint WARN
- Internal evaluation vocabulary in slide text (배점, 채점, 방어 논리, 결정 장소, 귀속) is lint FAIL

## Headlines

- Fix headlines at the storyline step
- The storyboard writing step uses the fixed headlines as they are
- For slides with topic patterns, replace only the keywords in the patterns of `references/headline-patterns.md`
- For topics without a pattern, write the headline as a conclusion sentence that follows the writing rules
- The headline limits are 50 characters for one line and 100 for two lines (over 50 is lint WARN, over 100 is lint FAIL)
    + Characters are Hangul-equivalent characters (text width divided by the width of one Hangul syllable; English decks use the same width basis)
- Page sizes narrower than 16:9 reduce the one-line limit by the headline width ratio (A4 43 characters, 10.83×7.5 40 characters, 4:3 37 characters; the two-line limit is twice the one-line limit)
- Write headlines as conclusion sentences (lint WARNs a topic label of 2-12 characters with no space, such as "추진배경")
- Headlines are typeset at 18pt for both one and two lines
- Shorten the text to fit a headline on one line
- check_layout reports inconsistent headline font sizes
- Write grounds, conditions and assumptions in `note` or `footnotes` (the build adds ※ before a note)
- Set one emphasized phrase in the `accent` field

### Subject term

- Use the RFP term first for the subject term
- Without an RFP term, choose by the nature of the output (`references/headline-patterns.md`)
- Even if the public contract form is an academic research service, refer to consulting content as 본 과업
- If there are several candidate terms or no RFP term, confirm in the kickoff questions
- If the user does not answer, use 본 과업 for public engagements and 본 프로젝트 for private ones
- Use one subject term within a deck (mixing is lint WARN)
- Replace engagement expressions in template labels and sample text with the chosen subject term (the replacement list is in the subject term section of `references/headline-patterns.md`)
- The exceptions are RFP form names (과업지시서, 과업 세부내용) and structural labels such as VISION and SCOPE
- An engagement label left in a non-proposal output is lint WARN
- Change proposal-only labels to fit the output type
    + Set labels shared by the whole deck once in `meta.labels` (keys and defaults in the label slots section of `references/templates.md`)
    + Change the label text of the Point band (default "수행 Point") with `meta.pointLabel`
    + Change the engagement column header and the report row group name of the gantt (defaults "과업", "보고회") with `taskHead` and `reportHead` of gantt
    + Set the company name on the cover and closing slides with `meta.company`

## Writing rules

- Read `references/writing-rules.md` before writing the storyboard
- (Sentences) One message per sentence, noun-ending style in the body
- (Simple sentences) Simple sentences with one subject and one predicate
- (Symbols) Replace em dashes with commas or periods
- (Phrases) The lists of lint FAIL expressions and lint WARN vocabulary follow `references/writing-rules.md`
- (Fixed wording) Keep the standard spelling of key RFP wording
- (Figures) Mark unconfirmed figures with the `[확인 필요]` placeholder
- (Point band) Use the band only for judgment criteria, formulas, follow-up links, selection reasons, timing or principles that are not in the headline or body
    + Delete a band that only repeats the headline or summarizes the body
    + Write one-line formulas or conditions in `footnotes` to free body height
- lint reports writing rule violations as FAIL and WARN

## English decks

- English decks use the same templates, build and review procedure
- The writing rules, the headline style (kickoff question 5) and the lint writing rule checks apply only to Hangul text
    + The em dash and en dash checks also apply to English text (lint FAIL)
- Template and block default labels are Korean, so set English labels for the whole deck in `meta.labels` (keys, defaults and an English example in the label slots section of `references/templates.md`)
    + The resolution order is the slide slot value, then `meta.labels`, then the default
    + Set only the labels that differ per slide in the slots
    + In a deck where only some slides are in English, set only the labels of the templates those slides use, or set them in the slots of those slides
    + Keys left out are typeset with the Korean defaults, so set every label of the templates the English deck uses
    + lint reports unknown template, block and slot names and type errors in `meta.labels` as FAIL
- Set the 수행 Point band label with `meta.pointLabel` or `meta.labels.common.pointLabel`
- The scope structure labels (visionTag, scopeTag, outputTag) are typeset at 10pt, so write them in uppercase Latin letters (other text gets the check_layout 11pt minimum WARN)
- Set the language tags of the PPTX text with `meta.labels.language` (default latin en-US, east_asia ko-KR for runs that contain Hangul; finalize.py applies them)
- Keep the placeholders (`[회사 확인]`, `[확인 필요]`) as they are in English decks, since lint finds unfinished items by them
- The common part (company2slides.py output) is generated with Korean text, so translate it into English after copying it into the storyboard
    + Translate headline, marker, section, chapter and slot text
    + Keep id, template, slot keys and placeholders as they are
- Source and note lines starting with "Source:" or "Note:" are recognized the same way as "출처:" and "자료:"
    + Add note tokens of other languages in `meta.labels.notation.source` (the built-in tokens stay)
- Headline and marker character limits are checked in Hangul-equivalent characters (about twice as many English characters fit in the same width)
- English names and English staffing tables are recognized as described in `references/storyboard-schema.md`
- In the visual review, check that no slide still shows a Korean default label

## Design system

- (Band) Section number 32pt, section title 20pt, chapter tracker on the right 18pt
    + The headline area is between the upper line (y 1.05) and the lower line (y 1.80)
    + The headline is 18pt bold, centered between the two lines
    + The marker is typeset at y 2.02 with a square shape and 18pt bold
    + The body area is y 2.32-6.92 (the footnote and source rows are based on y 6.78)
    + If the marker text is empty, the marker shape is omitted
    + The body area stays the same even when the marker is omitted
    + Source 10pt, page number 11pt at the bottom right
    + The coordinates above are inches for 16:9 (other page sizes are converted by the page height ratio)
- (Page size) `tokens.scaled()` converts coordinates per page size
    + Set the page size with `meta.layout`
    + build.js and lint.py apply the `--layout` argument over `meta.layout`
    + The body width relative to 16:9 is 87.7% for A4, 81.2% for 10.83×7.5 and 75.0% for 4:3 (ratio of widths)
    + The text volume of the samples (`assets/recipe-demos.json`, `assets/proposal-templates.json`) is for 16:9
    + For page sizes narrower than 16:9, shorten box text by the body width ratio (overflow is reported as a build warning and check_layout FAIL)
    + When typesetting several page sizes from one storyboard, write shortened text for narrow page sizes in `byLayout` of the slide (`references/storyboard-schema.md`)
    + Label columns and subject boxes are typeset at least as wide as the longest word fits on one line
- (Color) The color scheme is black and white
    + Choose the theme from navy (default), mono and a user-specified color (kickoff question 6)
    + Use the theme color (navy #1F3864, mono #2B2B2B, the user-specified base color) only for label cells, chevrons, conclusion bands, markers and emphasized figures
    + The mono theme sets tints and secondary gray text in achromatic colors too
    + Body panels and table bodies use a white background with a 0.5pt gray border
    + Emphasis red #C0392B is used in one place per slide
- (User-specified color) Write the color the user chose in `meta.themeColors.base` as a six-digit color code
    + For a color given by name, write a representative color code and tell the user the code applied
    + The build computes the colors of conclusion bands, charts and tints from the one base color (computation rules in deriveTheme of `scripts/tokens.js`)
    + If the base color's contrast with white text is below 4.5:1, the build lowers its lightness and prints the color codes before and after the adjustment
    + Record the adjusted color code in the completion report
    + The pastel color that carries white text (navyPastel) is computed at a lightness with a white text contrast of 3:1 or more
    + To set a specific color separately, write that color key together with base (written keys take precedence over computed values; the key list is in the themeColors color key section of `references/storyboard-schema.md`)
    + If a directly specified color key falls below the contrast minimum for the text color placed on it, lint WARN
    + Assign light brand colors to keys that carry body text (navyPastel2, navyRamp items 2-3) and dark colors to keys that carry white text (navy, navyDeep, navyPastel)
- (Typeface) NanumGothic
    + Bold text uses the family name NanumGothic with the bold attribute (the same way PowerPoint saves bold formatting)
    + Use Hanja within the 4,888 KS X 1001 Hanja that NanumGothic contains
    + Hanja outside the range (some name Hanja, extension Hanja) are replaced by another font in PowerPoint, so write them with Hanja in the range or in Hangul
    + Body 12pt, dense tables 11pt, panel headers 14pt
    + The minimum font size for body text is 11pt (footnotes, sources and page numbers are exceptions)
    + Uppercase English structural labels such as VISION and SCOPE keep their original size, so they are excluded from the 11pt minimum check
    + Font handling in custom slide playback follows the playback corrections in `references/custom-slides.md`
- (Spacing) 0.20 inch between shapes, 0.42 inch from slide edges
    + Inner margins are 0.07 inch for text boxes, 0.045 inch left and right for theme color label cells, 0.05 inch left and right and 0.03 inch top and bottom for table cells
- (Tables)
    + Table cell fills use only the theme color, tints, gray and white
    + Set white for empty cells
    + Capability comparisons use Harvey balls with the ● ◐ ○ symbols in table cells
    + The circle color of Harvey balls is the body text color
    + Place the Harvey ball legend above the table
    + Column widths are computed automatically from the one-line width of cell text
    + Groups of continuous data columns, such as role codes, yearly figures and evaluations per option, have the same width
    + Bullets apply only to cells with two or more items (text wrapped into several lines is one item)
    + Number columns are right-aligned for easy comparison of digits
    + Columns with only single-item cells, other than number columns, are centered
    + Columns with multi-item cells and diagnostic question columns (sentences ending in question forms such as "는가", "인가", "는지") are left-aligned
    + The vertical alignment of cells is centered for the whole table
    + The cells of one column are either all single-item or all multi-item
    + Table text fill below 60% is a build warning
    + Row height limits are 0.5 inch for text-only one-line rows, the height holding 1.3 line spacing for multi-line rows (0.8 inch or less), and 0.8 inch for tables with Harvey balls
    + Multi-line cells widen line spacing up to 1.3 as far as the row height allows
    + Adjust the number of rows and row heights so the table ends within the body area
- (Table merging) Decide at the storyboard writing step whether to merge rows or columns with continuing identical values
    + The criterion is the relation between neighboring rows
    + Merge rows where a higher-level category (category, stage, module, owner) actually continues
    + Do not merge rows whose values are the same by chance, tables where each row is an independent item, or comparison tables that must show row-by-row correspondence
    + Merging is specified with the `merged` field of the storyboard
    + The builder merges only as specified by `merged`
- (Alignment) Horizontal alignment is uniform per column, vertical alignment is uniform per row
    + A single item is centered without a bullet, even when it wraps into several lines
    + Two or more items use left-aligned bullets and vertical centering
    + Cells of the same column use the same horizontal alignment
    + Cells of the same row use the same vertical alignment
    + Boxes of the same level placed side by side use the same horizontal and vertical alignment
    + Short label boxes are centered
    + A single box with a different alignment is limited to cases with a clear emphasis purpose
- (Vertical fill) Distribute the remaining height of a panel to the item spacing (18pt limit)
    + The spacing distribution is based on the remaining height measured with PowerPoint line height (1.4 times the font size)
    + Fonts keep the level's reference size during filling
    + The target fill ratio is 70% or more
    + If a bullet box with two or more items still has more than 45% empty space after widening item spacing to 18pt, build warning (empty space)
    + A fill ratio below 45% in bordered boxes and in text boxes within panels is a check_layout warning (not enough box content)
    + Body vertical fill below 70% is a check_layout warning
    + Code warnings are a floor
    + If half or more of a box looks empty to the eye, fix it even without a warning
- (Horizontal fill) Text width is judged by an estimated width, the measured font width divided by a slack factor of 0.9 (about 11% wider than the actual rendered width)
    + Bullet boxes with a box text fill average below 65% or a longest line below 80% get a build warning (box text fill)
    + Synthesis boxes with an average below 90% or a longest line below 95% get a build warning
    + A synthesis box item longer than one line gets a build warning
    + Parametric panels (bullets, cards, conclusion, compare row pairs) shrink the box width to the longest line and center the group
    + Resolve box text fill warnings by adding to item text (target, criterion, figures) or narrowing the cell
    + Boxes and tables with placeholders (`[회사 확인]` and so on) are excluded from the horizontal fill check
- (Height allocation) Rows side by side (`labeled`, `vsteps`) all get the same height if the longest row fits within the average height
    + The height limit of parametric panels is the height with item spacing widened to 18pt
    + Groups of parametric panels are centered vertically in the body
    + The spacing between row label boxes and content boxes is 0.14 inch (secured by narrowing the label box)
    + The natural height of composite text box blocks is 1.6 times the needed content height
    + The limit to which a composite block stretches to match neighboring cells is the capacity height of each block (grid section of `references/recipes.md`)
    + The remaining height of a composite is distributed in the order diagram rows, block capacity heights (table row heights, spacing between boxes, diagram size), spacing between rows (0.55 inch limit), vertical centering margin
    + If a composite cell height is smaller than the needed content height, the build warns of overflow risk
    + Among side-by-side composite cells, a cell with short content is centered vertically below the cell title
    + A composite cell holding only one table that is 0.3 inch or less shorter than its neighbor gets taller rows so the top and bottom ends align
    + The body group is placed in the body area so the margin below the marker equals the margin above the page number
- (Fill fixes) The order of fixes is adding content, shrinking and rearranging boxes, changing the form of expression, merging or restructuring slides
    + Apply the next step only when the previous one does not resolve the issue
    + On overflow, reduce the number of characters and items while keeping font size and alignment
    + When shrinking boxes, move the whole group to the center of the body by the freed space
    + If it still looks awkward after shrinking and rearranging, change the form of expression among table, chart, chevron and diagram
    + Fill empty space with elements that add information (share column, Harvey ball column and so on)
    + Write added items from facts confirmed in engagement material
    + For large cells, decide the scope of content first
    + The default vertical alignment of content boxes is centered
    + Top-fixed alignment is used only for notes and sources
- (Editing existing slides) When the user points out a defect in a specific slide, fix only the defect pointed out
    + Keep shape coordinates and sizes, connection structure, and header and label formatting
    + Fix defects that need a layout change only after user consent
    + After the fix, compare shape coordinates with the original to confirm only the intended changes remain
- (Shapes) The basic shapes of parametric, composite and free templates are rectangles, rounded rectangles with a radius of 0.05 inch or less, chevrons, straight lines, orthogonal connectors (split into straight lines) and circles
    + Diagram-specific shapes (flow arrows, Harvey ball pie slices, trapezoids of the strategy and house roofs, triangles and trapezoids of pyramid, funnel strips, porter arrowheads, storage cylinders, ellipses and diamonds of flowchart) are used only in their diagrams
    + Do not use icons, gradients, shadows, 3D, pill-shaped boxes, full-width color strips, vertical side strips, decorative lines below titles, or repeated grids of identical cards
- (Charts) Use native charts only
    + Composition uses pie charts (six slices or fewer) or stacked bars
    + Item comparison uses horizontal bars in descending order
    + Time series use vertical bars or lines
    + Show data labels
    + No gridlines
    + Show the legend only on multi-series charts
    + Chart colors are the pastel family of the theme color
    + For bar charts with negative values, the builder typesets a zero baseline and room for figures below negative bars
- (Images) Set a path or data URI in `src` of image blocks in composite and free
    + Without a logo, use the company name as text
    + An image block without `src` is typeset as a dashed placeholder box
    + check_layout warns about the small text of placeholder boxes
    + Before delivery, set an image for placeholder boxes or replace them with another block

## Briefing deck

- For short material used at reporting occasions, such as meeting reports, executive reports and sharing research results
- Set the volume limit with `--max`
- One chapter is one slide
- Sections within a chapter are placed as panels
- Omit dividers and contents
- Add cover and closing slides when needed
- Rewrite the headline as one conclusion sentence per chapter
- Split detailed grounds into appendix slides or switch to a report-style PPT
- The output of `md2storyboard.py --kind brief` is a skeleton draft, so finish it by refining headlines and templates

## Slide variety

- The variety criteria apply to every output type
- The unit of the variety check is the layout type
    + composite slides with the same recipe name are the same layout type
    + composite slides without a recipe name are distinguished by the number of grid cells and the combination of block kinds
    + Custom slides are distinguished by `own:N` number
- The share checks apply when there are eight or more body slides (excluding digest slides)
    + The number of layout types is at least 30% of the number of body slides (at least 3 types; below is lint WARN)
    + The share of one layout type is 40% or less of body slides (above is lint WARN)
    + Slides filled only with bullet panels are half or less of body slides (above is lint WARN)
    + If five or more slides of one chapter all use the same layout type, lint WARN
- The same layout type can be placed up to three times in a row (four in a row is lint WARN)
- Choose layout types by content type
- Typeset content that can be expressed as a table, chart, diagram or chevron in that form
- Use tables or charts for figure comparison, chevrons or process diagrams for procedures and stages, and comparison tables for contrasts

## Layout type selection

- Slides with a set structure (cover, contents, divider, background and purpose, goals and scope, features, strategy, process, module overview, schedule, project organization) use parametric templates (`references/templates.md`)
- Analysis, survey design, methodology and management plans use composite recipes (`references/recipes.md`)
- For recipe slides, copy slots from the sample with the same recipe in `assets/recipe-demos.json`
- Replace the text and figures of copied slots with engagement content
- For simple structures without a recipe, use table, chart_text, chart_two, cards and steps
- Use the free template only for slides that templates and recipes cannot hold (3-8 slides per deck recommended; more than 8 is lint WARN)
- If the user provides their own PPTX, register custom slides with the procedure of `references/custom-slides.md`
- If a custom slide fits the content, use `own:N` first
- List boxes (experience, track record, strengths, roles) fill 70% or more of the box height (the target fill ratio of the design system)
- If material is short, find additional grounds to secure facts
- Write the secured facts split by role, deliverable and performance figure
- Without material, ask the user or switch to a layout whose volume fits
- If text exceeds the box capacity, reduce the number of characters or items according to build warnings and check_layout results
- Replace placeholders in company fact recipes, features and staff_card (`[전문분야]`, `[N]명`, `[대표 실적]`, `[회사 확인]`) with bidder material
- The build replaces only the company name token (`__COMPANY__`) with `meta.company`
- Expert collaboration recipes (collaboration_structure, advisory_plan) are used in R&D program planning review response and R&D business planning engagements of wording track rnd (the planning committee practice of those two engagement kinds)
- Wording tracks mgmt and general use only the advisory committee slide (advisory_plan) or omit it
- Performance analysis recipes (performance_framework, representative_outcome, feedback_plan) follow the analysis areas and introduction items of the national R&D program performance analysis framework, so use them in R&D performance analysis engagements
    + Confirm analysis areas, outcome types and introduction items in the performance evaluation guidelines of the year
    + Non-R&D support program performance surveys and analyses use the indicator structure by input, output and outcome type in `references/methods.md`
- Use the common part by copying slides from the `common-slides.json` that company2slides.py made in the work folder
- Adjust id, chapter and secNo of the copied common part to the contents and keep the content as is
- If the original text or sample figures fit the engagement poorly, rewrite them to fit the engagement

- Argument part samples are `assets/proposal-templates.json` (one slide per parametric template) and `assets/recipe-demos.json` (one slide per recipe)

## Renderer compatibility

- The reference renderer for delivery is PowerPoint
- Review images (`render.sh`) are LibreOffice renderings
- finalize.py applies word-level line breaking (eaLnBrk=0) to every paragraph to prevent PowerPoint from breaking Korean words in the middle
- finalize.py restores the top and bottom margins of table cells in the cell properties (marT, marB) to prevent tables from overflowing when PowerPoint applies default margins
- finalize.py sets NanumGothic as the East Asian font of chart text (categories, legends, data labels) to prevent chart Hangul from switching to the theme default font
- finalize.py records the language of text runs that contain Hangul as ko-KR, so LibreOffice re-saving does not store Hangul in another language (zh-CN etc.) depending on the runtime locale
- finalize.py makes hyphen bullets ("-") follow the text font to prevent PowerPoint from showing these bullets as empty boxes
- LibreOffice rendering ignores word-level line breaking, so if review images show cut words, shorten the text
- A word wider than the inner width of a text box or table cell is cut in the middle by every renderer (check_layout WARN)
- Resolve wide words by spacing them, shortening them or widening the box
- PowerPoint uses taller line heights than LibreOffice, so spacing distribution in bullet boxes is computed with PowerPoint line height (1.4 times the font size)

## Review system

- Completion is judged from the record of viewing the rendered PNGs
- (lint) Checks of `scripts/lint.py` (remaining WARNs are a failure)
    + (Structure) Schema, full Task coverage, section ledger consistency, score attribution, volume limits, page size names and paths of page-size-specific text (`byLayout`)
    + (Notation) Writing rules, RFP wording, subject term, section numbers, ※ notes, duplicated prefixes, text contrast on theme colors
    + (Typesetting) Layout variety, bullet overuse, empty table cells, volume of replaced text, remaining slot markers
- (Structural check) Checks of `scripts/check_layout.py` (remaining WARNs are a failure)
    + (Overflow) Estimated text overflow, estimated mid-word line breaks in text boxes and table cells, tables leaving the slide
    + (Overlap) Overlap between text boxes (over 20% WARN, over 30% or over a picture FAIL), overlap among tables, charts, pictures and filled boxes (over 15% FAIL, over 25% between filled boxes FAIL), overlap of icons and text (FAIL)
    + (Overlap judgment) Labels inside content boxes are judged by the text area per line
    + (Overlap exclusion) Text that fits entirely inside a shape (text placed on a shape, such as stage names on funnel strips) is excluded from the icon overlap check
    + (Placement) Body margin imbalance (over 15% on one side and below 15% on the other), insufficient body vertical fill (below 70%), edge margins, leaving the band, empty panels, not enough box content
    + (Notation) Headline font consistency, body text below 11pt, two or more accent colors, missing bullets in multi-line text, mixed table alignment
- (Visual review) Create PNGs with `scripts/render.sh` and view all of them
- View them as contact sheets of 3-6 slides (`python3 scripts/sheet.py <png_dir> <out.png> 1,2,3 --cols 3`)
- List the viewed contact sheet file names in the completion report
- (Visual review questions) Questions to check for every slide
    + With the headline covered, does the body alone lead to the same conclusion?
    + Is the first place to look decided within three seconds?
    + Is the visual weight balanced left and right, top and bottom?
    + Do elements of the same level have the same size and spacing?
    + Do differences in color and weight correspond to differences in meaning?
    + Is there a monotonous stretch where the same layout type continues?

### Visual check items

- Check defects that code checks miss in the PNG of every slide
- The cover and the background and purpose slide set the first impression, so check them first and in detail
    + Do the notes of the background and purpose slide start with ※?
    + Are grounds attached to item text by line breaks?
    + Does every lead have a one-sentence title and 2-3 grounds?
    + Is the cover title exactly centered between the two horizontal lines?

#### Overflow

- Does text cross a box border or start outside the box?
- Is text cut inside a table cell or does it cross the cell border?
- Are Korean words broken in the middle at the end of a line?
- Does a table go below the body area and get cut, or leave the slide?

#### Overlap

- Do icons, pictures or shapes cover text?
- Do boxes overlap each other, or do connectors pass through boxes?
- Do roadmap and gantt bars touch lane dividers or neighboring bars?
- Do connectors and arrows float away from boxes?
- Do chart labels overlap rings, bars or other labels?

#### Placement

- Do the headline, marker or page number intrude on band borders or edge margins?
- Is content pushed to one side, leaving the other side largely empty?
- Is a bordered box less than half full so it looks empty (judge even without a code warning)?

#### Alignment

- Does horizontal alignment differ by cell within the same table column (right alignment mixed with other alignments in a number column)?
- Does vertical alignment differ by row so text heights look uneven?
- Is a table category column left empty without merging so the table looks broken?
- Do boxes placed side by side use different alignments (centered on one, left on the next)?
- Is one-line text stuck to the left, or multi-line text scattered in the center?

#### Notation

- Is the purpose of text smaller than the body clear (※ attached to grounds, sources and assumptions)?
- Do font sizes differ within the same level?
- Does one bullet in a box use a different font and stand out?

#### Color

- Do table headers or cell backgrounds use colors outside the palette (sky blue, orange and so on)?
- Are unit rows or empty rows transparent so the default table style color shows?

#### Fixes

- Fix found items in the storyboard and rebuild
- Judge defects that look like renderer differences by the PowerPoint standard

### Judging defects outside the rules

- Treat elements that look wrong as defects even if no rule covers them
- Examples of defects outside the rules
    + The layout is broken and elements are scattered or pushed to one side
    + A shape or line is left half drawn
    + One slide shows a different style of font, color or spacing
    + Alignment varies within the same column or among boxes of the same level (left, center and right mixed)
    + Icons or markers unrelated to the content appear
    + Empty boxes, empty tables or charts without values remain
    + The same content appears in two places
    + A connector touches nothing or points the wrong way
    + The section number appears twice (the section number is repeated in the section title after the band number)
    + A number or symbol appears twice (a bullet or hyphen is written again in text after a bullet shape)
    + Several items have no bullets so the lines run together
    + ※ is missing from notes and sources
    + A section number, marker or bullet is missing where it should be
    + Only some items of the same level are numbered
- The criterion is whether a practitioner would be called out for it when submitting the deck
- Choose the fix among storyboard edits, layout type changes, emptying slots and splitting slides
- Reproduce defects with unknown causes by building the slide alone
- Record the grounds for fixes and remaining defects in the completion report

### Visual adjustment discretion

- If text looks cramped or large areas are empty in review, adjust within the slide
- The adjustment means and their order are line spacing distribution, box size adjustment, moving elements
- Change font size only when changing it for the whole level together
- The adjustment scope is all elements of the same level
- After adjusting, check again the left-right and top-bottom weight and the spacing between levels
- If an adjustment breaks the proportions of the template, revert it
- After adjusting, rerun check_layout to confirm there is no overflow or overlap
- If a result typeset by the rules looks bad, choose the better-looking option
- Record adjustments that depart from the rules, with the change and the reason, in one line of the completion report

### In-depth review

- Following `references/review.md`, review once from the evaluator's perspective the slides attributed to detailed evaluation items worth 10 points or more
- The review items are figure integrity, source reliability, logical leaps, response to underlying needs, discriminating power, RFP response and respect for the contracting agency

### Completion conditions

- The outputs are an editable PPTX and a PDF for viewing (created with `scripts/topdf.sh`)
- lint and check_layout exit code 0 (WARNs also count as failures)
- Zero build warnings
- finalize.py and validate.py pass
- A record of viewing all PNGs
- 100% coverage in the section ledger (RFP work items, Tasks, slides)
- Placeholders in company facts resolved
- A WARN passes only when it is fixed or `--allow-warn "reason for keeping"` is added
- If `--allow-warn` is used, write the reason as is in the completion report
- The last step is the PNG visual review
- A completion report without viewed file paths counts as incomplete

## Notice

- 본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.
    + (English) This product was developed with reference to the public documentation of the Hancom Hangul document file format (.hwp)

## File structure

```
ieum-deck/
├── SKILL.md
├── package.json, package-lock.json   pptxgenjs pinned to 3.12.0
├── scripts/
│   ├── tokens.js            Page sizes, band, colors, typeface, limits (shared with lint through limits.json)
│   ├── limits.json          Copy of the limits and judgment values of tokens.js (updated on build, read by lint and check_layout)
│   ├── atoms.js             Atomic elements (text, shapes, lines, tables, charts, images), band, custom slide playback, shrinking based on measured widths
│   ├── templates.js         Parametric templates and free
│   ├── composite.js         Grid and blocks of the composite template
│   ├── labels.js            Lookup of the fixed template and block labels (slide slot, then meta.labels, then assets/labels.json)
│   ├── build.js             storyboard → pptx (--layout, --digest, --marker, --theme)
│   ├── finalize.py          OPC normalization, shape id renumbering, duplicate pPr removal, adj application, word-level line breaking, doughnut hole preservation, table cell fill normalization, table cell margin restoration, language tags (meta.labels.language), bullet font correction, soffice reserialization
│   ├── validate.py          Package structure validation (content types, XML syntax, relationship targets, slide ids, shape ids, python-pptx opening; schema validation when OOXML_PML_XSD is set)
│   ├── lint.py              storyboard checks
│   ├── check_layout.py      Checks of the typeset result
│   ├── render.sh, topdf.sh  PNG rendering, PDF conversion
│   ├── sheet.py             PNG contact sheets
│   ├── parse_input.py       hwpx, hwp, pdf, docx, pptx, xlsx, html, csv, json, xml, epub, md, txt → md (--pdf converts hwpx to PDF)
│   ├── extract_images.py    Source document → candidate images and manifest.json
│   ├── md2storyboard.py     Hierarchical md → storyboard draft
│   ├── company2slides.py    company.md → common-slides.json
│   ├── own_extract.py       pptx for custom slides → own-deck.json (--inspect, --config)
│   ├── own_catalog.py       own-deck.json → slot list document
│   ├── compare.py           Comparison of a source PDF and reproduced PNGs
│   └── setup_deps.py        Dependency installation and --check
├── assets/  labels.json (label defaults), font-metrics.json, company.md, common-slides.json, proposal-templates.json, recipe-demos.json
└── references/  storyboard-schema.md, templates.md, recipes.md, custom-slides.md, headline-patterns.md, strategy.md, methods.md, review.md, wording.md, skeletons.md, writing-rules.md
```

## Common failures

- (Missing Tasks) Starting the storyboard without a section ledger
    + Complete `ledger.json` first, before the step 3 user confirmation
- (Organization chart and staff mismatch) Fixing staff later than the organization chart
    + After fixing the staff list, place everyone in the organization chart
- (Bloated common part) Converting the whole manuscript into slides
    + Edit the content of the common part in company.md
- (Too much theme color) Filling body panels with the theme color
    + Use the theme color only for label cells, chevrons, conclusion bands, markers and emphasized figures
- (Lower headline quality) Writing new headlines at the storyboard writing step
    + Fix them at the storyline step by pattern replacement or by writing conclusion sentences
