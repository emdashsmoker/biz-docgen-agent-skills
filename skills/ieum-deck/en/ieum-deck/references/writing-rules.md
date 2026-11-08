# Text norms

- The rules below target Korean deck text, and the quoted words are the Korean patterns lint checks

## Sentences

- One message per sentence
- Each 5W1H element appears once in a sentence
- Resolve connectives (그리고, 그러나, 하며, 이는) and compound sentences by splitting sentences
- Use commas for lists of items
- Write list commas without omission
- Body text uses noun endings
- Correct a remaining adnominal form ("달성할 필요") to a noun phrase ("달성 필요")
- A form with the predicate cut off ("수립하는 것을 목적") is a grammar error
- Rewrite a sentence with the predicate cut off in the "수립을 목적으로 추진" form (noun-ending conversion rules in `references/headline-patterns.md`)
- The headline style is chosen in kickoff question 5 (noun style by default, polite style optional)
- Polite headlines end in the formal 하십시오체 style (e.g. "수립합니다", "확보합니다", "보유하고 있습니다", "추진하겠습니다" and similar forms)
- Body style is noun-ending regardless of the headline style
- Headlines and body text use no colloquial or informal style (including a colloquial or informal tone in endings, words, expressions and similar elements)
- Colloquial markers are hedged and softened endings (-듯, -듯함, -인 셈, -하는 편, -할 만함, -로 봄, -로 보임, -로 여겨짐), explanatory endings (-는데, -인데, -더라, -거든, -잖아), spoken contractions (-하는 게, -할 거, -한 걸, -하는 건), colloquial adverbs (일단, 약간, 좀, 꽤, 딱, 그냥, 나름) and similar forms
- Delete colloquial markers or replace them with formal expressions
- Name the referent with a concrete noun instead of a placeholder noun (것, 곳, 거, 셈, 부분 and similar nouns)
- Headline limits are 50 characters for 1 line and 100 for 2 lines (over 50 is a lint WARN, over 100 is a lint FAIL)
- The 1-line limit is 43 characters on the A4 page size, 40 on 10.83×7.5 and 37 on 4:3 (the 2-line limit is double the 1-line limit)
- Character limits count Hangul-equivalent characters (text width divided by the width of one Hangul syllable; Latin letters and spaces count less, by their width)
- Write headlines as conclusion sentences (lint WARNs a topic label of 2-12 characters with no space, such as "추진배경")

## lint FAIL expressions

- Em dashes and en dashes
- Contrast constructions ("X가 아닌 Y")
- Number declarations (a number with "대" followed by 전략, 방안, 과제, 축, 원칙, 목표 or 영역. e.g. "3대 전략")
    + (Exception) Counts set by the RFP are excluded from the number declaration check with the slide's `allowCount` field
- Empty filler expressions (이러한 맥락에서, 시사하는 바가 큼, 주지하다시피, 말할 것도 없이)
- Exaggerating modifiers (획기적, 혁신적인, 압도적, 매우, 탁월한)
- Meta narration (본 절에서는, 앞서 제시한, 앞에서 살펴본, 다음 슬라이드에서)
- Internal evaluation vocabulary (배점, 채점, 방어 논리, 결정 장소, 귀속)
- Coverage declarations ("누락 없이 반영", "빠짐없이 반영")
- Connectives (그리고, 그러나, 하지만, 그러므로, 그렇기 때문에, 이는)
- Noun forms with the predicate cut off ("수립하는 것을 목적")
- Polite endings in body text (합니다, 입니다, 됩니다, 습니다, 십시오)
- Headline endings that differ from the chosen headline style
- Unreplaced pattern slots (`{{ }}`)
- Variants of RFP key wording (engagement names, output names, stage names, subject names) (when registered in `meta.rfp.wording`)

## Expressions checked in review

- Expressions lint does not check are checked in the in-depth review and visual review
    + Self-posed questions answered by the writer
    + Exposed framework names (MECE, pyramid)
    + The subject term repeated in every section ("본 과업은")
    + Sentences implying shortcomings in the contracting agency's policies or RFP (turn them into positive statements)
    + Colloquial markers (correct them by the list in the Sentences section)
    + Two nouns joined with "와" or "과" (change to "및")

## lint WARN vocabulary

- 맥락, 패러다임, 인사이트, 함의, 축, 층위, 정립, 선제, 선점, 게이트, 매핑, 컨틴전시, 딥다이브
- The check targets these words when no other Hangul is attached before or after them

## Content composition

- Use a single dimension as the classification criterion
- Classification items are mutually exclusive and collectively exhaustive
- 3-4 items per tier are recommended
- Group items when there are more than 5
- One message per slide
- 3-4 or fewer components support the message
- Resolve department-store listing by splitting slides
- The message of a Task bundle slide is one module-level sentence
- On a Task bundle slide, Tasks are components of the message
- Items in boxes and table cells hold 1 item per line
- If an item runs to 2 lines, cut characters
- On overflow, cut characters and items (the font size stays)
- When a box is large, check how specific each item is before adding items
- A lead in background and purpose consists of a one-sentence title and 2-3 evidence items
- If a box has only 1-2 items, add items to reach a 70% fill ratio
- Write bullet item text at 80-95% of one line of the box width (if the longest line is under 80%, every line looks empty on the right)
- Write synthesis box item text at similar lengths filling 90-100% of one line (the judgment criterion is horizontal fill in the SKILL.md design system)
- Table cell text carries whichever of subject, criterion and figures is needed (enough to fill the column width)
- If there is nothing to add, shrink the box and gather it to the center
- If it still looks awkward after shrinking, change the form of expression or merge it with a neighboring box
- Write the Key Point band only for judgment criteria, formulas, follow-up links, selection reasons, timing, principles or similar content that is not in the headline or body
- Delete a band that only repeats the headline or summarizes the body
- Put one-line formulas or caveats in `footnotes`

## Notation

- Space long names word by word (a word wider than the inner box width is cut in the middle)
- Two listed nouns are joined with "및" in labels, headlines and body text alike (e.g. 전략과제 및 세부과제)
    + (Exception) RFP original names (engagement names, output names, stage names, subject names) keep the original wording
    + (Exception) Established names in a field keep their customary wording (e.g. the BSC perspective name "학습과 성장")
    + (Exception) "와" and "과" marking a relation between two nouns (사이, 간, 격차, 차이, 일치, 불일치, 연계, 연동, 정렬, 비교, 구분, 분리, 협력) stay (e.g. 현행과 기준의 격차, 성과지표와 성과목표의 연계)
    + (Exception) "와" and "과" marking the partner of an action stay (e.g. 발주기관과 공유, 사유와 함께 관리, 지역 대학과 공동 운영)
- Write section numbers as a number and a period (e.g. "1.")
- The builder corrects the period of section numbers automatically
- Write numbers and symbols once
- Leave out of the text the numbers and symbols the builder adds
    + Write section without the secNo number ("1.")
    + Write slot text without symbols such as "-" or "·" (the builder typesets bullets)
    + Write steps titles without prefixes such as "STEP 1." (set stepLabel to "" if no prefix is needed)
    + A grid cell that carries inherited numbering (1-1.) sets numbered so the number replaces the bullet
    + Write note and footnotes items without ※ or a mark such as "1)" or "Note:" (the mark comes from `meta.footnoteStyle` and the label text from the slide footnoteLabel and sourceLabel or `meta.labels.common`; the source mark of an item that cites a source follows the source mark rule below)
    + Write process module names without numbers such as "M1" (the module number goes in the id field)
    + On slides with a marker, start the first body line with content different from the marker
- The symbol repetition rule targets symbols typed directly (bullets drawn by the builder stay)
- Keep bullets when there are 2 or more items
- An item with sub items (sub) counts as a list even when it is the only one (it keeps its bullet like 2 or more items)
- A single item is written as a sentence without a bullet, even when it wraps onto several lines
    + (Table cells) Lines that receive bullets by the comparison line condition or the whole table condition in the tables section below are an exception
    + (Module overview slides) The process, data used and deliverables boxes are an exception and take bullets (treated as a table where both conditions always hold)
- Items in the same tier are consistent in having or not having numbers and symbols
- Write each source item as `기관명(연도), 자료명` (organization (year), material name)
- Separate several sources with semicolons (the build joins a `source` array)
    + The build joins a source line that fits one line and sets one source per line when it does not (the semicolon stays at the line end)
    + In the line-broken form, the second source onward aligns with the start of the first source (after the source label in a number-style deck; after the width of ※ and the source mark, as in "※ Source:", in a ※ mark deck)
    + Sources get no numbers (a source number signals numbered citations in the body)
- Quote document titles and material names in sources (`source`, `factSource`) as in the original (replace only em dashes and en dashes with hyphens)
- Notes and sources start with the `meta.footnoteStyle` mark
    + The build adds the ※, the number and the number-style label to note-type slots, footnotes and source
    + Notes written directly in body cells get ※ by hand
    + In a number-style deck, the build turns a ※ added by hand into the deck mark
    + (Notes with two or more items in a number-style deck) The note label goes on the first line only and 1) 2) tell the items apart. Items from 2) onward align with the start of 1)
    + The build removes a ※, * or number written before an item and adds the deck mark (superscript numbers or * marks paired with spots in the body are not supported)
- Start the first source item and any note item that cites a source with a source mark (e.g. "Source:", "출처:", "자료:")
    + (※ mark deck) The build adds only ※, so the source mark you write is typeset as is (e.g. "※ Source: organization (year), material name; organization (year), material name")
    + (Number-style deck) The build replaces the source mark of the source line and of a single-item note with sourceLabel
    + (source array) Write the source mark on the first item only (the build separates the items with semicolons)
- Use ※ only for note text such as evidence, sources, premises and caveats
- Put evidence, caveats and similar content in note slots or footnotes (the build adds the mark)
- ※ paragraphs in sample slides are example positions
    + Used as a note, start it with ※
    + Used as a normal item, write it without ※
- Shortened body sentences, item descriptions and labels have no ※ and use the font size of their tier
- All bullets in one box use the same font size
- The subject term rules follow the subject term section of `references/headline-patterns.md`
- Module section titles use the `[Module 1] 모듈명` format (to avoid clashing with the period after the section number)
- Task markers use the `Task 2. Task명` format
- Module items in organization charts and the table of contents also use the `[Module 1] 모듈명` format

## Notes

- Notes (footnotes, note slots) carry the supplementary information readers need to read or check the body correctly (example targets: figures, terms, judgments, scope and similar parts)
    + (Figures) Calculation basis such as formula, unit, reference date or conversion basis
    + (Terms) Definitions of terms, abbreviations, symbols and similar items unfamiliar to readers
    + (Judgments) Grounds such as the governing law or a higher-level guideline
    + (Scope) Conditions under which the content holds, such as assumptions, scope, exceptions, or whether figures are examples or provisional
- Write content that forms the body message in the body
- Write the material that figures, facts and similar content come from in `source`
- Write each note item as a simple sentence with one subject-predicate pair (judge a simple sentence by its structure regardless of length)
- Merge caveats on the same target into one item
- A note that supplements a specific word, figure or similar item names that item in its sentence (e.g. "Revenue is based on the 2024 settled accounts")
- Omit the definition note and the full name for terms and abbreviations readers use at work or in daily life (RFP, consulting, participation rate and so on)
- Write a note that defines a term, abbreviation or symbol as `(term) explanation` (the term in parentheses names the target)
    + Write the term in parentheses exactly as the body writes it
    + Write the explanation as one noun phrase that spells out the meaning (e.g. "(Location quotient) Share of an industry in a region divided by the share of the same industry nationwide")
    + Do not repeat the defined term or use other technical terms in the explanation
    + For an abbreviation, add the full name in parentheses at the end of the explanation. When the full name already gives the meaning, write the full name alone (e.g. "(TTL) Travel, transport, and logistics")
- Compose note items without duplication or omission
- Do not repeat in a note what the headline, body, Key Point band or similar parts already say
- Keep the number of notes per slide to the minimum the body needs
    + (※ mark) Write one item by default. Use two or more items when caveats on different targets are needed together (stacked ※ lines stand out more than the body)
    + (Numbers) Apply the same minimum as the ※ mark (with two or more items the build numbers them and sets one item per line)
    + (Judgment per slide) These counts are common practice, so do not apply them mechanically to every slide. Make the final judgment from the content and context of the slide
- Run-on is set with `footnoteInline: true` on the slide (the build never switches the line-broken form to run-on by itself)
- Set run-on only on a slide that still meets every condition below after the minimum note count and the source citation rules are applied
    + (Body fit) On the slide built in the line-broken form, the body overflows or overlaps (confirm with a check_layout FAIL or the PNG)
    + (Line saving) Running on removes two or more lines from the bottom notes and source line together (confirm with the build; do not set it when short items keep the same line count)
- Run-on layout
    + (Notes of a number-style deck) "Note: 1) A 2) B 3) C" runs on in one paragraph
    + (Source line) "Source: A; B; C" or "※ Source: A; B; C" runs on in one paragraph
    + (Notes of a ※ mark deck) No run-on; each line keeps its ※
    + A run-on paragraph that passes the line end aligns its second line onward after the label
- Keep run-on slides an exception across the deck (when several slides meet the conditions, review the amount of notes and sources in the deck)

## Tables

- When a cell has two or more items, look at the cell content and the whole table and choose whichever reads more easily: bullets or a comma list
- The default is a comma list for short noun phrases and bullets for descriptive items
- A comparison line is a line of cells that sets the same attribute side by side across subjects. In a table with subjects in columns (module overview table, alternative comparison table), rows are the comparison lines. In a table with subjects in rows (track record table, etc.), columns are
- Decide whether a comparison line uses one notation by comparing the nature of its cells
- A cell written with bullets takes a bullet per item. A single item takes no bullet, even when it wraps onto several lines
- Bullets on single-item cells are judged per comparison line
    + (Comparison line condition) When half or more of the cells in a comparison line hold two or more items, every single-item cell in that line also takes a bullet. Header rows and label columns are not counted
    + (Whole table condition) When most list-type lines of a table carry bullets, the remaining list-type lines may also take bullets as whole lines. Judge by how the whole table reads. A list-type line is one whose cells can hold several items (lines with one value per cell, such as amounts, periods and years, are excluded)
    + (Line-level application) Added bullets apply to a whole line. Within a line that receives added bullets, do not mix cells with and without bullets
    + (Context judgment) The conditions above do not fit every table mechanically. Make the final call from the context of the whole table
    + (Module overview table) Treated as a table where both conditions always hold, so all three rows take bullets (applied by the builder)
- Judge the lines that receive added bullets at the storyboard stage and give them with `bulletRows` and `bulletCols` (format in `references/templates.md` table typesetting)
- Horizontal alignment is set per column
- Column alignment is judged from the whole table by the role the column plays in it
    + (Quantity columns) Columns of numbers and units (amounts, counts, ratios, scores, weights, etc.) are right-aligned so digits compare easily
    + (Columns read as one expression) Columns whose cells each read as one expression (categories, names, years, serial numbers, periods, formulas, short text, etc.) are centered
    + (Columns read line by line) Bullet lists, diagnostic questions and descriptive text (content, details and main activities columns, etc.) are left-aligned
- A quantity with a share or change added in parentheses (○○ cases (○○%), etc.) makes a quantity column
- An expression that mixes numbers with words for a condition, a point in time or an order (○○ points or more, ○○% (2030), year 4, stage 3, etc.) makes a column read as one expression even though it contains numbers
- Columns of the same nature use the same alignment in every table of a deck
- A column that is hard to judge is centered
- The cells of a comparison line are all single-item or all multi-item (when the item counts are hard to match, bullets in that line follow the comparison line condition above)
- Vertical alignment is centered for the whole table
- Cell fills use only the theme color, tint, gray and white
- Set white even on cells without a fill
- With many rows, split the table or reduce the row height so it ends within the body area
- Merge cells repeating the same value only when the higher category actually continues
- Decide on merging by the meaning of the table and the relation of neighboring rows

## Figures

- Quantitative figures carry the source organization and reference date
- Check totals and ratios with code
- Mark unconfirmed figures with the placeholder `[확인 필요]` (lint WARN if left, FAIL with `meta.final`)
