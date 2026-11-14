# Manuscript rules

> Translated from the Korean original (blockwriter). When results differ, the Korean version is the reference.

Save the manuscript file as UTF-8. The role of each notation follows the manuscript level rules table in SKILL.md. Korean tokens shown below (such as `<표>`, `(단위: )`, `출처:`) are part of the notation, are written exactly as shown, and are always recognized. A label file (`--labels`, Labels section of references/layout.md) adds tokens in another language, such as `<Table>`, `(Unit: )`, `Source:`, which work the same way.

## Level notation

- Numbers in headings (`## 1.1 배경`, `# 제2장 현황`, `#### 가. 개요`) are removed, and the form's numbering assigns numbers automatically. Numbers in a label file's number format (`# Chapter 2. Status`, `#### (b) Overview`) are removed the same way
- If a heading level is skipped (`###` right after `#`), build reports it with the `[heading skip]` lint. 가나다 (`####`) may sit right under a section or a subsection
- Bullet markers `-` and `+` are treated the same
- Bullet levels are ranked by indent width. Across the whole manuscript, the shallowest width is a claim (○), the next width is support (-), and any deeper width is detail (ㆍ)
- Lines that start with the symbol itself (`○ statement`, `□ title`, `※ remark`) get the role that matches the symbol. For a bullet followed by a symbol (`- ○ statement`), the symbol decides the role
- A plain paragraph without a symbol is treated as a claim (○) statement
- A line containing only `---` is a page break

## Inline formatting

- The supported inline formats are `**bold**`, `*italic*`, `^superscript^`, `<sup>superscript</sup>`, and `<sub>subscript</sub>`
- Inline formats apply in body paragraphs, table cells, and footnote definitions
- `` `text` `` is printed as plain text with the backticks removed
- A footnote reference is written as `[^1]` in a body paragraph, and its definition `[^1]: content` can be anywhere in the manuscript. build attaches the footnote at the reference position
- build reports a reference without a definition with the `[footnote undefined]` lint, and a definition that no body paragraph references with the `[footnote unused]` lint
- HWPX bullet symbols take the character shape of the line's first character. A line that starts with `**bold**` prints its symbol in bold too

## Source footnote inheritance

This is how a footnote that cites the same source again is written. The default is off, and it applies only when the user chose short form or merging in the planning questions of step 1.

- (Scope) The unit the user chose among □, section, chapter, and whole document. When the scope changes, the same source counts as a first citation and the full source is written again
    - The □ scope runs from a □ line to just before the next □ line or heading. The section scope runs from a `##` heading to just before the next `##` or `#` heading. The chapter scope runs from a `#` heading to just before the next `#` heading
    - In the flat form `#` is the single document title, so the chapter scope equals the whole document
- (Off) Every footnote gives the full source
- (Short form) The first footnote in the scope gives the full source. Later footnotes for the same source put a short form that fits the document type after the organization or author name (year), written directly in the footnote definition
    - (Examples) `기관명(연도), 앞의 보고서`, `저자명(연도), 앞의 논문, p. 12`, `저자명(연도), 앞의 책`, `기관명(연도), 앞의 자료`, `저자명(연도), op. cit., p. 79`, and so on
    - Choose the short-form word by document type: 보고서 for a research report, 논문 or 글 for a journal article, 책 for a book, 자료 for press releases, ministry materials and web materials, and so on
    - Some documents use `위의`, as in `위의 보고서`, `위의 자료`, `Ibid.` and the like, for the same source as the footnote just before. Use one convention within a document
    - When the cited page differs, write the page after the short form
    - When the user gives a citation rule or the user form shows a notation, follow it
- (Merging) In the manuscript every footnote gives the full source in the same text. With `--footnote-merge scope` on build, footnotes with the same text inside the scope become the first footnote, and the later citation positions show the first footnote number in superscript
    - A footnote with different text stays a separate footnote. Write the same source in the same text, and keep citations of different pages as separate footnotes
    - Footnotes moved from source lines after body paragraphs are merged too
    - Check the number of merged citations on the build completion line (`merged footnote references`)
    - The number is a Hangul cross-reference in HWPX and a Word footnote number reference field in DOCX. The typesetting is in the object placement section of references/layout.md

## Tables

- A table is written as a `<표> title` caption line followed by a pipe table. build assigns the caption number automatically
- Put the caption line right before the table. Only a unit line and a column width line may come between the caption and the table. For a table without a caption, build reports the `[no table caption]` lint
- The default position of the `(단위: )` (unit) line is between the caption and the table. If it is written before the caption or right after the table, it still moves to the unit row above the table
- Write a unit line placed before the caption directly above the caption. If a table comes before it, leave a blank line between that table and the unit line
- Write a unit line for tables with numbers that need a stated unit to be read, such as amounts, ratios, and quantities
- A `(열 폭: 15, 20, 25)` (column width) line between the caption and the table sets each column's actual width as a percentage of the ○ level width. Each value is the width of one column. Write one value per column, separated by commas
    - (○ level width) The body width minus the level indent (the table width cap in the Table width section of references/layout.md). In the rendered PNGs it is almost the same as the width of one ○ paragraph line (from the ○ symbol to the line end)
    - (Sum) The sum of the values is the table width. `15, 20, 25` sums to 60, so the table is 60% of the ○ level width and sits in the middle of the body. A sum of 100 makes the table fill the whole ○ level width, so use it only for a table that needs all of that width
    - (Sum limit) The sum is 100 or less. Over 100, build prints a WARN and uses automatic sizing
    - (Over the no-wrap width) The no-wrap width is the width at which the longest line of each column fits on one line (the column need width in the Table width section of references/layout.md, computed without the reduction for the 2-line wrap). If the sum is 2 percentage points or more above the no-wrap width sum, build prints a WARN and uses the given values
- Use a column width line only for a table whose column widths the user asked for separately, or a table whose automatically sized column widths showed a defect in the render review. When writing the manuscript first, leave out column width lines and review the automatic sizing first. Judge defects by the review items in references/layout.md
- Set the values of a column width line that fixes a column width defect with the following steps
    - (Read the current width) Read the current width, as the table sum and per-column values, from the `INFO:` line that build prints for each table whose cells wrap and each table with a column width line. The values are % of the ○ level width, so they can be copied into a column width line as they are
    - (Redistribute between columns) Keep the width read as the sum and divide it among the columns again. When the third column wraps in a 3-column table about 50% wide, take width from the other columns and add it to the third, as in `(열 폭: 10, 12, 28)`
    - (Widen the table) Raise the sum only for a defect that redistribution cannot fix and that needs a wider table. Raise it only as far as the defect needs. The sum limit is the no-wrap width sum on the `INFO:` line (100 when that sum is over 100). Giving a column more than its no-wrap width does not reduce that column's line count
- Put the `출처: ` (source) line after the table
- Write a line break inside a cell as `<br>`
- A cell value `^` merges the cell vertically with the cell above, and `<` merges it horizontally with the cell on the left
- If the row right below the header contains `^` and has no numeric cells, it is treated as a multi-row header
- Inside a cell, lines starting with `○` (or `◦`, `ㅇ`, `ㆍ`, `·`, `•`) are printed as small-circle (◦) cell bullets, and lines starting with `- ` as - cell bullets. If a user form has no cell bullet styles, they are printed as table content with the symbol kept
- The `- ` cell bullet is a sub-level that starts one step further in than the ◦ cell bullet. Use it for detail statements under a ○ line
- When a cell holds two or more items, put a ◦ cell bullet on each item. A single item takes no cell bullet, even when it wraps onto several lines
- ◦ cell bullets on single-item cells are judged per comparison line. A comparison line is a line of cells that sets the same attribute side by side across subjects. In a table with subjects in columns (alternative comparison table, etc.), rows are the comparison lines. In a table with subjects in rows (project record table, etc.), columns are
    - (Comparison line condition) When half or more of the cells in a comparison line hold two or more items, every single-item cell in that line also takes a ◦ cell bullet. Header rows and label columns are not counted
    - (Whole table condition) When most list-type lines of a table carry ◦ cell bullets, the remaining list-type lines may also take ◦ cell bullets as whole lines. Judge by how the whole table reads. A list-type line is one whose cells can hold several items (lines with one value per cell, such as amounts, periods and years, are excluded)
    - (Line-level application) Added ◦ cell bullets apply to a whole line. Within a line that receives added cell bullets, do not mix cells with and without cell bullets
    - (Context judgment) The conditions above do not fit every table mechanically. Make the final call from the context of the whole table
- A ◦ item with `- ` cell bullets under it counts as a list even when it is the only one (handled like a cell with two or more items)
- In a manuscript you write or rewrite, put cell bullets by the rules above
- Keep the cell symbols in a manuscript the user provides
- Set column alignment with alignment markers in the table separator row (`---:` right, `:---:` center, `:---` left)
- Horizontal alignment is set per column
- Column alignment is judged from the whole table by the role the column plays in it (year 2005 goes center, amount 2,005 goes right)
    - (Quantity columns) Columns of numbers and units (amounts, counts, ratios, scores, weights, etc.) take `---:` (right) so that digits are easy to compare
    - (Columns read as one expression) Columns whose cells each read as one expression (categories, names, years, serial numbers, periods, formulas, short text, etc.) take `:---:` (center)
    - (Columns read line by line) Bullet lists, diagnostic questions and descriptive text (content, details and main activities columns, etc.) take `:---` (left)
    - (Marker example) The separator row of the project record table `| No. | Project | Year | Cases | Amount |` is `|:---:|:---:|:---:|---:|---:|`
- A quantity with a share or change added in parentheses (○○ cases (○○%), etc.) makes a quantity column
- An expression that mixes numbers with words for a condition, a point in time or an order (○○ points or more, ○○% (2030), year 4, stage 3, etc.) makes a column read as one expression even though it contains numbers
- Columns of the same nature use the same alignment in every table of a document
- A column that is hard to judge is centered
- Header rows are centered regardless of column alignment
- In a manuscript you write or rewrite, put an alignment marker on every column of every table
- Keep the alignment markers in a manuscript the user provides
- If a manuscript the user provides has tables without alignment markers, ask the user before typesetting whether to add markers
- Columns without a marker take the default alignment (columns with bullets go left, all other columns go center, number and descriptive text columns included)
- For tables over 25 rows including the header rows (long tables), a build without `--long-table` reports them on a `HITL: [long table]` line

## Figures

- Write a figure as `![caption](path or URL)`. Relative paths are resolved from the manuscript file location
- A `[그림] caption` line right after the figure is used as that figure's caption
- Write the source on the line after the figure (after the caption line, if there is one) as `※ 출처: ` or `출처: `
- `{폭 120}` at the end of a figure line sets the figure width in mm (`![caption](path) {폭 120}`). The height follows the original aspect ratio, and a value wider than the body width is reduced to the body width. A figure without it is typeset at the default size in the figure placement part of references/layout.md
- Insert only files or URLs the user provided
- webp is converted to JPG when inserted. If the file does not exist, build prints `WARN: image not found` and skips that figure

## Attached lines

Attached lines are the source lines and ※ note lines that belong to a table, a figure, or a body paragraph.

- (Source line) A line starting with `출처:`, `자료:`, `주:`, `(출처)`, or `(자료)`. `(출처)` and `(자료)` are printed as `출처:` and `자료:`. Tokens added by a label file work as `token:` and `(token)` (`(Source)` prints as `Source:`)
- (※ note line) A line starting with `※` or `* ` (an asterisk and a space)
- A `> ` line gets its role from its content. It is a source line if it starts with a source line notation, and a ※ note line otherwise
- Source lines and ※ note lines right after a table or figure are attached to the source rows of that table or figure. The ※ and * symbols are kept, and a `※ 출처:` line is attached as a `출처:` line
- (Several sources) When the source line of a table or figure has two or more sources, split the line at each source with `<br>`. build aligns the later lines with the start of the first source (`자료: 기관명(연도), 자료명<br>기관명(연도), 자료명`)
    - (One line) For a table or figure where all sources fit on one line and one line looks tidier, join them with `; ` (`자료: 기관명(연도), 자료명; 기관명(연도), 자료명`)
    - (Choosing) Decide for each table and figure from the number and length of the sources, the width of the table or figure, the page layout and the like
    - (Wrapped lines) When a source runs past one line, the wrapped lines also align with the start of the first source
    - (Source lines that become footnotes) In a source line after a body paragraph, `<br>` becomes `; `
- To keep a ※ note line off a table or figure, leave one blank line between them. ※ note lines after the blank line are treated as body notes
- A source line after a body paragraph becomes a footnote of the previous paragraph. A source line with no previous paragraph in the same section prints as a ※ note paragraph, and build reports it with the `[source line position]` lint
- Write the sources of body statements as `[^n]` footnotes
- Write source lines for tables with external data and figures taken from outside. Explanatory tables, methodology tables, methodology figures, and figures made with generative AI get no source line
- Sources and notes cite only external material the reader can look up (do not cite items such as the target RFP, input files, internal documents, the user's request, or the drafting process)

## Adjustment notation

This notation adjusts the width ratio (장평), letter spacing (자간) and line spacing (줄 간격) of a paragraph or a range. It is off by default, and each item is used only when the user chose the width ratio and letter spacing adjustment or the line spacing adjustment in the step 1 plan.

- (Notation) Write the item name and the adjustment value in braces, such as `{자간 -3}`, `{장평 -2, 자간 -3}`, `{줄 간격 -10}`
    - (Value) An integer in percentage points added to the style value. `{자간 -3}` on a style with 0% letter spacing gives -3%, and `{줄 간격 -10}` on a style with 160% line spacing gives 150%
    - (Style values) The width ratio and letter spacing of each built-in form style are in the built-in forms table of references/layout.md, and the line spacing is in scripts/form.py
- (One paragraph) Write it after a space at the end of a heading line or a body paragraph line (□, ○, -, ㆍ, ※). It applies to that paragraph only (`- statement {자간 -3}`)
- (A range) Written alone on a line, it applies to the paragraphs and tables from that line up to the next adjustment line. End the range with an adjustment line whose value is 0 (`{줄 간격 0}`)
    - An adjustment line replaces the previous adjustment line. Inside a range, a notation at the end of a paragraph overrides the same items for that paragraph
    - Tables take the line spacing only. To adjust one table, put an adjustment line before the caption line and another after the source lines
- (Recommended range) -5 to +5 for the width ratio and the letter spacing, and -15 to +15 for the line spacing. For a value outside it, build prints a `WARN:` and typesets with the given value
- (When) Add it in step 4 review, after finding the targets in the page PNGs
- (Amount) Use the smallest value that does the job. If an adjusted paragraph or page looks noticeably different from its neighbors, reduce the value

Width ratio and letter spacing adjustment

- (Targets) A paragraph whose last line holds only 1-2 characters, a paragraph where one overflowing line gives it a different line count from neighboring paragraphs of the same level, and the like
- (Order) Narrow the letter spacing from -1 in steps of 1 and build again. If the letter spacing alone is not enough, narrow the width ratio as well
- (Room at the line end) The review renderers tend to fit more characters on a line than Hangul. Choose a value that leaves room for 1-2 characters at the line end in the page PNGs
- (Shortening the wording) For a paragraph that adjustment within the recommended range does not resolve, also try shortening the wording, as far as the meaning is kept

Line spacing adjustment

- (Targets) A page with empty space at the bottom because a table, a figure or a few lines of a paragraph moved to the next page, facing pages that fill unevenly, and the like (Page fill section of references/layout.md)
- (Unit) Apply the same value to a whole page, consecutive paragraphs, a table and the like
- (Order) Narrow from -5 in steps of 5 and build again

## Content-writing rules

- Put bullet statements (`- statement`) right after a □. If the next element has a role other than claim, support, detail, or note, build reports it with the `[□ alone]` lint
- Chapter, section, subsection, and 가나다 headings are keyword-style noun phrases. Sentence-style messages go at □ and below
- For □, choose keyword style or sentence style (a 1-2 line message ending in a noun form) by the nature of the section, and use one style consistently within a section
    - (Argument sections) Background, necessity, implications, and strategy derivation sections use sentence style. Examples are "중앙정부는 공공 서비스 전환을 위한 제도 기반 마련" (the central government lays the institutional basis for public service transition) and "주요국의 기술 표준 경쟁 심화" (intensifying technical standards competition among major countries)
    - (Summary sections) Project purpose and scope, process, trend analysis, and related-law list sections use keyword style. Examples are "과업 범위" (project scope), "정책 동향" (policy trends), and "관련 법률 (제정 연도, 최근 개정 연도)" (related laws (year enacted, year last amended))
- The section and subsection levels form the TOC skeleton, so they stay fixed once the TOC is set. The levels that grow or shrink as needed are 가나다 and □
- Use section numbers only to the depth the content needs to be divided. The usual depth of a chapter document is the subsection (N.N.N)
- For a flat document, section numbers (`1.`, `2.`) and 가나다 are the natural structure. Use a subsection (`1.1`) only when a section needs one more level of division
- 가나다 is optional grouping. If a section has 4 or fewer □, place the □ directly without 가나다. With 5 or more, group them with 가나다
- Distribute □ evenly across 가나다 groups. If the split is lopsided, such as 4 □ under 가. and 1 □ under 나., rearrange the □ or remove the 가나다 grouping
- All formatting, including table header text and body text, uses the font, size, bold, and color set by the form styles as they are
- Use only the □, ○, -, ㆍ, ※ level system of the SKILL.md table, which is familiar to readers of public documents
