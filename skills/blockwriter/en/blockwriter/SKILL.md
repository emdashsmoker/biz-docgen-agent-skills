---
name: blockwriter
description: "Typesets Korean-style reports (policy, research, planning) from one Markdown manuscript into HWPX (Hancom Hangul) or DOCX (Word) and reviews them by rendering. Two code-generated forms (chapter: 제N장 numbering; flat: N. numbering) place heading, □, ○, -, ㆍ, ※ levels, tables (numbered captions, unit and source rows, header shading, merging, long tables), figures, footnotes, cover, TOC, header, and page numbers. Also extracts user HWPX forms, fills blanks, and converts DOCX, XLSX, and HWPX into manuscripts. Use when the user mentions hwpx, Hangul or Hancom documents, Korean or Word reports, md to hwpx or docx, docx to hwpx, hwpx forms or rendering, or asks to produce, edit, or extract .hwpx or report-style .docx files; prefer it over a general docx skill for report-style Word documents. references/manuscript.md: manuscript notation and writing rules. references/layout.md: form values, typesetting rules, DOCX mapping, TOC, user forms, review items. references/renderers.md: renderer setup and limits, fonts."
license: AGPL-3.0-or-later with an output exception. Terms in LICENSE and NOTICE.md
---

# blockwriter

> This English version was translated from the Korean original (blockwriter). Differences in wording may make it behave differently from the original intent. When results differ, the Korean version is the reference.

The "block" in the name comes from the woodblock. In woodblock printing, a board carved with text is inked, paper is laid on it and rubbed, and the same page is printed again and again. This skill uses a code-generated form as the block, prints a Markdown manuscript on it, and produces reports of the same shape again and again.

- Typesets one Markdown manuscript on a code-generated form and produces an HWPX or DOCX report file
- Both formats share the same manuscript, the same form definition (scripts/form.py), and the same typesetting rules (scripts/config.py)
- DOCX, XLSX, and HWPX inputs are first converted into a Markdown manuscript and then typeset the same way
- Official letters and approval drafts (공문, 기안문) are out of scope

Run every command as `python3 scripts/report.py <command>`. The command notation below omits `python3 scripts/report.py`.

## Terms

- (Hangul) Hancom's word processor (한/글) that opens HWPX files
- (Labels) The fixed strings that build prints into documents (numbering such as 제N장 and 가., caption labels 표 and 그림, the TOC title) and the language tags written into the files. The default labels are Korean, and a label file (`--labels`) switches them for documents in other languages. Style names stay in Korean. The Korean tokens of the manuscript notation (such as `<표>`, `출처:`) are always accepted and are written exactly as shown; a label file can add tokens in another language
- (Manuscript) The Markdown file that is the input to typesetting. Its notation rules are in references/manuscript.md
- (Heading) A Markdown line that starts with `#`. The number of `#` sets chapter, section, subsection, or 가나다
- (가나다) The heading level numbered with Korean letters in order (가., 나., 다.)
- (Role) The kind of a manuscript element: chapter, section, subsection, 가나다, key point, claim, support, detail, note, source, table, figure, and so on. build applies the style set for each role
- (Level) The hierarchy of headings and body symbols from chapter down to note (※)
- (Output format) The file format that build produces. HWPX (Hangul) or DOCX (Word)
- (Form) The set of styles, fonts, bullets, and page settings for each role
    - (Built-in form) chapter and flat. Defined in scripts/form.py, and build generates them as styles of the output format every time
    - (User form) An HWPX report form provided by the user. The skeleton command turns it into a skeleton and a draft profile
- (Skeleton) An empty HWPX document that keeps only the style definitions and the page settings of the body section from a user form
- (Profile) A JSON file that lists the form style name and numbering format applied to each role. The built-in forms are specified by the names `chapter` and `flat`
- (Review renderer) A program that draws a document as a PDF and page PNGs for review (rhwp, LibreOffice). It approximates the layout of Hangul and Word

## Setup

```bash
pip install -U python-hwpx python-docx lxml pillow openpyxl fonttools --break-system-packages
```

- Try to install the latest versions first and work with the installed latest versions
- If a latest API change breaks a script, update the script to the latest API
- Pinning a version is the last resort when the script cannot be updated. If pinned, state the reason in the final report
- Review rendering needs a renderer. For HWPX obtain one in this order: rhwp release binary, rhwp source build, LibreOffice with H2Orestart. DOCX uses LibreOffice. The procedure is in references/renderers.md
- Page PNGs and TOC page numbers need poppler-utils (pdftoppm, pdftotext). Without them render produces only the PDF and build leaves TOC page numbers empty
- The built-in forms use 나눔고딕 (NanumGothic), with 나눔바른고딕 (NanumBarunGothic) only for flat headings. For both fonts, only the NAVER release has Hanja. Check installation and Hanja coverage with `fonts` and set up downloads and substitute fonts with `fonts --setup`. The font policy is in references/renderers.md

## Commands

| Request | Command |
|------|------|
| Report with chapters | `build manuscript.md output.hwpx --profile chapter` (for DOCX, `output.docx`) |
| Report without chapters | `build manuscript.md output.hwpx --profile flat` (for DOCX, `output.docx`) |
| Report on a user form (HWPX only) | `skeleton form.hwpx skeleton.hwpx`, then `build manuscript.md output.hwpx --profile skeleton.profile.json --skeleton skeleton.hwpx` |
| Save a built-in form as an empty file | `form chapter form.hwpx` or `form flat form.hwpx` |
| Fill form blanks (HWPX only) | `fill document.hwpx replacements.json [-o output.hwpx]` |
| View an existing HWPX | `export document.hwpx manuscript.md [--image-dir folder]` |
| Manuscript for re-editing an existing HWPX | `export document.hwpx manuscript.md --profile chapter` (levels restored. Figures, footnotes, and super/subscripts are not restored) |
| Convert DOCX to a manuscript | `docx2md document.docx` to print paragraph types, then `docx2md document.docx manuscript.md --map mapping.json` |
| Convert XLSX to a manuscript | `xlsx2md table.xlsx manuscript.md [--allow-wide]` |
| Visual review | `render document.hwpx [--engine auto\|rhwp\|soffice] [--rhwp path] [--outdir folder]`, `render document.docx [--outdir folder]` |
| Structure check | `check document.hwpx [--expect "--expect-min-tables 2"]` (schema, image manifest consistency, rhwp verify), `check document.docx` (structure summary) |
| Font check | `fonts`, `fonts --setup` |

build options

- The output path extension (.hwpx, .docx) decides the output format. If the output path is omitted, `--format hwpx|docx` (default hwpx) and the manuscript file name decide it
- (`--profile chapter|flat|profile.json`) Required. DOCX accepts only chapter and flat
- (`--page-break chapter|section|none`) The heading unit that starts a new page. chapter starts a new page at each chapter (`#`), and section at each chapter and section (`##`). none breaks pages only at `---` lines. Default chapter
    - (flat) `#` is the single document title, so chapter breaks pages only at `---` lines, the same as none. section starts a new page at each N. heading (`##`)
- (`--long-table engine|split`) How tables over 25 rows including the header rows (long tables) are handled. engine splits one table at page boundaries and repeats the unit row and header rows on every page. split divides it into several tables, each with the header row. Default engine
- (`--merge auto|explicit|none`) How table cells are merged. auto merges consecutive identical values in leading label columns and the `^` and `<` directives, and explicit merges only the directives. Default auto
- (`--numbered-square`) Prints `□ 1. title` lines as numbered headings without the □ bullet. When the title wraps to two lines, the second line aligns with the text after the number
- (`--page-number`) Footer page number `- N -` at center. Default OFF, so that page numbers do not clash when several documents are combined into one
- (`--toc`) Inserts a table of contents at the front. Default OFF
    - (`--toc-depth 1|2|3`) TOC depth (1 up to chapters, 2 up to sections, 3 up to subsections). Default 2
    - Entries are the title, a dotted tab, and the page number. Page numbers are written only when `--page-number` is also given
    - Page numbers are approximations computed by rendering. build fills them in, renders again, and prints the check result (TOC section of references/layout.md)
    - Forms without TOC styles (including flat) skip the TOC with a warning
- (`--cover "title=title;subtitle=subtitle;date=date;org=organization"`) Cover page. Default OFF. Title 24pt bold, subtitle 16pt, date 14pt, organization 16pt bold, centered
    - If a long title risks pushing the cover past one page, adjust only the cover values in config.py (the blank line counts and font sizes whose names start with COVER_)
- The cover and TOC go in a front section and the body starts a new section. Body page numbers start at 1
- (`--header "text;align=LEFT|CENTER|RIGHT"`) Page header. Default OFF. Alignment defaults to right. Applies only to the body section
- (`--skeleton skeleton.hwpx`) Skeleton extracted from a user form (HWPX only)
- (`--rhwp path`) rhwp executable used for TOC page numbers (HWPX)
- (`--labels labels.json`) Label file for a document in another language (Labels section below). Default OFF (Korean labels)

The fill replacement JSON has the form `{"replace": {"old text": "new text"}, "cells": {"label > right": "value"}}`. A `cells` key finds the table cell that contains the label text and then points to the cell reached by moving in the given directions (left, right, up, down). Directions can be chained with `>` (for example `"합계 > down > right"`). If the label text appears in more than one table cell of the document, the target cell cannot be determined and fill reports it as failed, so use text that appears only once as the label.

The `--expect` value of check is passed as is to rhwp verify as its expectation arguments. Wrap condition values that contain spaces in single quotes (for example `--expect "--expect-contains '가상 기획 수치'"`). Table count conditions also count the one-column tables that hold figures. The text-contains condition (`--expect-contains`) searches body paragraphs and table cell text. Footnote and caption text are outside its search scope. Expectations are checked only when rhwp is available and `--expect` is given. HWPX check returns exit code 1 if there is any schema issue, image manifest mismatch, or failed expectation.

## Procedure

- Create and edit documents only with the scripts/report.py commands. The commands keep the form's styles, bullets, and numbering references intact in the document
- When an error occurs, use its message to find the cause in the manuscript, the profile, or the script and fix it. If generating a built-in form fails, first check the python-hwpx version and installation

1. (Plan) Ask the user all of the following at once and continue after the answers. Do not ask again about items the request already answers. If the user explicitly says to run immediately, proceed with the defaults
    - (Output format) HWPX (Hangul) or DOCX (Word). Work on a user form is HWPX only. Recommend choosing one format. Producing both repeats the rendering review and fixes for each format, which uses more of the working context and can lower review quality. If the user wants both, state this in one line and proceed
    - (Purpose) chapter for a chaptered document of a full report. flat for a standalone document or a partial manuscript to insert into a full report. A cover and TOC are optional regardless of purpose
    - (Form contrast) Show this when asking about the purpose. chapter sets the 제N장, N.N, N.N.N, and 가. headings in NanumGothic bold and restarts caption numbers in each chapter (표 1-3). flat sets the document title, N., and N.N headings in NanumBarunGothic bold and the 가. headings in NanumGothic bold, and numbers captions continuously through the document (표 3). The body levels □, ○, -, ㆍ, ※ and the body font NanumGothic are the same in both forms. Only chapter has TOC styles
    - (Page breaks) Choose chapter, section, or none. build reports the number of short sections with fewer than 8 elements on a `HITL: [page-break]` line. Under section, each page that holds a short section ends with a large blank area
    - (Long tables) Choose engine or split. build reports those tables on a `HITL: [long table]` line
    - (Missing styles in a user form) If build reports with `WARN:` a style missing from the profile, choose among deriving it from a close style, adding a style to the form, or merging into an existing level
    - (Optional elements) Page numbers, TOC, cover, and page header are OFF by default, so ask whether each is needed. Also ask for the TOC depth (chapter, section, subsection), the cover title, subtitle, date, and organization, and the page header text. Change the page header alignment from right only when the user asks
    - (Document language and labels) Korean labels by default. If the user wants a document in another language, write a label file with the labels of that language (references/layout.md, Labels) and pass it with `--labels`
2. (Manuscript) Write the Markdown manuscript with the level rules below and the writing rules in references/manuscript.md
3. (Typesetting) Run build and act on each output line prefix
    - (`LINT:`) A manuscript defect. Fix the manuscript and run build again
    - (`HITL:`) A typesetting choice for the user (page breaks, long tables). build prints it only when `--page-break` or `--long-table` is not given, so pass the items decided in step 1 as options
    - (`WARN:`) A typesetting warning such as a missing style or a missing image
4. (Review) Check the structure with check, open the page PNGs made by render, check the review items in references/layout.md, and do a free review. Save the review PDF and PNGs outside the delivery folder with `--outdir`
    - (Column width defect) Only for a table whose automatically sized column widths show a defect in the rendered PNGs, add a column width line (references/manuscript.md) to the manuscript and build again. Run the first build without column width lines
5. (Report) Give the user the following
    - Output path, what was fixed, which renderer was used, and the fallback reason
    - (Renderer limits) One line saying that the review renderers are approximate, so the result may look different in Hangul or Word
    - (DOCX TOC) If a TOC with page numbers was inserted, one line saying that Word asks whether to update fields when it opens the document, and that choosing "Yes" updates the TOC with Word's page numbers
    - (Font notice) If `fonts` can run on the computer where the user opens the documents (the skill runs on that computer or can send commands to it), run it. If every form font (NanumGothic, plus NanumBarunGothic for flat) is installed with all Hanja present, skip the notice. If a font is missing or lacks Hanja, name it and give the installation steps for the user's computer in references/renderers.md
    - (Remote workspace) If the user's computer cannot be checked, skip the font notice and the question about font installation. Give the installation steps when the user mentions a font or Hanja display problem

## Manuscript level rules

| Manuscript notation | Role | chapter | flat |
|------|------|------|------|
| `# title` | chapter | 제N장 title, new page | document title (centered, 20pt bold) |
| `## title` | section | N.N title | N. title |
| `### title` | subsection | N.N.N title | N.N title |
| `#### title` | 가나다 | 가. title | 가. title |
| `□ title` | key point | □ | □ |
| `- statement` | claim | ○ | ○ |
| `    - statement` | support | - | - |
| `        - statement` | detail | ㆍ | ㆍ |
| `※ remark` | note | ※ | ※ |
| Source lines such as `출처: ` | source | after a table or figure: source row. After body text: footnote of the previous paragraph | same |

- Heading number removal and automatic numbering, bullet level ranking, inline formatting, footnotes, table and figure notation, and source and unit lines are in references/manuscript.md
- The rules for statements under □, keyword versus sentence style, and the use of section numbers and 가나다 are also in references/manuscript.md

## Differences between formats

- Both formats share fonts, sizes, bold, character width ratio, character spacing, alignment, margins, line spacing, bullet symbols, and the table and figure rules
- DOCX supports only the built-in forms (chapter, flat). User forms (`--skeleton`) and fill are HWPX only
- DOCX puts the chapter, section, subsection, and 가나다 headings on Word's built-in heading styles so that the navigation pane and the TOC field recognize them
- DOCX mapping rules such as unit conversion, caption number fields, the TOC field, footnotes, and the font table are in references/layout.md

## Labels

- (Customizable) Heading number formats (chapter, section, subsection), the letters and format of the 가나다 level, the TOC title, caption label words, marks, and Word SEQ field names, extra manuscript tokens (source, unit, table caption, figure caption, column width), and the language tags of DOCX and HWPX
- (How) `build manuscript.md output.docx --profile chapter --labels labels.json`. A nested JSON object; omitted keys keep the defaults. Unknown keys and invalid values stop build with the list of all problems. Works for HWPX and DOCX and for both built-in forms
- (Defaults) Without `--labels`, documents get the Korean labels (제N장, 가., 목  차, 표, 그림)
- (Manuscript tokens) The Korean tokens stay recognized. A label file only adds tokens (for example `Source:`, `<Table>`, `(Unit: )`)
- The key table with defaults and a complete English example are in the Labels section of references/layout.md

## Converting existing documents

- (DOCX) docx2md step 1 prints counts and samples for each combination of style name, indent, autonumbering, and leading symbol. After agreeing on the level mapping for each combination with the user, step 2 creates the manuscript. Add table captions and figures in the manuscript
- (XLSX) xlsx2md creates a table caption line and a pipe table for each sheet. If a sheet has more than 6 columns, ask the user whether to transpose or split it. If the user keeps it as is, pass `--allow-wide` to turn the warning off and proceed. Add caption titles, unit lines, and source lines in the manuscript
- (HWPX) Create a leveled manuscript with `export --profile`, edit it, then build. Paragraphs whose role cannot be found from the style name get a role guessed from the leading symbol and numbering pattern

## Notice

- 본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다. (This product was developed with reference to Hancom's published HWP document file (.hwp) specification.)
- Hangul, Hancom Office, and HWPX are trademarks of Hancom Inc. This tool is independent and not affiliated with Hancom Inc.
