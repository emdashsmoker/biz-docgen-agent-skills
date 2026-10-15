# Typesetting rules

> Translated from the Korean original (blockwriter). When results differ, the Korean version is the reference.

Change form appearance only in scripts/form.py and typesetting values only in scripts/config.py. The length unit HWPUNIT is 1/7200 inch (1mm is about 283 HWPUNIT). Style names are Korean because they are the names stored in the documents.

## Built-in forms

Both forms are A4 (210 x 297mm) with 20mm left and right margins and a 170mm body width. chapter has 15mm top and bottom margins and 10mm header and footer areas. flat has a 15mm top margin, a 10mm bottom margin, a 10mm header area, and a 15mm footer area.

| Role | chapter style | flat style |
|------|------|------|
| chapter | 장 제목 (나눔고딕 (NanumGothic) 20pt bold) | 문서 제목 (나눔바른고딕 (NanumBarunGothic) 20pt bold, centered) |
| section | 절 제목 (나눔고딕 15pt bold) | 절 제목 (나눔바른고딕 15pt bold) |
| subsection | 소절 제목 (나눔고딕 14pt bold) | 소절 제목 (나눔바른고딕 14pt bold) |
| 가나다 | 가나다 제목 (나눔고딕 13pt bold) | 가나다 제목 (나눔고딕 13pt bold) |
| key point | □ 내용 (나눔고딕 13pt bold) | □ 내용 (나눔고딕 12pt bold) |
| claim | ○ 내용 (나눔고딕 12pt) | ○ 내용 (나눔고딕 12pt) |
| support | - 내용 (나눔고딕 12pt) | - 내용 (나눔고딕 12pt spacing 3%) |
| detail | ㆍ 내용 (나눔고딕 12pt) | ㆍ 내용 (나눔고딕 12pt spacing 2%) |
| note | ※ 내용 (나눔고딕 10pt) | ※ 내용 (나눔고딕 12pt spacing 2%) |
| table content | 표 내용 (나눔고딕 11pt width 95% spacing -5%) | 표 내용 (나눔고딕 10pt spacing -7%) |
| table content, left-aligned | 표 내용 왼쪽 (나눔고딕 10pt, left-aligned) | 표 내용 style derived as left-aligned |
| cell bullets | 표 내용 ○, 표 내용 - (나눔고딕 10pt, left-aligned, symbols ◦ and -) | 표 내용 ○, 표 내용 - (나눔고딕 10pt spacing -7%, left-aligned, symbols ◦ and -) |
| table caption | 표 제목 (나눔고딕 11pt bold) | 표 제목 (나눔고딕 11pt) |
| unit row | 단위 (나눔고딕 9pt) | 단위 (나눔고딕 9pt spacing -7%) |
| source row | 출처 (나눔고딕 9pt) | 출처 (나눔고딕 9pt spacing -7%) |
| figure caption | 그림 제목 (나눔고딕 11pt bold spacing -6%) | 그림 제목 (나눔고딕 11pt spacing -6%) |
| footnote | 각주 (나눔고딕 10pt, left-aligned) | 각주 (나눔고딕 9pt, left-aligned) |
| TOC | 목차 장 (나눔고딕 14pt bold), 목차 절 (나눔고딕 12pt) | none (TOC skipped) |
| body | 바탕글 (나눔고딕 10pt) | 바탕글 (나눔고딕 10pt) |

"width" is the character width ratio (장평) and "spacing" is the character spacing (자간).

- All fonts are NanumGothic, with NanumBarunGothic only for flat headings. A style uses the same font in every language slot. Where to get the fonts and how Hanja are shown are in the fonts section of references/renderers.md
- (Numbering) chapter uses 제N장, N.N, N.N.N, 가. in that order, and caption numbers restart at 1 in each chapter (표 1-1, 그림 1-1). flat uses document title, N., N.N, 가. in that order, and caption numbers run continuously through the document (표 1, 그림 1)
- (Bullet output) If a style's bullet setting is BULLET, Hangul and Word draw the symbol. For a style without a bullet, build writes the symbol character into the text
- (No stranded headings) The chapter, section, subsection, and 가나다 heading styles and the □ style are set to stay on the same page as the next paragraph
- Other values such as line spacing, paragraph margins, and the gap after bullet symbols follow the definitions in scripts/form.py

## Object placement

Table width

- A table is subordinate information under a ○ statement, so its column widths fit the text and keep it inside the ○ level. Only a table with so much information that its text-fitted width goes past the ○ level widens up to the cap
- The table width cap is the body width minus a level indent of 1500 HWPUNIT (about 5.3mm, TABLE_INDENT_MARGIN). The floor is 50% of the cap (TABLE_MIN_RATIO). The actual width is the sum of the columns' required widths
- The weighted length is the rounded-up sum of character widths counted in half-Hangul units. Full-width characters such as Hangul and Hanja count 2, Latin letters, digits, and symbols use NanumGothic widths per character (GLYPH_EM), a space is the HWPX 0.5em or DOCX 0.28em width (SPACE_EM_HWPX, SPACE_EM_DOCX) divided by half a Hangul width, and characters not in the width table count 1
- A line's width is its weighted length times the width of one weighted unit, plus the left and right margins of the paragraph inside the cell and the width of a cell bullet (symbol width, gap after the symbol, and width adjustment). Font size, width ratio, letter spacing, and margins come from the style that line uses (table body, table body left, cell bullet); a plain line takes the wider of table body and table body left
- A column's required width is the width of its longest line plus 1800 (COL_PAD_W). The minimum is 3000 (COL_MIN_W)
- A cell that spans several columns through `<` directives spreads its line width evenly over the spanned columns. Merge directive cells (`^`, `<`) are left out of the length calculation
- A column whose longest line is wider than 12000 HWPUNIT (about 42mm, 10 Hangul characters at 12pt, COL_ONE_LINE_W) is calculated with its width reduced to 60% (COL_WRAP_RATIO), assuming a 2-line wrap. The reduced width stays at 12000 or more, so names and short phrases within that width do not wrap
- If the sum exceeds the cap, short columns whose required width is at most an equal share (the cap divided by the number of columns) keep their required width, and the remaining width is divided among the other columns in proportion to their required widths. Those columns then wrap at similar ratios, so row heights stay even
- If the sum is below the floor, the columns are widened to the floor in proportion to their widths
- A table with a column width line in the manuscript takes its column widths from that line instead of the sizing above. Each column width is the table width cap times value/100, with no floor adjustment. The conditions for use are in the Tables section of references/manuscript.md

Cell formatting

- Alignment is decided for each column. The order of priority is the manuscript alignment marker, right for numeric-only columns, left for columns that contain a cell starting with a bullet, containing a line break, or with a weighted length over 20, and center otherwise
- Alignment is judged only on body cells, leaving out the header rows (including multi-row headers) and merge directive cells. Whether a cell is numeric is judged on its displayed text, without inline format markup such as bold
- Header rows use the center alignment of the table content style regardless of column alignment
- Cell borders are 0.15mm black. The left border of the leftmost cells and the right border of the rightmost cells are left open (EDGE_OPEN_SIDES)
- After merging, the left and right outer borders are set again from each cell's actual span. Merged cells that reach the table edge also have open outer borders
- Header rows use the same font, size, width ratio, and spacing as the table content and add only bold and the background `#D9D9D9`. Multi-row headers get the same formatting on every header row

Table attachments

- The unit row is a transparent merged row above the header, right-aligned. The source row is a transparent merged row below the table, left-aligned. Both are inside the table and move with it
- Unit and source rows use dedicated 9pt styles without bullets (단위, 출처). A ※ note line attached to the source rows is printed in the source style with its ※ or * kept
- Table captions go above the table and figure captions below the figure. The gap between the caption and the table is 850 HWPUNIT (about 3mm, CAPTION_GAP)
- The caption width is the width of its table or figure table. A long caption wraps within this width
- HWPX captions are caption objects attached to the table, and the number is an automatic number field. chapter restarts the numbering at 1 in each chapter through a number restart in the chapter's first paragraph

Merging

- Vertical merging (auto) merges consecutive identical values in the leading label columns (before the first numeric column, at most 2 columns, MERGE_LABEL_COLS)
- A label column is merged only inside the merge spans of the label column above it, so spans do not overlap or leave gaps
- The `^` directive works in every column. Horizontal merging happens only through the `<` directive. If a horizontal merge overlaps a vertical merge, build skips the horizontal merge with a warning
- `--merge explicit` applies only the directives, and `--merge none` merges nothing

Row layout

- Row height is a minimum height of 2000 HWPUNIT (ROW_BASE_H) plus 1400 (ROW_LINE_H) for each additional expected line. When the content overflows, Hangul and Word grow the row
- A row's expected line count is the line count of its cell with the most lines among the cells outside vertical merges. A cell's line count is the sum, over each line of the cell separated by line breaks, of its line width (see Table width) expressed in weighted units, divided by the line capacity and rounded up
- The line capacity is the cell's inner width divided by the width of one weighted unit. The inner width is the sum of the widths of the columns the cell spans minus the left and right cell margins
- A line's weighted length applies the width ratio and letter spacing of the line's style. A character's width is the glyph width times the width ratio plus the letter spacing, so with negative letter spacing narrow characters such as Latin letters shrink more relative to half a Hangul character
- One weighted unit is half the width of one Hangul character. One Hangul character is font size x (Hangul width ratio x width ratio + spacing), using the font size, width ratio, and spacing of the table content style. The Hangul width ratio 0.94 (CELL_HANGUL_EM) is measured on NanumGothic
- A vertically merged cell fits its lines into the total height of the rows it spans. Only the missing lines are added to the spanned rows in turn, so the row heights stay even
- Cell padding is 510 HWPUNIT left and right and 141 HWPUNIT top and bottom (CELL_MARGIN_LR, CELL_MARGIN_TB)
- A table whose row count, including the header rows, is over 25 (LONG_TABLE_ROWS) is a long table. The unit row and source rows are not counted
    - (engine) Splits the table by row at page boundaries and marks the unit row and header rows as title rows (rows that appear again at the top of the table on each new page). Hangul and Word repeat only title rows that run contiguously from the top of the table, so the unit row above the header is included in the title rows
    - (split) Divides the rows after the first row (header) into groups of 24 as separate tables and repeats the first row at the top of each table. The caption gets a sequence number (1), (2) at its end

Figure layout

- A figure is placed inside a transparent one-column table so that the figure and source rows move together (FIGURE_IN_TABLE)
    - (HWPX caption) A caption object attached to the table, so it moves with the table. HWPX sets the table's numbering type to figure and excludes the inner picture from the numbering count
    - (DOCX caption) A caption paragraph right after the figure table. Every paragraph in the table is set to stay on the same page as the next paragraph, so the caption stays on the figure's page
- The figure table width is the picture width plus the left and right cell margins (CELL_MARGIN_LR x 2), so the picture fits the cell's inner width as is
- Figure size depends on the width to height ratio. A landscape figure (1.4 or more) is 140mm wide, a portrait figure (0.8 or less) is 110mm high, and anything in between is 90mm wide. Without resolution information, 96dpi is assumed
- Tables and figures are centered in the body. The spacing before and after them comes from the paragraph margins of the table position and figure position styles

HWPX package

- (Image manifest) Right after build, the image entries in header.xml and the BinData files are checked against the content.hpf list, missing entries are registered, and a `Registered N image(s) missing from the manifest` line reports them. python-hwpx 6.5.0 registers only the first of several images when a document has a TOC or cover, and without the fix Hangul cannot open the remaining figures. The line reports the result of the fix
- check verifies the same consistency and the body references again

## DOCX mapping rules

DOCX converts the same form.py definitions into Word units.

- (Units) twip = HWPUNIT / 5, EMU = HWPUNIT x 127
- (Fonts) The Hangul slot font goes to Word's East Asian and complex script fonts, and the Latin slot font goes to the Latin fonts. The width ratio becomes the character scale, and the spacing becomes character spacing equal to the font size times the spacing ratio
- (Automatic spacing) Automatic spacing between Hangul and Latin text and between Hangul and numbers is turned off, the same as the HWPX paragraph setting
- (Language) The document default language is recorded as en-US for Latin text and ko-KR for East Asian text, the same pair as the default of Korean Word documents. A label file changes them (language.latin, language.east_asia)
- (Line spacing) Hangul's percentage of the font size becomes Word's minimum line height (font size x percentage). Because the two programs calculate line height differently, vertical positions can differ slightly
- (Paragraph margins) Carried over as they are, and a negative first-line indent becomes a Word hanging indent
- (Bullets) Word bullet lists (single level). The hanging indent is the sum of the symbol width, the gap after the symbol, and the width adjustment, so that the second line aligns with the text start line. The symbol width is 0.5 character for symbols whose Unicode East Asian Width is half-width (Na, H), which is the hyphen in the built-in forms, and 1 character for other symbols
- (Heading styles) chapter puts the chapter, section, subsection, and 가나다 headings on Word Heading 1-4. flat puts the document title on Word Title and the section, subsection, and 가나다 headings on Heading 1-3. The navigation pane and the TOC field recognize these styles
- (Other roles) Custom styles named after the form styles
- (Caption numbers) Word number fields (SEQ 표, SEQ 그림; the name follows the caption label of a label file) with prefilled results. chapter adds the chapter number as text, and the field restarts at 1 at each Heading 1. flat numbers continuously through the document
- (Caption width) The caption paragraph is indented on both sides by half the difference between the body width and the table width, so it wraps at the same width as the HWPX caption object
- (Footnotes) Word footnotes with `)` after the footnote number
- (Tables) A single row does not split across two pages. For tables of 25 rows or fewer, every row is kept with the next row so the table stays on one page. Long tables (engine) repeat the unit row and header rows as title rows
- (Page settings) Hangul keeps a separate header area between the top margin and the body. The Word top margin is the Hangul top margin plus the header area, and the header position is the Hangul top margin. The bottom works the same way
- (Front section) The cover and TOC go in a front section that starts on a new page, and the body section's page numbers start at 1. The page header and page numbers appear only in the body section. The page number is `- N -` at the footer center
- (Font table) For each form font, the English name (NanumGothic for 나눔고딕, NanumBarunGothic for 나눔바른고딕), the Hangul character set, and the family are recorded. The family is roman (serif) when the English name contains Myeongjo and swiss (sans-serif) otherwise. When a font is missing, Word uses this information to pick a font of the same family
- (Document properties) Author, last modified by, and comments are left empty, and the title is the cover title. The preview image attached to the template is removed

## Table of contents

- TOC entries go down to chapters at depth 1, to sections at depth 2, and to subsections at depth 3. Each entry is the title, a dotted tab, and the page number
- A TOC is created only on forms with TOC styles (toc_chapter, toc_section). flat has no TOC styles, so its TOC is skipped
- The HWPX TOC is static paragraphs. For a delivered document, rebuilding the TOC with Hangul's table of contents feature is recommended
- The DOCX TOC is a Word TOC field (`TOC \o "1-depth" \h \z`) with the entries and page numbers prefilled as its result. Without page numbers, the `\n` switch hides them
- The DOCX TOC is generated with the same structure as a TOC made by Word. Each heading gets a hidden bookmark (a name made of `_Toc` and a 9-digit number), each TOC entry gets a hyperlink to that bookmark and a `PAGEREF` page-number field, and a Word TOC content control wraps the whole TOC
- If a DOCX TOC with page numbers is inserted, the document is set so that Word asks to update fields when it opens. Choosing "Yes" recalculates the numbers with Word's layout. A TOC without page numbers does not ask
- The DOCX TOC collects its entries from the Word heading styles. If a heading's style is changed during manual editing, the heading drops out of the TOC. After editing, select the TOC and press F9 to update it
- When the TOC is updated, Word offers 'Update page numbers only' and 'Update entire table'. 'Update page numbers only' recalculates the `PAGEREF` fields from the bookmark positions, and 'Update entire table' makes Word rebuild the entries

Page-number calculation (when `--toc` and `--page-number` are both given)

1. Typeset a first-pass document that holds only the TOC entries
2. Render the first-pass document to a text-extractable PDF and get the text of each page in drawing order. HWPX uses rhwp, or LibreOffice with H2Orestart if rhwp is missing. DOCX uses LibreOffice, which updates the TOC field before saving. The rendering copy and the PDF are made in a temporary folder and removed, so only the document stays in the output folder
3. Starting from the first page that contains the TOC title (`목  차`, or toc.title of a label file), find the TOC entries in order. The pages up to the one containing the last entry are the TOC, and the next page is body page 1. The same applies when the TOC spans several pages
4. Find the TOC entries in order in the body and use the first page where each entry appears as its page number. The search for an entry starts at the page of the previous entry
5. Render the final document with the page numbers filled in and check it the same way. If there are mismatches, typeset again with the new values (TOC_MAX_PASSES, default 2)
6. build prints `TOC page check: filled numbers match the re-rendered page positions N/M` (M is the number of TOC entries) or a list of mismatched entries. Entries not found in the body get no page number and a `WARN:` line reports them
7. For HWPX, when a TOC heading sits at a page bottom in the final render and the first body line after it (lower headings and □ in between are skipped; tables and figures are found by their captions) starts on the next page, the `[stranded TOC heading]` WARN reports the heading and its body page number. As the WARN says, put `---` before that heading in the manuscript

- TOC entries and page numbers are matched by entry order, so headings with the same text do not get mixed up
- The body section starts at page 1, so a change in TOC length does not change the body page numbers
- The values are approximations based on the review renderer. If the renderer's line and page breaks differ from Hangul or Word, the values can differ

## User forms (HWPX only)

- The skeleton command (`skeleton form.hwpx skeleton.hwpx [--section N]`) produces, from a user form, an empty form that keeps only header.xml and the page settings of the body section (first paragraph), plus a draft profile (skeleton.profile.json). The body section defaults to the last section
- The skeleton drops the other sections, images, the preview, and the author and date metadata
- The draft guesses a style for each role from candidate names (built-in form names and short names common in report forms). Roles that are not found are null. Fill them in from the printed style list
- The cover, submission letter, research team page, and list of tables are not in the skeleton. Fill them in the original user form with fill or paste them in Hangul

Profile keys

- (numbering) manual writes the section and subsection numbers into the heading text. auto leaves the section and subsection numbers to Hangul outline numbering and writes no number into the heading text. Chapter numbers and 가나다 are written into the heading text in both modes
- (chapter_format, section_format, subsection_format) Heading formats. chapter_format uses `{n}` (chapter number) and `{t}` (title). section_format and subsection_format use `{c}` (number of the containing chapter, 1 if there is no chapter), `{s}` (section number), `{ss}` (subsection number), and `{t}`. Examples are `"제{n}장 {t}"`, `"{c}.{s} {t}"`, and `"{s}. {t}"`. The formats.* keys of a label file override these values
- (caption_prefix) Characters before the caption number. `"{c}-"` numbers captions per chapter, and `""` numbers them continuously through the document
- (Role keys) The values are style names. body, chapter, section, subsection, ganada, square, circle, dash, dot, note, table_pos, table_cell, table_cell_left, table_title, unit, source, fig_pos, fig_title
- (Optional role keys) toc_chapter, toc_section, table_cell_bullet, table_cell_dash
- A null or missing role is printed in the body style with a WARN. A style name that is not in the skeleton stops build with an error

Skeleton editing rules

- Renderers refer to bullet definitions by their position in the list, so add new bullet definitions at the end of the list in id order
- H2Orestart conversion needs the engName, langID, and lockForm attributes, so set them when adding a style
- Fix the margins and paper size before adding a page header or footer. python-hwpx computes the header and footer area width only once, from the margins at creation time, so a later margin change leaves that width out of step with the body width
- For the page header, the ctrl copy outside secPr is the effective one. Remove the copy inside secPr that the python-hwpx header setting creates, and set the paragraph alignment on the ctrl copy (`--header` does this automatically)

## Labels

The fixed strings that build prints into documents and the language tags it writes into files are labels. The defaults are Korean, so a build without `--labels` produces Korean documents. `build ... --labels labels.json` reads a nested JSON object with the keys below and works for HWPX and DOCX and for both built-in forms. The defaults are in LABEL_DEFAULTS of scripts/config.py.

| Key | Meaning | Default |
|------|------|------|
| formats.chapter | Chapter heading format. `{n}` chapter number, `{t}` title | the active profile's value: chapter `제{n}장 {t}`, flat `{t}` |
| formats.section | Section heading format. `{c}` chapter number, `{s}` section number, `{t}` | chapter `{c}.{s} {t}`, flat `{s}. {t}` |
| formats.subsection | Subsection heading format. `{c}`, `{s}`, `{ss}` subsection number, `{t}` | chapter `{c}.{s}.{ss} {t}`, flat `{s}.{ss} {t}` |
| letters.items | Letter sequence of the 가나다 level, one character per heading. After the last one it starts again | `가나다라마바사아자차카타파하` |
| letters.format | Number format of the 가나다 level. `{x}` letter. The title follows after a space | `{x}.` |
| toc.title | TOC title. The TOC page-number check also starts from the page with this title | `목  차` |
| caption.table.label, caption.figure.label | Caption label word | `표`, `그림` |
| caption.table.open, caption.table.close | Marks around the table caption label and number | `<`, `>` |
| caption.figure.open, caption.figure.close | Marks around the figure caption label and number | `[`, `]` |
| caption.table.seq, caption.figure.seq | Word SEQ field name of the caption number (DOCX). No spaces | the caption label |
| notation.source | Source line tokens (`token:`). Added tokens are also recognized as `(token)` | `출처`, `자료`, `주` (also `(출처)`, `(자료)`) |
| notation.unit | Unit line token (`(token: )`) | `단위` |
| notation.table | Table caption line token (`<token> title`) | `표` |
| notation.figure | Figure caption line token (`[token] caption`) | `그림` |
| notation.colwidth | Column width line token (`(token: 20, 30, 50)`) | `열 폭` |
| language.latin, language.east_asia | DOCX document default language (w:lang) for Latin and East Asian text | `en-US`, `ko-KR` |
| language.hwpx_package | HWPX document language (opf:language in content.hpf) | `ko` |
| language.hwpx_style_lcid | HWPX style language (langID, a Windows LCID integer) | `1042` |

- (Partial override) Omitted keys keep the defaults. Unknown keys, values of the wrong type, formats with unknown placeholders or without `{t}` (`{x}` for letters.format), and SEQ names with spaces stop build with the list of all problems
- (Profiles) formats.* overrides the active profile's formats (chapter, flat, or a user profile JSON). A label file for flat sets the flat formats; leave formats.chapter out for flat because the flat document title has no number
- (Caption) A caption prints as open, label, a space, the number, close, a space, and the title (`<표 1-1> title`, `[그림 1-1] caption`)
- (Manuscript tokens) notation.* only adds tokens. The Korean tokens stay recognized, so a manuscript may mix both. Tokens are matched as written (case-sensitive), and a space inside a token matches any spacing
- (Heading numbers) Numbers written in the manuscript in a label file's number format (for example `# Chapter 2. Status`, `#### (b) Overview`) are removed like `제2장` and `가.`, and the form's numbering assigns them again
- (HWPX language) language.hwpx_package and language.hwpx_style_lcid apply to the built-in forms. A user form (`--skeleton`) keeps its own values
- (Not labels) Style names (장 제목, □ 내용 and so on, names stored in the form), font names, the level symbols □ ○ - ㆍ ※, the page number `- N -`, and the footnote mark `)` stay as they are. Cover and page header text come from `--cover` and `--header`

English example (a chapter document; the 가나다 level becomes (a), (b), (c))

```json
{
  "formats": {"chapter": "Chapter {n}. {t}"},
  "letters": {"items": "abcdefghijklmnopqrstuvwxyz", "format": "({x})"},
  "toc": {"title": "Contents"},
  "caption": {"table": {"label": "Table"}, "figure": {"label": "Figure"}},
  "notation": {"source": ["Source", "Note"], "unit": ["Unit"], "table": ["Table"], "figure": ["Figure"],
               "colwidth": ["Column widths"]},
  "language": {"latin": "en-US", "east_asia": "ko-KR", "hwpx_package": "en", "hwpx_style_lcid": 1033}
}
```

- Prints `Chapter 1. Title`, `1.1 Title`, `(a) Title`, the TOC title `Contents`, and captions `<Table 1-1> Title` (SEQ Table) and `[Figure 1-1] Caption`
- Recognizes `<Table> Title`, `[Figure] Caption`, `(Unit: %)`, `Source: `, `Note: `, `(Source)`, and `(Column widths: 20, 30, 50)` together with the Korean tokens

## Review items

- Check that the level symbols are printed and that each level steps in by its indent. ※ is a note on the previous item, so it is left out of the indent step check
- Cross-check the presence of statements under □ with the lint results
- Check that tables are centered, column alignment is consistent, header shading and the unit and source row positions are right, and label column merges neither overlap nor leave gaps
- If automatic merging looks odd, switch to `--merge explicit` and merge only where needed with `^` and `<`. Whether a merge fits differs from table to table, so judge it in the free review
- A long-text cell wrapping to 2 lines is normal. Only a line break that cuts a word in the middle (for example `대한민` and `국` on different lines) counts as a defect
- Check whether the table, caption, and source row are separated across a page boundary. A whole table moving to the next page is normal placement
- Differences in how renderers show numbers computed by automatic numbering and fields (caption numbers, page numbers) do not count as defects. Check the numbers in the XML's automatic numbers and fields
- Check figure size and caption position, and look for clipped or overlapping text
- If a TOC was inserted, confirm that the build check result is a full match, and check the entries, dotted leaders, and page-number alignment on the TOC page PNG. If build prints the `[stranded TOC heading]` WARN, fix the manuscript as it says
- For DOCX, confirm in the structure summary of `check document.docx` that the counts of tables, figures, and footnotes and whether a TOC field exists match the manuscript. The table count includes the one-column tables that hold figures, the footnote count includes footnotes moved from source lines, and the figure count is the number of image files in the document (one for the same file). The paragraph count is a reference value that includes cover, TOC, caption, and spacing paragraphs
- Decide whether a difference found in the page PNGs is a defect with the judgment method in references/renderers.md
- After the item checks, set the list aside and do one free review. Fix at your discretion anything that would look odd to a practitioner receiving the document for the first time, even if no rule covers it
    - (Design and alignment) Left alignment lines between levels, the balance of table and figure widths against the body width, the alignment lines of captions, unit lines, and source lines, consistent spacing, and the distribution of visual weight on a page
    - (Character formatting) The hierarchy of fonts and sizes by level, the consistency of bold and color, uniform fonts inside and outside tables, and leftover unintended formatting
    - (Fix order) If the cause is the manuscript, fix the manuscript. If it is a rule, fix config.py or form.py. Change the typesetting code last. If 3 or more defects of the same kind appear, fix the rule to resolve them all at once
    - (Report) State discretionary fixes in one line of the final report

## Rationale for the rules

- (Symbol levels) Article 2(1) of the Enforcement Rule of the Regulation on the Operation and Innovation of Administrative Affairs (행정업무의 운영 및 혁신에 관한 규정 시행규칙) says items in official documents are marked in the order 1., 가., 1), 가) and may be marked with special symbols such as □, ○, -, ㆍ when needed. The forms use these symbol levels as the report body levels
- (Symbol characters) The level symbols are □ (U+25A1), ○ (U+25CB), - (U+002D), ㆍ (U+318D), and ※ (U+203B). Every weight file of NanumGothic (NAVER and Google releases) and NanumBarunGothic has outlines for them, so the symbols appear whatever the font, weight, or release. □, ○, ㆍ, and ※ share one width within each font (0.94 of the font size in NanumGothic, 0.89 in NanumBarunGothic), so the text start line after the bullet stays the same across levels
- (Cell bullet symbol) Next to 10pt cell text, ○ (diameter 0.75 of the font size) looks large, so cell bullets use ◦ (U+25E6) with a diameter of 0.53. Its advance width equals that of ○, so the text start line stays the same
- (NanumGothic and NanumBarunGothic) Chosen so that Hanja in reports with many Hanja do not print as blanks or in another font. The NAVER releases of both fonts have outlines for all 4,620 KS X 1001 Hanja and the 268 compatibility Hanja in every weight. NanumMyeongjo has no Hanja, and NanumSquare has the Hanja codes with empty glyphs, so neither is used. The flat headings use a different typeface to set them apart from the chapter headings
- (Nanum fonts) They are free fonts under the SIL Open Font License 1.1, so they can be installed without license fees in any Hangul or Word environment and documents open with the same appearance. Both NanumGothic and NanumBarunGothic are offered as safe fonts (안심글꼴) on 공유마당 (Gongu Madang) of the Korea Copyright Commission
- (Table width cap) Using the full available width makes the table's left side stick out past the text start line, so the cap is reduced by the level indent
- (Alignment per column) Deciding per cell splits the alignment within a column among numbers, long text, and short cells, so alignment is decided per column
- (Caption objects and automatic numbers) When a table is moved in Hangul, the caption follows and the number updates. The DOCX number fields serve the same purpose
- (Attached rows inside the table) The unit and source rows are transparent cells inside the table so that they move with the table during manual editing
- (Outer table borders) The left and right outer borders are open to soften the boundary between the text and the table. If outer borders are needed, set EDGE_OPEN_SIDES to False
- (Code-generated forms) The references among styles, fonts, bullets, and outline numbering are created from one definition (form.py), which prevents missing references. If even one bullet definition reference is missing, Hangul omits the symbol, and checking the body text does not reveal such a gap
- (Manuscript parsing module) Manuscript parsing and the table and figure calculations live in one module, manuscript.py. The HWPX and DOCX typesetters use the same merge, alignment, and width calculations, so a rule change happens in one place
- (TOC page number recheck) The recheck catches cases where filling in the page numbers changes the TOC or body layout
- (DOCX language tag) With the Latin language set to ko-KR, LibreOffice breaks lines inside numbers such as `3,456,789`
- (DOCX TOC bookmarks) With a TOC that only had prefilled result text, updating the fields in Word reset every page number to 1. Using the same structure as a Word-made TOC lets Word recalculate the page numbers from the heading positions whichever update option is chosen
