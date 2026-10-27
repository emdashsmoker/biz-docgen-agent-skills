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
- Polite headlines end in the formal 하십시오체 style (e.g. "수립합니다", "확보합니다")
- Body style is noun-ending regardless of the headline style
- Headlines and body text use no colloquial style
- Colloquial markers are hedged and softened endings (-듯, -듯함, -인 셈, -하는 편, -할 만함, -로 봄, -로 보임, -로 여겨짐), explanatory endings (-는데, -인데, -더라, -거든, -잖아), spoken contractions (-하는 게, -할 거, -한 걸, -하는 건), colloquial adverbs (일단, 약간, 좀, 꽤, 딱, 그냥, 나름) and similar forms
- Delete colloquial markers or replace them with formal expressions
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
- Write the Point band only for judgment criteria, formulas, follow-up links, selection reasons, timing or principles that are not in the headline or body
- Delete a band that only repeats the headline or summarizes the body
- Put one-line formulas or caveats in `footnotes`

## Notation

- Space long names word by word (a word wider than the inner box width is cut in the middle)
- Two listed nouns are joined with "및" in labels, headlines and body text alike (e.g. 전략과제 및 세부과제)
    + (Exception) RFP original names (engagement names, output names, stage names, subject names) keep the original wording
    + (Exception) Established names in a field keep their customary wording (e.g. the BSC perspective name "학습과 성장")
    + (Exception) "와" and "과" marking a relation between two nouns (사이, 간, 격차, 차이, 일치, 불일치) stay (e.g. 현행과 기준의 격차)
    + (Exception) "와" and "과" marking the partner of an action stay (e.g. 발주기관과 공유, 사유와 함께 관리, 지역 대학과 공동 운영)
- Write section numbers as a number and a period (e.g. "1.")
- The builder corrects the period of section numbers automatically
- Write numbers and symbols once
- Leave out of the text the numbers and symbols the builder adds
    + Write section without the secNo number ("1.")
    + Write slot text without symbols such as "-" or "·" (the builder typesets bullets)
    + Write steps titles without prefixes such as "STEP 1." (set stepLabel to "" if no prefix is needed)
    + A grid cell that carries inherited numbering (1-1.) sets numbered so the number replaces the bullet
    + Write process module names without numbers such as "M1" (the module number goes in the id field)
    + On slides with a marker, start the first body line with content different from the marker
- The symbol repetition rule targets symbols typed directly (bullets drawn by the builder stay)
- Keep bullets when there are 2 or more items
- A single item is written as a sentence without a bullet, even when it wraps onto several lines
- Items in the same tier are consistent in having or not having numbers and symbols
- Join several sources on one line with semicolons (a `source` array is joined automatically)
- Quote document titles and material names in sources (`source`, `factSource`) as in the original (replace only em dashes and en dashes with hyphens)
- Notes and sources start with ※ (the build attaches it automatically to source and note-type slots, and notes written directly in body cells get it by hand)
- Use ※ only for evidence, sources, premises and caveats
- Put evidence and caveats in note slots or footnotes to use the automatic ※
- ※ paragraphs in sample slides are example positions
    + Used as a note, start it with ※
    + Used as a normal item, write it without ※
- Shortened body sentences, item descriptions and labels have no ※ and use the font size of their tier
- All bullets in one box use the same font size
- The subject term rules follow the subject term section of `references/headline-patterns.md`
- Module section titles use the `[Module 1] 모듈명` format (to avoid clashing with the period after the section number)
- Task markers use the `Task 2. Task명` format
- Module items in organization charts and the table of contents also use the `[Module 1] 모듈명` format

## Tables

- When a cell has two or more items, look at the cell content and the whole table and choose whichever reads more easily: bullets or a comma list
- The default is a comma list for short noun phrases and bullets for descriptive items
- Decide whether a column uses one notation by comparing the nature of its cells
- Horizontal alignment is set per column
- Number columns are right-aligned so digits compare easily
- Columns with multi-item cells and diagnostic question columns are left-aligned
- Other columns with only single-item cells are centered
- The cells of a column are all single-item or all multi-item
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
