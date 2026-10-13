# Deck Conversion Path

- The path that turns a proposal presentation deck (pptx, pdf) into an hwpx qualitative technical proposal. The deck is treated the same way as an RFP
    + The scripts only convert formats. The model that read the full source text does the extraction and judgment
    + The procedure is parsing, source reading, transfer to the proposal strategy file and storyline, comparison with the RFP, and manuscript writing. The steps, writing norms, checks, and typesetting of the general path apply as is
- A deck is an argument-centered document. The proposal's composition units (❍, evidence lines, tables) are added at the manuscript writing stage. A manuscript that only copies slide sentences into the hierarchy fails `check volume` and `check density`

## Parsing

```bash
python3 <SKILL>/scripts/proposal.py init workspace
python3 <SKILL>/scripts/proposal.py rfp RFP_file workspace      # submitting the RFP with the deck is recommended. Without it, see the RFP Comparison section
python3 <SKILL>/scripts/proposal.py deck deck_file workspace
```

- There is one processing path, PDF. pptx is converted to PDF in LibreOffice first. Extraction of body text and tables, extraction of embedded images, and diagram capture all run on that PDF
- The output goes to `발표자료/` in the workspace. 원문.md (body text and tables per page), sheets/ (page thumbnail sheets), pages/ (page PNGs), img/ (embedded images), 발표자료.pdf (reference copy)
- If both pptx and pdf are received, use the pptx as input. The pptx conversion keeps the spacing of the body text. Keep the PDF saved from PowerPoint as a backup source for diagram capture
- Handling stdout warnings

| Warning | Meaning | Handling |
|---|---|---|
| Incomplete text layer, stop | A PDF that went through size compression or re-saving. Body text is extracted as different syllables | Stop the work and pass the warning text to the user. Request the pptx original or the PDF before compression |
| Pages missing spaces | Pages missing only spaces (characters are intact) | Restore spacing when transferring |
| Empty pages | Pages with only formatting and no content. The material is still being written | Confirm the page numbers together in the kickoff questions |
| Fonts missing in this environment | Converted with substitute fonts. Unrelated to body extraction | Check only for text overflow in the diagram capture results |

- The conditions for using `--allow-garbled` are the user's answer that they do not have the original and their agreement to proceed by reading page PNGs. In that case the reference material is the page PNGs and 원문.md is auxiliary. OCR has low quality on slide layouts. Do not use it

## Source Reading

- Read the full text of 발표자료/원문.md the same way as 01_RFP원문.md. For diagram-heavy material, check the thumbnail sheets in sheets/ as well
- Open page PNGs only for the pages needed. The targets are diagram candidates, pages with broken sentences, pages with broken tables, and pages marked `이미지 쪽` (image page; may be a content page with a table pasted as an image)
- The estimated page types in 원문.md are reference values. Headers, footers, and page numbers have been removed

## Transfer

- For kickoff question items that the deck confirms (consortium, staff, advisory committee), present the values and get only confirmation. Ask at the same time whether anything changed after the deck was written
- Transfer the content of the proposal strategy file, the module overview table, and the storyline from the deck. The range to write anew is the fields absent from the deck

| Deck element | Transfer target |
|---|---|
| Headline sentence at the top of a page | Point judgment statements in 02_스토리라인.md (converted to nominal endings) |
| Background, implementation strategy, and features and strengths pages | Client needs, proposal strategy, and differentiation points in 00_제안전략서.md, and the matching tables of the storyline |
| Execution process diagram, tables of detailed activities and work products per module | 02_모듈총괄표.md (names kept, numbering unified as Module and Task) |
| Pages on proposer status, track record, staff, advisory candidates, schedule, reporting, and security | 회사자료.md and common part substitution values |
| Pages marked as examples or drafts | The filled table of the relevant Task |

- For fields absent from the deck (underlying-need hypotheses, key wording dictionary, some Background stages), mark the model's draft entries with `[보강]` (supplemented). Point them out as confirmation items in the step 2 approval request. Remove the marker after approval
- Do not transfer cover, table of contents, divider, and closing pages. If other content pages are left out, report their page numbers and reasons in one line in the step 2 approval request

## RFP Comparison

- RFP dissection (step 1) is done from the RFP source text, as on the general path. The deck's requirement response pages are reference material for the placement section column
- The RFP's specified table of contents takes priority for chapter structure. Compare the deck's Modules and Tasks with the requirement table. If requirement items are missing, add Tasks. `check rfp` judges this
- If terms in the deck's sentences differ from the RFP wording, unify them to the RFP notation
- Submitting the RFP along with the deck is recommended. Adding missing requirement items, allocating volume by points, and comparing wording are possible only with the RFP. Without the RFP, recommend submitting it once within the kickoff questions. After that, follow the user's decision
- When proceeding without the RFP
    + Place empty tables with `rfp 발표자료/원문.md workspace` (01_RFP원문.md then holds the deck's body text)
    + Transfer 01_요구항목표.md from the deck's engagement scope pages, requirement response pages, and detailed activities per module. Write `발표자료 기준` (per the deck) in the remarks column
    + Transfer 01_배점표.md from the evaluation items shown in the deck. For items with unknown points, enter 0 in the points column (empty cells are excluded from the tally). Attributed points become 0. For the in-depth review intensity, treat the execution part and argument sections as 10 points or more
    + Write the key wording dictionary from the deck's engagement name, detailed task names, and work product names
    + Chapter structure follows the deck's table of contents. If the user submits the RFP later, redo from step 1
    + Record in one line in the final report the limitation that the requirement omission check, the point weight judgment, and the RFP wording comparison could not be done

## Manuscript Writing

- Headlines become the approved □ judgment statements, and bullets become the gist of ❍ claims. Add evidence lines and tables from other deck pages, the RFP, 회사자료.md, literature the user submitted, and web search (if allowed), in that order
- Rebuild deck tables as tables. Rebuild schedules by the schedule chart norms and organization charts as the participating staff table and the division of duties table
- Convert the deck's customary expressions to manuscript norms. The targets are honorific endings, count declarations, arrow and slash links, lists of methodology names, contrast diagrams, adjective strengths, and symbol bullets. `check tone` judges them
- Transfer figures from the deck after checking their sources. Handle effect figures without sources and hypothetical values in example tables with one of: replacing them with confirmed values, adding a draft note, or marking `[확인]` and asking at step 5
- Compare the proposer's own figures (years in business, track record, staff) with 회사자료.md. If values differ, ask the user

## Figure Selection

- Figures come from embedded images and page captures. Photos, logos, maps, and chart images are embedded images that `deck` extracted (`발표자료/img/` and manifest.json). Diagrams drawn with shapes and text boxes are page captures (`figure`)
- Apply the selection criteria and user confirmation procedure of the SKILL.md Reusing Source Images section as is. The model writes a candidate list (file or page, type, insertion point, draft caption) based on the manifest and thumbnail sheets. This list is included in the step 2 approval request. Insert only the items the user adopts
- If the same figure exists as both an embedded image and a page capture, prefer the embedded image, which keeps the original resolution. If the embedded image is split into pieces, use the page capture

### Diagram Capture

```bash
python3 <SKILL>/scripts/proposal.py figure workspace page --grid
python3 <SKILL>/scripts/proposal.py figure workspace page --crop left,top,right,bottom --name name
```

- Diagrams drawn with shapes and text boxes are not extracted as embedded images. Capture the region of the reference PDF
- Figure candidates are diagrams whose core is relations and flow (process diagrams, structure diagrams, concept diagrams), charts, maps, and photos. Rebuild simple list diagrams and collections of other organizations' logos as tables
- `--crop` values are percentages of the page size. A whole-page capture includes the slide title bar and footer. Specify only the diagram region. Read the values from the grid PNG that `--grid` creates
- Before inserting, check the capture for cut shapes, leftover headlines, and text overflow. If text overflows in the pptx conversion, capture the same page from the PDF saved by PowerPoint (`--pdf path`)
- Insert as `![caption](../발표자료/figures/file_name.png)`. Place one ❍ holding the gist of the diagram before it. If `WARN: image not found` appears in the build stdout, the path is wrong
- Sentences inside a diagram are outside the verdict of `check wording`. Include key wording in the ❍ text as well
- For diagrams with small text, check legibility in the rendered PNG. If it is hard to read, rebuild it as a table or capture it as two regions

## Failure Patterns

- (Slide transcription) Only slide sentences copied into the hierarchy. Manuscripts with empty composition units fail the volume and density verdicts. Add evidence lines and tables
- (Diagram overuse) Inserting whole pages. Pages that should be rebuilt as tables inserted as figures too. Insert only diagrams the user adopted. Capture only the diagram region with `--crop`
- (Forcing a compressed PDF) Proceeding with `--allow-garbled` without user confirmation on a PDF whose body text extracts as different syllables. Pass the stop message and request the original
- (Treating example figures as final) Using hypothetical values from example pages and figures without sources as grounds in the body. Replace them with confirmed values, or convert them with a draft note or a `[확인]` mark
- (Deck structure first) Using a deck chapter structure that differs from the RFP's specified table of contents as is. Apply the RFP's specified table of contents first
