# Manuscript rules

> Translated from the Korean original (blockwriter). When results differ, the Korean version is the reference.

Save the manuscript file as UTF-8. The role of each notation follows the manuscript level rules table in SKILL.md. Korean tokens shown below (such as `<표>`, `(단위: )`, `출처:`, `(조판 조정: )`) are part of the notation, are written exactly as shown, and are always recognized. A label file (`--labels`, Labels section of references/layout.md) adds tokens in another language, such as `<Table>`, `(Unit: )`, `Source:`, which work the same way.

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
    - Some documents use `위의`, as in `위의 보고서`, `위의 자료` or `Ibid.`, for the same source as the footnote just before. Use one convention within a document
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
- Insert only files or URLs the user provided
- webp is converted to JPG when inserted. If the file does not exist, build prints `WARN: image not found` and skips that figure

## Attached lines

Attached lines are the source lines and ※ note lines that belong to a table, a figure, or a body paragraph.

- (Source line) A line starting with `출처:`, `자료:`, `주:`, `(출처)`, or `(자료)`. `(출처)` and `(자료)` are printed as `출처:` and `자료:`. Tokens added by a label file work as `token:` and `(token)` (`(Source)` prints as `Source:`)
- (Several sources) When one table or figure has two or more sources, write the source label once and separate the sources with `;`. Choose between line breaks and joining
    - (Line breaks) End a source with `;` and write the next source on the next line. build breaks the lines inside the source row and aligns the second and later lines with the start of the first source
    - (Joining) Write all sources on one line, separated by `; `
    - (Line break example) Write a `자료: Agency(year), Title;` line, then an `Agency(year), Title;` line, then an `Agency(year), Title` line. The last source has no `;`
    - (Continued lines) After a source line that ends with `;`, a blank line or a line that starts with another manuscript notation (heading, bullet, table, figure, caption, unit, ※ and so on) is not read as a continuation
- (Choosing the arrangement) When the user chose automatic in step 1, decide the arrangement for each table and figure by the criteria below. The aim is a source row that looks right next to its table or figure
    - (Default) Line breaks. Long sources and two or three short sources read more easily with one source per line
    - (Many short sources) When many short sources would make the source row tall with line breaks, join them
    - (Other cases) Even with long sources, joining is occasionally the better choice depending on the editing situation, such as the width of the table or figure and the page layout
    - (Check) In the rendered PNGs, check that the height and width of the source row suit the table or figure, and change the arrangement when it looks awkward
- (Fixed arrangement) When the user chose fixed line breaks or fixed joining in step 1, pass `--source-layout break` or `--source-layout inline` to build. The whole document is typeset one way, whatever line breaks the manuscript has
- (※ note line) A line starting with `※` or `* ` (an asterisk and a space)
- A `> ` line gets its role from its content. It is a source line if it starts with a source line notation, and a ※ note line otherwise
- Source lines and ※ note lines right after a table or figure are attached to the source rows of that table or figure. The ※ and * symbols are kept, and a `※ 출처:` line is attached as a `출처:` line
- To keep a ※ note line off a table or figure, leave one blank line between them. ※ note lines after the blank line are treated as body notes
- A source line after a body paragraph becomes a footnote of the previous paragraph. A source line written over several lines is joined into one line in the footnote. A source line with no previous paragraph in the same section prints as a ※ note paragraph, and build reports it with the `[source line position]` lint
- Write the sources of body statements as `[^n]` footnotes
- Write source lines for tables with external data and figures taken from outside. Explanatory tables, methodology tables, methodology figures, and figures made with generative AI get no source line
- Sources and notes cite only external material the reader can look up (do not cite items such as the target RFP, input files, internal documents, the user's request, or the drafting process)

## Adjustment lines

An adjustment line changes the glyph ratio, letter spacing or line spacing of a paragraph or table slightly from the form style values. Use it only when the user turned on the ratio and letter spacing adjustment or the line spacing adjustment in the step 1 plan. The criteria for targets and values follow the Typesetting adjustment section of references/layout.md.

- (Single line) A `(조판 조정: 장평 -3, 자간 -2)` line applies to the one element right after it. An element is a heading, a body paragraph or a table
- (Range) Applies to every element from a `(조판 조정 시작: 줄 간격 -10)` line to just before the `(조판 조정 끝)` line
- (Items) Write only the items needed among 장평 (ratio), 자간 (letter spacing) and 줄 간격 (line spacing), separated by commas. The English names `ratio`, `spacing` and `line` and the range words `begin` and `end` are also recognized
- (Values) A change in %p against the form style value. With a style ratio of 100%, `장평 -3` gives 97%. With a style line spacing of 160%, `줄 간격 -10` gives 150%
    - (Why changes) The ratio, letter spacing and line spacing differ between styles, and a user form has other values. Written as a change, the same notation gives the same degree of adjustment in any form
- (Tables) Put the adjustment line of a table before the caption line. It applies to the text of the table cells including the header rows, and not to the caption, unit row or source row
- (Single line inside a range) A single line inside a range applies to the next element together with the range adjustment. For the same item, the single line value is used
- (Recommended range) Ratio ±5%p, letter spacing ±5%p, line spacing ±10%p. build reports a value beyond the range with `WARN:` and typesets the given value
- (Lint) An unreadable item is reported as `[adjustment value]`, and an end line without a begin line or a begin line without an end line as `[adjustment range]`

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
