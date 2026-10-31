---
name: "juja-builder"
description: "Writes Korean technical proposals for research and policy service contracts, from an RFP to hwpx and docx files. The same methods write RFP-based pre-diagnosis reports (planning, feasibility, performance analysis, surveys) and planning reports (plans, event plans, initiative cards, issue reports, briefings, guidelines). Excludes SI, national R&D plans, and grant plans. Converts proposal decks (pptx, pdf) to hwpx. Use when the user mentions a proposal, RFP, bid, tender, 제안서, 제안요청서, hwpx or Word proposal, deck to proposal, pre-diagnosis report, planning report, initiative card, issue report, briefing, or guideline, or attaches an RFP or deck. Translated from the Korean edition and may not perform as intended. Korean labels by default. References: references/methods.md, content-models.md, lexicon.md, deck-conversion.md, report.md, planning.md. Templates: assets/strategy.md, storyline.md, company.md, diagnosis.md, report-storyline.md, plan-design.md, assets/common/overview.md, organization.md, management.md."
license: AGPL-3.0-or-later with an output exception. Terms in LICENSE and NOTICE.md
---

# juja-builder

- (Translated edition) This English edition is translated from the Korean original. Its instructions may not deliver the performance intended in the Korean edition
- (Korean public procurement) The proposal path is built on the Korean public procurement system. It assumes an RFP from a Korean public institution, a contract by negotiation (협상에 의한 계약), and evaluation of qualitative technical proposals against a scoring table
- (Free-form planning) For work outside Korean public tenders, the feature you most likely want is free-form planning. It is the planning report path, which writes a document without an RFP, starting from a topic and materials you set (`init workspace --kind plan`, references/planning.md)
- (Name) Taken from 주자소(鑄字所), the type-casting office of the Joseon dynasty. 주자(鑄字, type casting) became juja and 소(所, office) became builder
- (Purpose) Write proposals in which evaluators find the answer to each detailed evaluation item directly in the manuscript
- (Goal) Produce hwpx and docx delivered files that pass the code checks and the render review
- (Scope) Qualitative technical proposals (정성제안서) submitted to tenders for research, planning, and operation service contracts
    + (Target engagements) Strategic planning and master plan development, informatization planning (mandatory ISP, intelligent information society plans, the client's own IT planning), business planning (R&D, non-R&D), performance analysis and evaluation response (R&D, non-R&D), policy research and survey analysis (status surveys, trend surveys, demand surveys, institutional improvement, initiative discovery), management evaluation response, support program operation. Identification signals for each type are in the Module Frameworks by Engagement Type section
    + (Excluded) System integration projects (SI), R&D plans for national R&D projects (국가연구개발과제 연구개발계획서), business plans for open-call programs (공모사업 사업계획서)
    + (Informatization boundary) Informatization planning whose final result is a plan (ISP and similar) is in scope. Build projects whose final result is a system are excluded. The criterion is the form of the final result. Whether the project legally counts as a software project is outside the criterion
    + (Excluded input) If the RFP is out of scope, tell the user so before the kickoff questions
    + (Additional outputs) Pre-diagnosis reports (사전진단보고서) and planning reports (기획보고서). Identification and procedure are in the Output Types section
- (Language) Manuscripts, design-file content, and delivered files are written in Korean by default. Replies to the user follow the user's language
    + The default document labels (table of contents title, captions, 가나다 letters, chapter labels, delivered file names) are Korean. A label file (`build --labels`, references/labels.md) switches them for documents in another language. Korean manuscript notation (`출처:`, `<표>`, `(단위: )`) stays accepted
    + For manuscripts not written in Korean, skip the Korean-specific checks with `check all --skip` (Checks section)
    + Korean strings in backticks, Korean file and folder names, Korean headings and column names of design files, and Korean markers are anchors that the scripts parse or that appear in deliverables. Keep them verbatim
    + An English gloss in parentheses follows a Korean anchor on first use. The gloss is for the reader and is never written into files
- The default input is one RFP. If a proposal presentation deck (pptx, pdf) is in the input, apply the deck conversion path (Procedure section)
- The output files of a proposal are the proposal strategy file, requirement table, scoring table, section ledger, module overview table, storyline, section manuscripts, check log, and the hwpx or docx delivered file
- Every file this skill creates goes into the workspace. What a chat reply contains is set in the Chat Replies section
- The script is `<SKILL>/scripts/proposal.py`. Call it as `python3 <SKILL>/scripts/proposal.py command arguments`. `<SKILL>` is the folder that holds SKILL.md
- The typesetting code is `hwpx_report.py` (the format-agnostic typesetting layer such as the manuscript parser and table layout calculation, plus the hwpx writer) and `docx_report.py` (the docx writer) in the same folder. Do not modify the typesetting norms of these two files (the permitted scope is editing API call sites, as in the Preparation section)
- Reference files are in the `<SKILL>/references` folder. When and how much to read is in the table below

| File | Contents | When and what to read |
|------|----------|-----------------------|
| methods.md | Module frameworks by engagement type, purposes of Modules and Tasks, label sets by Task type, committee design, opinion-gathering tools | At step 2: the opening, the Common Standards section, and the section for the engagement type (all matching types for a composite engagement). For an engagement that matches no identification signal, read the opening first at step 0 |
| content-models.md | Content models by section, volume units, line-limit table | At step 2: the Volume Units section (including the line-limit table) and the Background, Implementation Strategy, and Features and Strengths sections. At step 3: the section for the file being written |
| lexicon.md | Conventional vocabulary, replacement table, sentence-ending vocabulary | All of it when step 3 starts |
| deck-conversion.md | Parsing, source reading, transfer, RFP comparison, figure selection, and diagram capture for the deck conversion path | All of it before step 0 when a proposal deck (pptx, pdf) is in the input |
| report.md | Procedure, diagnosis design, RFP-first principle, table of contents derivation and TOC examples, storyline finalization, source research, manuscript writing, check targets, and typesetting options for the pre-diagnosis report | All of it right after `init` when the output type is the pre-diagnosis report |
| planning.md | Design streams, planning type examples, short-form examples, initiative card format, procedure, planning design, check targets, and typesetting options for the planning report | All of it right after `init` when the output type is the planning report |
| labels.md | How to supply document labels, the key table with defaults, an English example, and how to proceed with manuscripts in another language | All of it before the first check when the document language in the kickoff answers is not Korean |

## Output Types

| Type | Identification signals | init | Procedure source | Numbering |
|------|------------------------|------|------------------|-----------|
| Proposal (default) | proposal, qualitative technical proposal, tender, request for proposal (제안서, 정성제안서, 입찰, 제안요청서) | `init workspace` | SKILL.md Procedure section | Ⅰ. 1. 가. 1), unnumbered captions |
| Pre-diagnosis report | pre-diagnosis report, report from an RFP, research report draft (strategic planning, business planning, feasibility study, performance analysis, R&D performance evaluation, informatization planning, demand survey, trend analysis, and similar), diagnosis before kickoff | `init workspace --kind report` | references/report.md | 제1장 1.1 1.1.1 가., numbered captions per chapter, list of tables and list of figures, divider pages |
| Planning report | planning report, free-form planning, plan draft, implementation plan (추진계획(안)), event plan, initiative card, summary report, issue report, briefing material, guideline, manual, and similar | `init workspace --kind plan` | references/planning.md | Same hierarchy as the proposal, document title |

- (Purpose by type) Readers do different things with each of the three types
    + (Proposal) In a contract by negotiation, evaluators compare proposers' understanding of the client's situation and their capacity to perform, and pick the contractor
    + (Pre-diagnosis report) In the diagnosis stage before kickoff, the client's staff check the current state, gaps, and direction (draft), and use the document for advance consultation and internal reporting. It follows the structure of a final report, so it doubles as a draft that previews the final deliverable
    + (Planning report) Starting from the needs of the people who will use the result, it decides what to do and how before execution. Short forms such as issue reports and guidelines deliver the inputs to a planning judgment or its results
- If the request wording does not settle the type, confirm it in the kickoff questions
- The output type is recorded in state.json. build and check all run with the recorded type
- All three types apply Usage Notice, Chat Replies, Preparation, the hierarchy and sentence discipline of Writing Norms, Typesetting, and Render Review. Which SKILL.md sections the pre-diagnosis report and the planning report follow or skip is set by the scope table in each reference file
- The output format is set by the answer to the kickoff questions. The recommendation is one of hwpx or docx. `build --format hwpx|docx|both`
    + (Reason for one format) Producing both formats repeats the render review and defect fixes for each format. The repetition consumes context and lowers the quality of writing and review in later steps
    + (If both are chosen) If the user picks both in the kickoff questions, state the reason above in one line in the next reply. If the user keeps the choice, proceed with `--format both`

## Usage Notice

- When starting in a new workspace without state.json, show the notice below once, word for word, at the very top of the first reply. Then continue with the start sequence as is

> **juja-builder usage notice**
> - (Translated edition) This English edition is translated from the Korean original. Its instructions may not deliver the performance intended in the Korean edition. Manuscripts and delivered files are written in Korean by default
> - Documents made by this skill are drafts that assume review and revision by the user
> - (Before starting) A high-volume task that handles the full text of the RFP or input materials and the whole manuscript over several steps
>     + Use the top-tier model of each provider to get the intended quality
>     + Token usage is high. Check plan limits and API costs in advance
> - (Role while writing) The user makes the final decisions on arguments, strategy, and figures
>     + This skill's role is to present the grounds for judgment and the drafts
> - (Review before submission) The user must review everything before submission
>     + AI models can make errors in facts, figures, and logic
>     + Information on systems, laws, and methods included in the skill may also contain errors or content from before an amendment
>     + The user finalizes all content after checking it against the original text as of the announcement date
> - (Responsibility after submission) The user and the proposer are responsible for any use of documents made by this skill
>     + Winning the bid is outside what this skill guarantees
>     + The skill's author is not liable for damages or legal disputes arising from the use of those documents

## Terms

- The meanings of terms apply equally to SKILL.md, the reference files, and script output. Vocabulary not to be used in manuscripts is set by the Sentence Discipline section and the lexicon.md replacement table

| Term | Meaning |
|------|---------|
| user | The person who writes a proposal, pre-diagnosis report, or planning report with this skill |
| model | The AI that executes this skill's procedure |
| author | Whoever writes the design files and manuscripts. Includes the model and the user |
| proposer (제안사) | The organization that submits the proposal. For a consortium, all participating organizations |
| client (발주처) | The organization that commissions the service contract and receives the final results. A working term used in SKILL.md, the reference files, and the design files. Manuscripts use the organization's real name |
| workspace (작업폴더) | The folder that `init` creates. Holds the design files, manuscripts, delivered files, and state.json |
| design files (설계 파일) | Numbered files in the workspace that hold the design and grounds for the manuscripts. 00_제안전략서.md, 00_진단서.md, 00_기획설계.md, 01_요구항목표.md, 01_배점표.md, 02_섹션대장.md, 02_모듈총괄표.md, 02_스토리라인.md, 03_자료대장.md |
| manuscripts (원고) | The md files in workspace/원고/. build merges them in file name order and typesets them into the delivered file |
| kickoff questions (착수 질의) | The questions asked of the user all at once at step 0. The items are in the Procedure section |
| skeleton (스켈레톤) | An empty hwpx template that defines only styles. The typesetter typesets the manuscripts on top of it. init and build create the default skeleton at workspace/_양식/proposal.hwpx. docx has no skeleton file and generates styles from the same settings definitions |
| output type | The distinction among proposal, pre-diagnosis report, and planning report. The value set by `init --kind` is recorded in state.json |
| output format | The format of the delivered file. hwpx, docx, or both. The recommendation is one (the reason is in the Output Types section) |
| engagement type (과업 유형) | A classification of the RFP engagement used to choose the module framework. Strategic planning type, business planning type, informatization planning type, and so on. Identification signals are in the Module Frameworks by Engagement Type section |
| evaluator (심사위원) | A member of the evaluation committee that scores the proposal |
| section (섹션) | A proposal section (절) used as the smallest unit over which points divide. The ID joins the chapter number and the section number (for example Ⅲ-2) |
| deciding section (결정 섹션) | The section an evaluator reads to score one detailed evaluation item |
| attributed points (통제배점) | The sum of points attributed to a section. `ledger` computes it from the deciding-section column (`결정 섹션`) of the scoring table. For an item with several deciding sections, the points are split evenly |
| original part (오리지널 파트) | Sections written anew for each engagement. The first digit of the manuscript file name is 3 or 5. The type column of the section ledger holds 오리지널. Its sections are called original sections |
| common part (공통 파트) | Sections filled with values from 회사자료.md. The first digit of the manuscript file name is 4 or 6. The type column of the section ledger holds 공통. Its sections are called common sections |
| argument section (논증 절) | A section that develops claims through judgment statements. Background and Necessity, Implementation Strategy, Features and Strengths, Implications |
| descriptive section (정리 절) | A section that organizes facts and composition. Engagement purpose and scope, implementation process, current state summary, list of laws, implementation structure, schedule |
| Background | Short name for the Proposal Background and Necessity section (제안 배경 및 필요성) |
| Features and Strengths | Short name for the Features and Strengths of the Proposal section (제안의 특징 및 장점) |
| engagement purpose (과업 목적) | The higher-level state or direction the client aims to reach through the engagement's results. The answer to "why do it". Sentence pattern, limits on figures, and examples are in the content-models.md Proposal Scope section |
| engagement objective (과업 목표) | The results the engagement sets out to achieve. The usual objective of research and planning engagements is to develop and derive plans, strategies, and measures by the end of the engagement. The answer to "what, and how far" |
| judgment statement (판단문) | A one-line message ending in a nominal form, used as the □ heading of an argument section |
| work products (산출물) | Documents and materials the engagement submits to the client. Includes Task-level lists, analysis tables, criteria tables, drafts, and final results |
| final results (결과물) | All final work products the client receives at the end of the engagement. Final report, plan, operation results, and so on |
| design language (설계 언어) | Vocabulary the author and user use in design files and checks and never carry into manuscripts. Framework stage names and abbreviations (S, C, Q, A, SCQA, WWH), framework language ("과업의 답", "전제조건", and so on), skill-operation vocabulary (통제배점, 섹션대장, 밀도, stream names, and so on), thinking framework names (MECE, pyramid, and so on). Replacements for manuscripts are in the lexicon.md replacement table |
| Module | A bundle of tasks that divides the execution part. Also written as 모듈 inside sentences |
| Task | A detailed task inside a Module. `Step` is an alternative notation at the same level as Task |
| hierarchy level (계위) | The upper and lower divisions of manuscript text. Consists of the heading levels of chapter, section, subsection, and item, and the body levels □, ❍, hyphen, ․, and ※. Notation and typesetting results are in the Manuscript Hierarchy section |
| evidence line (근거 줄) | A hyphen (-) level line or a ※ line |
| framework (골격) | The standard order of composition for a document or section. The modifier sets the target. The background framework is the stage structure (S, C, Q, A) of the Background section, the module framework is the Module structure by engagement type, and the framework of pre-diagnosis and planning reports is the overall form of the document (one of SCQA, WWH, SCR) |
| reasoning stream (계통) | A classification of the thinking order of an engagement or plan. The goal-setting stream (strategic planning methodology) and the gap-analysis stream (problem-solving methodology). The definition is in the stream table at the opening of methods.md |
| bracketed subheading (괄호 소제목) | A noun phrase of 4-8 Korean characters in parentheses at the start of a ❍ or hyphen line |
| label | A bracketed subheading used as a fixed set. (목적), (분석 대상), (산출물) of a Task, and so on |
| band | A one-row table (number cell, empty cell, title cell) that holds a chapter, Module, or Task title. The typesetter generates it |
| divider page (간지) | A page before a chapter that holds only the chapter number and title. Turned on with `build --divider on` |
| filled table (채움본) | A table filled with actual survey values or draft values. Named target list tables, preliminary survey result tables, criteria tables, and work product draft tables qualify |
| long table (장표) | A table that runs past one page after typesetting |
| stated needs (표면 니즈) | The procurement purpose written in the RFP text |
| underlying needs (이면 니즈) | The client's circumstances at the time of procurement that the RFP does not write down |
| key wording dictionary (핵심 워딩 사전) | The table in 00_제안전략서.md that collects noun phrases of the RFP task items in their original notation |
| whitelist | The list of proper terms masked in the tone verdict of `check tone`. Sources are the key wording dictionary, the `RFP 용어` table of the diagnosis file, and the Module and Task names in the module overview table |
| `[확인]` | The marker for a place whose value is not yet confirmed. Never left in a delivered file |
| approximate renderer (근사 렌더러) | rhwp and LibreOffice (H2Orestart), which draw hwpx as PDF without Hancom Office (한/글), and LibreOffice, which draws docx without Word. Some displays differ from the screen display of 한/글 and Word |
| mandatory ISP | An informatization strategy plan that a system such as a law or budget guideline requires before an information system is built |
| HITL alert | The `[long table HITL]` and `[page break HITL]` alerts build prints at points that need user confirmation |
| final report (최종 보고) | The report sent to the user together with the step 6 delivery. It holds the items each section instructs to be reported |

### Work Concepts

- Basic concepts used to judge engagements and write manuscripts. Definitions from business administration and public administration, narrowed to the use of this skill

| Group | Term | Meaning |
|-------|------|---------|
| Way of working | planning (기획) | The process of deciding, before execution, the means and order that achieve a goal (Dror). Its product is a plan |
| Way of working | proposal (제안) | A sales act that wins selection by presenting a solution better than competing alternatives on the few criteria the customer values most, with its grounds (Anderson et al.). Public service contracts pick the negotiation counterpart through proposal evaluation in a contract by negotiation |
| Way of working | research (연구) | Systematic activity that increases knowledge or finds new applications (OECD Frascati Manual). Research in this skill means research engagements that build the grounds for the client's judgment (policy research, survey analysis, and so on) |
| Way of working | consulting (컨설팅) | Independent advice that helps an organization solve problems and carry out change. The process is entry, diagnosis, action planning, implementation, and termination (Kubr) |
| Field of application | management (경영) | Activity that plans, organizes, directs, and controls resources to achieve an organization's goals (Fayol). Management strategy, organizational diagnosis, and public institution management evaluation belong here |
| Field of application | policy (정책) | A course of action a government decides to take or not to take on a public problem (Dye). Made concrete through laws, plans, and budget programs |
| Field of application | institution (제도) | Rules that constrain the behavior of people and organizations, and the way they are enforced (North). Laws, guidelines, evaluation systems, review procedures, and so on |
| Unit of implementation | strategy (전략) | The goal to reach and the choices that lead there. It also decides what not to do (Porter). Every engagement that develops a plan, such as a master plan, mid- to long-term strategy, or ISP, is strategy development |
| Unit of implementation | program (사업) | A unit that assigns funds to a bundle of activities with a purpose. In a company, a business unit that sells value to customers. In public finance, the budget units of program, unit program, and detailed program |
| Goal management | purpose (목적) | The reason an activity is needed and the higher-level state or direction it aims to reach. The answer to "why do it". Engagement purpose applies this meaning to an engagement |
| Goal management | objective (목표) | A concrete level of attainment set to reach the purpose. Specified by target, level, and time. Achievement is measured with indicators. Engagement objective applies this meaning to an engagement |
| Goal management | performance (성과) | The change an activity produces for beneficiaries. Centers on outcomes and impacts as distinct from outputs (OECD DAC). R&D outcomes (연구개발성과) under the R&D laws also include outputs (products, intellectual property, and so on) |
| Goal management | MBO | A way of managing work against goals (Drucker, 1954). Members control themselves by performance against goals. Public management of performance goals and performance indicators follows the same principle. In this skill, the basic principle of strategic planning (including ISP). Also applies to the goal system of business planning and alignment with higher-level policy (methods.md goal-setting stream) |
| Judgment logic | problem (문제) | The gap between the target state and the current state. A state that needs analysis because the way to close the gap is not immediately visible |
| Judgment logic | problem solving (문제해결) | The procedure of finding the causes of the gap and the solutions that close it. This skill applies the seven steps from problem definition to communication (McKinsey) |
| Funding system | R&D | National R&D programs pursued under the Science and Technology Basic Plan for the advancement of science and technology. Performance is proven through the performance goals, indicators, and evaluations of a dedicated law (연구성과평가법, the R&D performance evaluation act). Evaluation results feed into budget allocation. A program (사업) is a ministry's support program. A project (과제) is the unit inside it that an R&D institution carries out under an agreement |
| Funding system | non-R&D (비R&D) | Fiscal programs and institutional programs for policy goals outside R&D (welfare, SOC, industrial support, and so on). Performance is managed through common systems such as the self-evaluation of fiscal programs. A program (사업) is a detailed budget program. A task (과제) is an implementation task in a plan document. The meaning of 과제 differs from document to document. The terminology is more flexible than in R&D |

## Chat Replies

- The user reads only the information needed for judgment in the chat window. A reply consists of file paths, the current step, items for the user's judgment, and error reports. The first reply at the start includes the notice in the Usage Notice section
- Content left out of replies
    + Restating user input, RFP content, or file bodies (including 02_스토리라인.md and manuscripts)
    + Relaying tool calls and work order, explaining the skill's internal terms and rules
    + Announcing the next task, self-assessment of finished work, offers of unrequested extra work (the one line of deepening options when presenting the storyline is the exception)
- Report revisions by the changed points only. Report check results as the PASS count, FAIL count, and unresolved items only
- Bundle questions in one turn. For items with a reasonable default, state the default and proceed
- The reply style is short bullet statements. Keep step completion reports short
- Deliver files that ask the user for review, confirmation, or approval, and delivered files, through the file delivery feature of the execution environment. In an environment where the workspace is not visible to the user, the user cannot open a file from a path alone
    + The main delivery points are the step 2 approval request and re-presentation, confirmation of source image candidates, the step 6 delivery (hwpx or docx, and the PDF when included), and whenever the user asks for a file
    + In an environment where the delivery feature only sends files from a designated folder, place a copy in that folder and deliver it. The original in the workspace is the reference copy
    + In an environment without a delivery feature, give the file path
- Read files only as far as needed. Do not read the same file repeatedly (reading the full text of 01_RFP원문.md at step 1, rereading manuscripts in the in-depth review, and reading at session handover are the exceptions). Check only the verdict summary of script stdout
- Do not skip reports of error causes, sources of figures, or user approval procedures to cut length

## Premises

- A proposal is a document that responds to a scoring sheet. The smallest unit over which points divide is taken as the section
- What decides the award is evidence of practical understanding. Names of institutions to be surveyed, names of materials, survey scale, and preliminary survey result tables count as evidence. Methodology names have no evidential function
- Identifying the underlying needs is what separates a proposal from an RFP summary (stated and underlying needs are defined in the Terms section)
- Volume comes from the number of composition units. In the usual composition of a qualitative technical proposal, one □ with 2-3 ❍, two or more evidence lines, and one table or figure fills about one page. Filling these units reaches the usual proposal volume (hierarchy symbols are in the Manuscript Hierarchy section)
- Keep the short-sentence discipline. Sentences stretched with connective endings blur semantic relations. Secure volume by adding evidence lines and tables
- Evaluators score along the RFP wording. Key wording goes into the key wording dictionary of the proposal strategy file. Code checks whether it appears in the manuscripts
- The execution part usually takes up more than half of the body
- Figures come from source images extracted from the RFP and from literature the user submitted, and from diagram captures of deck pages. Generating diagrams and charts with code (SVG, Python) is out of scope. Other visual elements are expressed as tables

## Preparation

```bash
pip install -U python-hwpx pillow python-docx pdfplumber --break-system-packages
```

- Install dependencies before any other work. In a local environment, install inside a virtual environment without `--break-system-packages`. If a script fails because of a recent API change, update only the failing call site to the latest API
- The start sequence is fixed as below. Securing the renderer and the render test come before the kickoff questions
    + Step 6 is the stretch where the context is fullest with manuscripts and check records. Securing a renderer at that point fails often because attempts shrink and are abandoned early. Securing and testing at the start leaves time to resolve the cause of a failure
    1. Install dependencies (the pip command above)
    2. Secure the renderer (priorities 1-3 below)
    3. `init workspace`
    4. `selftest workspace` judges typesetting and rendering of a sample manuscript. On PASS, check the display of bullets, bands, and tables in one output PNG. On FAIL, move to the next-priority renderer and rerun
    5. `rfp` conversion and kickoff questions
- When moving on to priority 2 (source build), run the build as a background process detached from the session. During the build, run items 3 and 5 (`init`, `rfp` conversion, kickoff questions) in parallel. Run item 4 `selftest` after the build finishes
    + Confirm `selftest` PASS before entering step 1. If the build has not finished by then, install priority 3 and secure PASS on the soffice path first. After the build finishes, rerun `selftest` with rhwp
- The `selftest` verdict is recorded in checks.render of state.json (engine, page count, errors). This record is the basis for renderer decisions at session handover and at step 6
- `selftest` also judges docx typesetting and LibreOffice rendering of the same sample. The verdict is recorded in checks.render_docx of state.json
    + A docx delivery requires PASS in this record
    + If LibreOffice is missing, install it with the apt command of priority 3
- In an environment where the skill folder is read-only and the scripts need changes, copy the whole skill folder to a writable path. From then on `<SKILL>` is the copy
- Verified environment: Python 3.11-3.12, python-hwpx 6.x, python-docx 1.2.0, lxml, pillow, pdfplumber 0.11, pypdfium2 5.x, poppler 24.02, rhwp v0.8.6, LibreOffice 24.x. Install the latest versions. This record is the reference for tracing causes when version differences cause failures
- Renderer priority 1 is the rhwp CLI (https://github.com/edwardkim/rhwp). Obtain the CLI executable directly from GitHub releases with the procedure below. The npm packages (@rhwp/core, @rhwp/editor) are for library and editor use and are excluded as a CLI source. Packages of the same name on PyPI or other package registries are also excluded. The condition for moving to priority 2 (source build) is confirmed failure to obtain a release. A permission denial by the execution environment follows the rhwp permission denial item below
    + (GitHub repository attach) If the execution environment has a tool that attaches a GitHub repository to the session, call it before the first GitHub access. Pass the owner `edwardkim` and the repository name `rhwp` as separate values. Apply any access route the tool's reply names to the steps below. Skip this step when no such tool exists or the call is refused
    + GitHub's address scheme and page layout can change. The model checks the current state and obtains the release in the order below
    + GitHub addresses split into web page paths and file delivery paths. In execution environments with a network allowlist, the file delivery path (`releases/download/<tag>/<file name>`) and the git protocol sometimes pass even when web page paths (`releases/latest`, `releases/expanded_assets`, `api.github.com`) return 403
    + Priority 1 counts as failed only when download through the file delivery path in item 4 fails
    1. If an executable already exists (`rhwp --version` works or `<SKILL>/scripts/rhwp/rhwp` exists), compare its version with the latest tag from item 2 below. If it is the latest, skip obtaining. If it is lower, download the latest with the procedure below and replace it. Keep a specific version only when the user asks for it
    2. Take the tag as the highest version among the version tags printed by `git ls-remote --tags --refs https://github.com/edwardkim/rhwp`. Only when git access is blocked, read it from the end of the final address of the https://github.com/edwardkim/rhwp/releases/latest redirect. If a specific version is needed, use that tag
    3. Read the asset list from the file name column of `https://github.com/edwardkim/rhwp/releases/download/<tag>/SHA256SUMS.txt` fetched with `curl -fL`. If this file is missing, try `releases/expanded_assets/<tag>` and then the GitHub API `/repos/edwardkim/rhwp/releases/tags/<tag>` in that order. The API often returns 403 from shared IPs because of the unauthenticated call limit (60 per hour), which is why it comes last. The body of the release page loads the asset list late. Do not use that body as the basis for the asset list
        + If the highest version tag has no release (SHA256SUMS.txt 404), retry with the next version tag
    4. From the asset list, choose the archive that matches the current platform (OS, CPU). Do not assume a file name pattern. Download the chosen file from `https://github.com/edwardkim/rhwp/releases/download/<tag>/<file name>` with `curl -fL`. If SHA256SUMS.txt exists, verify with `sha256sum -c` and then extract. On a mismatch, stop obtaining
    5. Give the executable execute permission and place it in `<SKILL>/scripts/rhwp/`. If that folder is not writable, place it in `~/.local/bin`. render searches both locations automatically. For any other location, use `render --rhwp path`
    6. Check operation with `rhwp --version` and `rhwp export-pdf --help`. For a version without export-pdf, find the PDF output command in `rhwp --help`
    + Do not include the obtained executable when repackaging the skill
- Priority 2 is building rhwp from source. The git protocol sometimes passes even in environments where downloading assets through the file delivery path is blocked by 403 or repository access denial. If obtaining a release fails, try priority 2 before priority 3
    + rhwp changes often. Decide how to build from the configuration of the repository obtained with `git clone` at that time
    1. The inputs to the decision are the build manifest and workspace configuration at the repository root, toolchain pins, CI settings, and development documents
    2. Identify the target that contains the CLI binary and the PDF export path. Build only that target
    3. If a profile or feature combination that shortens build time exists, choose it. For a review binary, completion time takes priority over optimization level
    4. Place the output binary in the location of priority 1 item 5 (a location render searches automatically). Check operation with the method of priority 1 item 6
    + A clone can reach several GB. The repository may contain large materials unrelated to the build. Check free space before cloning. If the size is a burden, fetch only the paths needed for the build with a history-free partial clone (lazy blob fetch and sparse checkout)
    + Decide which paths to include in a partial clone from the repository configuration as well. The inputs are workspace member paths, target files whose paths the manifest names, files the source loads at build time, and the exclusion list of container builds
    + If the build fails with 'file not found', fetch only the files named in the error. Even when such a file sits inside a large folder, fetch only that one file
    + The latest commit of the default branch may be a work-in-progress state. Even where the release page is blocked, `git ls-remote --tags` shows the tag list. Build the latest release tag first. If the tag build fails, retry with the default branch
    + Builds can take long. In execution environments that cap the run time of a single command, run the build as a background process detached from the session. The same applies to environments that clean up child processes when a command ends. Check the log of a detached build periodically. Resume an interrupted build by rerunning the same command
    + After the build, the clone folder and the build output folder may be deleted
    + On git access denial or build failure, move to priority 3. Record the reason in the final report
- Priority 3 is LibreOffice with H2Orestart. On Debian-based systems, run `apt-get update` and then `apt-get install -y --no-install-recommends libreoffice-writer libreoffice-java-common default-jre-headless libreoffice-h2orestart fonts-nanum poppler-utils`. Then use `render --engine soffice`
- An rhwp permission denial is a case where the permission check of the execution environment refuses a command that downloads or runs rhwp (tag lookup, download, clone, build, run). When a denial occurs, stop obtaining rhwp at that point. Then ask the user whether to allow downloading and running rhwp. Before the answer, do not obtain priority 3, run `selftest`, or start work from step 1 onward
    + (Judgment) A permission denial is a refusal response from the execution environment without the command running. A 403, a connection error, or a repository access denial after the command ran is a network failure and follows the priority rules above
    + (Why ask) Only the user's permission lifts a permission denial. Moving to priority 3 without asking takes away the user's chance to allow it
    + (What stops) Also stop trying to get the same rhwp code through another route (priority 2 source build, another download tool). Start sequence items unrelated to rhwp (`init`, `rfp` conversion) continue
    + (When to ask) For a denial at item 2 of the start sequence, ask it as the first item of the kickoff questions. For a denial at a later step, ask when it occurs
    + (After the answer) If the user allows it, obtain rhwp again from priority 1. If the user does not allow it or does not answer, run `selftest` with priority 3 without priority 2
- If all three paths fail, skip render. Tell the user of the skip and its reason in the kickoff question turn. Record the same in the final report
- On the deck conversion path, pptx input is converted to PDF with LibreOffice (`soffice`). Install with `apt-get install -y --no-install-recommends libreoffice-impress fonts-nanum fonts-noto-cjk`. Without Korean fonts, line breaks and diagram layout of the converted file differ from the original. pdf input is handled without LibreOffice
- The render review needs the Nanum fonts. On Debian-based systems, `apt-get install -y --no-install-recommends fonts-nanum`. Without them the approximate renderer uses substitute fonts, and character widths and line breaks then differ from the delivered file
- poppler-utils is needed for RFP pdf input (pdftotext) and page PNG output (pdftoppm). pdfplumber is needed to extract body text and tables from deck pdfs. pypdfium2, installed together with pdfplumber, is needed for page PNGs, diagram captures, and image extraction from pdf originals

## Commands

| Command | Action |
|---------|--------|
| `init workspace [--kind proposal\|report\|plan]` | Create the workspace. Create state.json (records the output type) and the default skeleton _양식/proposal.hwpx. For a proposal, also place 00_제안전략서.md, 회사자료.md, and the common part templates 원고/41 61 62. For a pre-diagnosis report, also place 00_진단서.md. For a planning report, also place 00_기획설계.md |
| `rfp RFP_file workspace` | Convert hwpx, pdf, docx, or md input into 01_RFP원문.md. Place empty 01_요구항목표.md and 01_배점표.md tables |
| `deck deck_file workspace [--allow-garbled]` | Normalize the proposal deck (pptx, pdf) into a reference PDF. Stop with a warning for a PDF with an incomplete text layer (a size-compressed copy). Output 원문.md, page PNGs, a thumbnail sheet, and embedded images into the 발표자료/ folder |
| `figure workspace page [--grid] [--crop left,top,right,bottom] [--name name] [--pdf source] [--no-trim]` | Capture a whole deck page or part of it as a diagram PNG for insertion. `--grid` only creates a grid PNG for reading crop values. Outer margins are removed automatically (turn off with `--no-trim`) |
| `ledger workspace` | Tally the deciding-section column (`결정 섹션`) of 01_배점표.md. Create 02_섹션대장.md and update attributed points |
| `check rfp workspace` | Judge whether every row of the requirement table has a placement section and whether it matches a section ledger ID |
| `check density workspace [--file manuscript]` | Judge Task density and lone □ in 원고/5*.md |
| `check volume workspace [--file manuscript]` | Judge lone □ and a table right after □ in all manuscripts. For 원고/3*.md and 5*.md, also judge volume units (❍ per □, evidence lines, presence of a table per Task, character count) |
| `check wording workspace` | Judge appearance of key wording dictionary terms, prohibited expressions, mixed notation, and banned sentences |
| `check tone workspace [--reset-whitelist]` | Judge tone and vocabulary. FAIL conditions and warning targets are in the Checks section. Whitelist terms are masked from the verdict |
| `check numbers workspace` | Recalculate total rows of tables and check that composition ratios sum correctly |
| `check fill workspace` | Judge leftover `[확인]` and participation rate overruns in 원고/4*.md and 6*.md. Leftover `[확인]` in 원고/3*.md and 5*.md is a warning |
| `check all workspace [--skip check,check] [--skip-reason reason]` | Run the checks for the output type in one go (all of the above for a proposal, the Checks section of each reference file for pre-diagnosis and planning reports). Record in 05_점검기록.md. Exit code 0 when everything passes. `--skip` leaves out the named checks (Checks section) |
| `build workspace [output path]` | Merge 원고/*.md in file name order. Typeset 납품/{제안서, 사전진단보고서, 기획보고서}.hwpx and .docx (file names are the output.* labels). The default skeleton is regenerated on every run. When both formats are produced, compare the character order of paragraphs and print the result |
| `render output.hwpx or output.docx` | Output PDF and page PNGs (`--engine auto\|rhwp\|soffice`, `--rhwp path`, `--outdir folder`. docx uses LibreOffice). The default output location is next to the original. With `--outdir`, PDF and PNGs go to that folder |
| `selftest workspace` | Judge the render path by typesetting a sample manuscript to hwpx and docx and rendering it. Output goes to workspace/_렌더시험/. Verdicts are recorded in state.json checks.render and checks.render_docx (the `--engine` and `--rhwp` options are the same as for render) |
| `skeleton template.hwpx skeleton.hwpx` | Extract a skeleton and a draft profile from a template the client specified |
| `python3 <SKILL>/scripts/extract_images.py source output_folder [--min-px 64] [--min-kb 2]` | Extract candidate images for insertion and manifest.json from the RFP and user-submitted literature (pdf, hwpx, pptx, docx) |

- build options are `--format hwpx|docx|both` (output format, default hwpx), `--page-break chapter|section|none` (default chapter), `--long-table engine|split`, `--merge auto|explicit|none`, `--toc`, `--toc-depth 1|2|3` (default 2), `--page-number`, `--cover`, `--header`, `--unify manual|auto` (table width unification, default manual), `--theme navy|mono` (band color theme, default navy), `--labels file.json` (document labels, Document Labels in the Typesetting section). Check the value format of `--cover` and `--header` with `build --help`
    + `--title "document title"` is the document title on the first line of the body (planning report). `--chapter-start N` is the first chapter number (chapter-by-chapter output of the pre-diagnosis report)
    + `--divider on|off` controls chapter divider pages. The default is on for the pre-diagnosis report and off for the proposal and the planning report
    + `--long-table` is the default handling of long tables. Always set its value from the answer to the kickoff questions
    + If a manuscript has a table subject to long-table handling and `--long-table` is not set, build stops. A per-table `(장표: )` directive line takes precedence over `--long-table`
- Table of contents, page numbers, and cover are OFF by default. The cover is ON only when the user asks for it. The conditions for turning on the table of contents and page numbers are in the Typesetting section
- `[page break HITL]` in the build lint is an alert from the general-purpose typesetter. Change the default chapter only when the user asks to change page breaks
- When using the client's template, set `--profile path` and `--skeleton path` together. Typesetting with a client template is hwpx only
- Verdicts are recorded in stdout and state.json. Fix FAIL items and rerun
- `build` stops if there is no `check all` PASS record. It also stops if manuscripts, 02_모듈총괄표.md, or the label file changed after PASS (resolved by rerunning check all). Use `--force` only for trial typesetting and for handling misjudgments per the Checks section
- Figure calculations such as point totals, participation rate totals, and person-months are done in code

## Procedure

| Step | Output files | Completion condition |
|------|--------------|----------------------|
| 0 Proposal strategy | 00_제안전략서.md | `selftest` PASS (or notice of skipped rendering), kickoff answers reflected, user confirmation |
| 1 RFP dissection | 01_요구항목표.md, 01_배점표.md | The `## 전개표` (breakdown table) of 01_배점표.md filled, placement sections of requirement items filled, `check rfp` PASS (section ID matching happens on the rerun after step 2 `ledger`) |
| 2 Structure finalization | 02_섹션대장.md, 02_모듈총괄표.md, 02_스토리라인.md | Section name, type, and manuscript file filled, zero `[확인]` in the proposal strategy file and the storyline (the `(Approval)` line is written on approval), user approval after presenting the three files in one turn |
| 3 Original part writing | 원고/31-34, 51-5N files | `check volume` PASS for each file, `check density` PASS for 5* |
| 4 Common part substitution | 원고/41, 61, 62 files | `check fill` PASS |
| 5 Full check | 05_점검기록.md | In-depth review after `check all` PASS, zero `[확인]` in 원고/3*.md and 5*.md (handling of misjudged FAILs is in the Checks section) |
| 6 Typesetting and review | 납품/제안서.hwpx or .docx, page PNGs | Review items passed, discretionary adjustments recorded |

- Ask the items below all at once as kickoff questions. The condition for entering step 1 is receiving the answers and checks.render PASS in state.json. Securing the renderer, `init`, `selftest`, and `rfp` conversion run before the questions (the order is the start sequence in the Preparation section). The `rfp` conversion is used to judge the engagement type (transfer of requirement items and points happens at step 1)
    + Whether to allow rhwp. If an rhwp permission denial occurred in the Setup section, put this first in the list. Present the refused command, the rhwp repository (https://github.com/edwardkim/rhwp), and the commands that run once allowed (release download, clone and build if needed, running rhwp). A question that names the source and the commands makes the scope of the user's permission clear
    + Scope of the proposal (all or a specific part)
    + Whether there is a consortium and each member's role
    + Principal investigator candidates and participating staff candidates
    + Whether an advisory committee runs, and its candidates
    + Delivery format. Output format (one of hwpx or docx recommended. Both is allowed after the notice in the Output Types section), whether the client specifies a template, volume cap, whether to insert a table of contents, page numbers, and a cover, band color theme (navy by default, mono is black and gray). The conditions for turning on the table of contents and page numbers are in the Typesetting section
    + Whether to include a PDF. Not included by default. Give the approximate rendering notice with the question (PDF Copy in the Render Review section)
    + Long-table handling for tables that run past one page. engine (한/글 splits rows at the page boundary) or split (physically divide the table into several). The difference and the limit on deciding arbitrarily are in the Long Table Handling section
    + Whether web search is allowed. If not, preliminary survey tables are filled from model knowledge (the note under the table is in the Task Description Standard section)
    + Whether 회사자료.md is filled. Items the user lacks stay as `[확인]`
    + The judged engagement type. Judge by comparing the identification signals in 01_RFP원문.md with the table in the Module Frameworks by Engagement Type section. For an engagement that matches no identification signal, judge with the stream table at the opening of methods.md. The user confirms the result
    + Narrative length of the proposal background. Detailed (the situation and the problem described across several points) or brief (one or two points each). Present a recommended value with the question by checking the judged engagement type against the lists in the Background Framework section. For an engagement outside the lists, ask without a recommended value. If there is no answer, use the recommended value for an engagement in the lists and detailed for one outside them. The question wording does not use design language such as the names of the forms in the Background Framework section
    + Storyline finalization depth. Basic (□ judgment statements of argument sections and one line per Task) or deep (□ headings and ❍ claim gists for all original sections). Basic if there is no answer
    + Document language and labels. The default is a Korean document with Korean labels unless the user wants another language. For another language, settle the label file and the skip of the Korean-specific checks together (Document Labels in the Typesetting section, references/labels.md)
- In the kickoff question turn, report the render test result in one line (engine, PASS or FAIL). If a source build is running in parallel, state its progress on the same line. While the rhwp permission question is pending, mark it as awaiting permission
- When all three renderer paths failed and skipping render was announced, that notice replaces checks.render PASS
- Fill 00_제안전략서.md step by step. At step 0, write the fields filled from the kickoff answers. At step 1, write the fields confirmed from the RFP text (including basic project conditions, writing rules, and the key wording dictionary). At step 2, write the responding modules, the sections that carry them, and the responding sections
- At step 1, read the full text of 01_RFP원문.md (run `rfp` first if it has not run). The model transfers requirement items, detailed evaluation items, basic project conditions, and writing rules according to the rules in the RFP Dissection section
    + The script only converts formats. Section structure, bullets, and table use of RFPs differ by client. Because of these differences, regex extraction produces false positives and omissions. Extraction is done by the judgment of the model that read the source text
    + For an RFP that presents task content in tables, transfer the rows and cell items of the tables into requirement item rows. Write the parent heading in the parent item column. This column preserves the grounds for placement decisions
- At step 2, create 02_섹션대장.md with `ledger`. Fill the section name, type, and manuscript file columns after reading references/methods.md (the range in the reference file table at the opening). Then write 02_모듈총괄표.md and 02_스토리라인.md. The presentation and approval procedure is in the Storyline Finalization section of Framework Design
    + The condition for starting step 3 is the approval record. The cost of revising the argument is lowest before writing manuscripts. Revising the argument after the manuscripts are complete means going through volume units and tone checks all over again
- At step 3, read lexicon.md and then complete the files one at a time. For each file, read the matching section of content-models.md first. The order is Background and Necessity (31), Proposal Scope (32), Implementation Strategy (33), Features and Strengths (34), implementation structure (51, when set as a separate section), module execution plans (52 onward)
    + Proposal Scope (32) consists of the engagement purpose and objective □ followed by the engagement scope □. Definitions, sentence patterns, and limits on figures for the two □ are in the content-models.md Proposal Scope section
    + The □ headings of argument sections (31, 33, 34) use the approved judgment statements of 02_스토리라인.md in order. Module introductions and the (목적) of Tasks expand from the one line in the execution part table
    + Run `check volume --file` for each file. Resolve FAIL by adding composition units
- At step 4, substitute the `[확인]` in 원고/41, 61, 62 with values from 회사자료.md. For track records, select only engagements that meet the RFP's recognition requirements
- At step 6, apply the Typesetting and Render Review sections. Use the renderer secured at the start. If `render` fails because the renderer is missing, reapply the Preparation procedure without skipping. Rerun render after confirming `selftest` PASS
- At session handover, read state.json, 02_섹션대장.md, and 02_스토리라인.md first. Judge whether step 2 is complete from the `(Approval)` line of the storyline. Resume from the unfinished step
    + If the execution environment changed, the renderer executable may be gone. Run `selftest` right after resuming. On FAIL, secure the renderer again with the Preparation procedure

### Deck Conversion Path

- Applies to requests to turn a proposal deck (pptx, pdf) into an hwpx proposal. Treat the deck the same way as an RFP. Details are in references/deck-conversion.md
- The order is parsing with `deck`, reading the full text of 발표자료/원문.md, transferring to the design files (proposal strategy file, module overview table, storyline), comparing with the RFP requirement items, and writing manuscripts. Steps and approval procedure are the same as the general path
- deck-conversion.md is the single source for `deck` stop handling, the `[보강]` marker, diagram capture, and the failure patterns of the conversion path
- Submitting the RFP along with the deck is recommended. The recommendation to submit the RFP, the procedure without an RFP, and items for the final report are in the deck-conversion.md RFP Comparison section

## Proposal Strategy

- The fields of 00_제안전략서.md are basic project conditions (including the writing rules row), agency naming, minimum requirement verdict, feasibility verdict, client needs, external environment, competitive landscape, own strengths and weaknesses, proposal strategy, key wording dictionary, prohibited expressions, storyline, staff candidate pool, and price direction
- The heading `금지 표현` of the prohibited expressions section and the column name `RFP 용어` of the key wording dictionary are markers the check code reads. Keep them in Korean
- Record unmet minimum requirements in the feasibility verdict as reasons to hold off participation. Get the user's judgment
- Derive underlying-need hypotheses as answers to the questions below. A hypothesis at the level of an RFP summary does not count as a hypothesis
    + What circumstances make the client procure at this moment (revision cycle of a higher-level plan, audit findings, first year of a new system, reorganization, budget review, shortcomings of a previous contract, and so on)
    + Whom does the client's responsible department have to persuade with the final results (budget authorities, the competent ministry, the National Assembly, a supervising agency, an internal union, and so on)
    + Which phenomena does the background text of the RFP describe negatively. What does the client see as their cause
- Write the modules that answer the underlying needs in the responding module field. The Background section describes the underlying needs together with supporting materials
- 1-3 differentiation points. Each point comes with at least one ground among track record, data, and staff. Each point leads to capability claims in the Features and Strengths section and to strategies in the Implementation Strategy section. One point may expand into several capability claims
- In the competitive landscape field, record the strengths of each competitor type. Link the proposer's grounds that offset those strengths to the differentiation points
    + If web search is allowed, fill the competitor candidate table through the competitor search paths below (award records, disclosed engagements, similar organizations, industry search). Estimate strengths and weaknesses by type based on this table
    + Most organizations do not disclose public engagements they carry out. The disclosed-engagement path alone leaves the table empty. Use the award record path together with the estimation paths (similar organizations, industry search)
    + (Eligibility verdict) Before searching for competitor candidates, judge which company sizes may bid on this announcement
        + Searching without this verdict includes large consulting firms that cannot bid. The competitive landscape is then distorted
        + The first basis for the verdict is the eligibility wording of the bid announcement and the RFP. If the wording and the amount criteria differ, follow the wording
        + If there is no wording or it is ambiguous, estimate with the systems below. Attach `[확인]` to an estimated verdict
    + (Amount criteria for service contracts) Article 2-2 of the Enforcement Decree of 「중소기업제품 구매촉진 및 판로지원에 관한 법률」 (Act on Facilitation of Purchase of Small and Medium Enterprise-Manufactured Products and Support for Development of Their Markets) sets company size limits for public institution service contracts
        + An estimated price below KRW 100 million is restricted competition among small enterprises or micro-enterprises. Medium enterprises, mid-sized enterprises, and large enterprises cannot bid
        + If it is evident that three or fewer eligible small or micro-enterprises exist, or the announcement failed to attract bids, it relaxes to restricted competition among SMEs. Medium enterprises may then bid
        + An estimated price of KRW 100 million or more and below the notified amount is restricted competition among SMEs. Mid-sized and large enterprises cannot bid
        + At or above the notified amount, there is no company size limit by amount
        + Services designated by the Minister of SMEs and Startups as products for competition among SMEs are competition among SMEs regardless of amount. Check the announcement for this designation
    + (Amount conversion) The estimated price excludes VAT
        + If the base amount or budget in the announcement includes VAT, divide by 1.1 to get the estimated price. On a VAT-inclusive basis, KRW 100 million corresponds to KRW 110 million, and the notified amount of KRW 230 million corresponds to KRW 253 million
        + The notified amount is the amount for goods and services that the Minister of Economy and Finance notifies every two years under Article 4(1) of 「국가를 당사자로 하는 계약에 관한 법률」 (Act on Contracts to Which the State Is a Party). The amount for 2025-2026 is KRW 230 million
        + If the announcement date is in 2027 or later, confirm the new notified amount by web search
    + (Academic research exception) Article 2-3 of the same Enforcement Decree allows exclusion from priority procurement contracts when participation of non-profit corporations is needed for policy advisory services such as academic work, research, surveys, and evaluation
        + An announcement using this exception states the reason in the announcement. Large consulting firms may bid on such announcements
        + For academic research services, the verdict rests on the amount, the eligibility wording of the announcement, and whether an exception reason is stated
    + (Amount criteria for SW projects) For software projects, the lower limits on large enterprise participation are set by Article 48 of 「소프트웨어 진흥법」 (Software Promotion Act) and Appended Table 1 of the Ministry of Science and ICT notice 「중소 소프트웨어사업자의 사업 참여 지원에 관한 지침」 (Guidelines on Supporting Project Participation of Small and Medium Software Businesses, No. 2026-4)
        + A large enterprise under this criterion is every software business other than an SME. Mid-sized enterprises count as large enterprises
        + Companies with revenue of KRW 800 billion or more may join only projects of KRW 8 billion or more
        + Companies with revenue below KRW 800 billion may join only projects of KRW 4 billion or more
        + Companies within five years of moving from SME to mid-sized enterprise may join projects of KRW 2 billion or more. Projects below KRW 2 billion are open only to SMEs
        + Companies belonging to a business group subject to limits on cross-shareholding may join only exception projects regardless of amount
    + (SW project amount) The project amount of an SW project is the estimated price including VAT. The calculation differs from the estimated price used in the service contract criteria
    + (Checking SW project announcements) Whether the large enterprise participation limit applies must be stated by the client in the announcement or RFP. Check that wording first for the verdict
        + For informatization planning services such as ISP and ISMP, check from the announcement wording whether they count as SW projects
        + The government improvement plan of January 2024 (raising the SME-only project threshold to KRW 3 billion, opening design and planning projects, allowing business groups subject to cross-shareholding limits to join projects of KRW 70 billion or more) is not reflected in Appended Table 1 of the guidelines revised in January 2026. Check applicability from the announcement wording
    + (Applying the verdict) If the verdict limits bidders to SMEs or smaller, delete the large consulting firm type from the competitive landscape
        + Keep the university industry-academic cooperation foundation type regardless of the company size verdict
        + Include company size and region conditions in the queries of the similar organization and industry search paths. Search for the organizations meeting the conditions at the query stage. Example queries are "[지역] 소재 [업종] 소기업" ([region]-based [industry] small enterprises) and "[과업 유형] 연구용역 중소기업 제한 낙찰" ([engagement type] research service SME-restricted award)
        + Record the verdict and its grounds (the announcement wording, or the estimated price and the applicable article) in the competitive landscape section
    + (Filter release) If the user asks for a competitor search without eligibility filtering, skip the eligibility verdict and its application
        + Frequent revisions of the systems can make the verdict wrong. The user's judgment on filtering takes priority
        + In this case, apply the large consulting firm default candidate rule regardless of the announcement amount. Also skip eligibility exclusion and the excluded organization memo on the industry search path
        + Write "필터링 해제(유저 요청)" (filter released at user request) in the verdict cell
    + (Award records) Check opening results and award results of KONEPS (나라장터) by web search
        + The inquiry screens of the KONEPS site often do not open through the web search tool. Use public posting pages exposed in search results for inquiries
        + Public posting pages are the announcement detail pages of private bid information sites and the bid announcement, preferred bidder selection result, and contract information disclosure boards on client websites
        + Search engines index announcement titles more heavily than opening results. First find, by announcement title, the announcement pages of past projects with the same name at the same client and of projects of the same type at other clients. Then check the opening result, winning bidder, and preferred bidder items on those pages. If the items are missing, search again by announcement number
        + Example queries are "[과거 사업명] 개찰결과" ([past project name] opening result), "[과거 사업명] 우선협상대상자" ([past project name] preferred bidder), "[공고번호] 낙찰자" ([announcement number] winning bidder), and "[발주처명] 계약정보 공개 [과업 키워드]" ([client name] contract information disclosure [engagement keyword]). KONEPS award results provided by the user are also recorded through this path
    + (Inquiry method) Fetch announcement pages one at a time, only as needed
        + Follow each site's terms of use and crawling limits (robots.txt). Do not repeatedly crawl list pages
        + If the user provides an authentication key for the Public Procurement Service KONEPS Open API on the Public Data Portal (bid announcement information service, award information service, contract information service), use API queries first
    + (Disclosed engagements) Search for contract wins that performers announced through press releases, track record lists on their websites, blogs, and social media. Search both the same client's projects and projects of the same type at other clients. Example queries are "[발주처명] 연구용역 수주" ([client name] research service win), "[발주처명] 착수보고회 수행기관" ([client name] kickoff meeting performer), and "[과업 유형] 수립 연구용역 최종보고회 수행기관" ([engagement type] development research service final report meeting performer)
    + (Similar organizations) Summarize the proposer's profile from the industry, business field, headcount, and track record fields of 회사자료.md. Search for organizations with the same profile. The purpose of this path is to find organizations that repeatedly compete with the proposer in the same client market
        + Example queries are "[자사 사업 분야] 전문 컨설팅 기업" ([own business field] specialized consulting firm) and "[자사 대표 과업 유형] 연구용역 수행기관" ([own main engagement type] research service performer)
        + If 회사자료.md is empty, use the kickoff answers. If both are missing, skip this path
    + (Industry search) Derive the industries that can carry out this engagement from its characteristics. Search for companies and organizations in those industries
        + For example, IT consulting firms and SI affiliates for an ISP, science and technology consulting firms and specialized research institutes for R&D performance analysis, regional research institutes and urban planning engineering firms for a regional development plan
        + Use association member lists, mentions of major companies in industry articles, and queries that combine the RFP's task field and engagement type with the client type ("OO 기본계획 수립 연구용역", "OO 분야 산학협력단 정책연구")
        + Exclude organizations that cannot bid because of RFP eligibility (industry registration, large enterprise participation limits, regional limits)
    + (Large consulting firm default candidate rule) A rule that places large consulting firms with many public consulting contract wins as default candidates of the large consulting firm type
        + It applies to announcements on which the eligibility verdict allows mid-sized and large enterprises to bid. With a filter release request, it applies to all announcements
        + Large consulting firms win many public service contracts regardless of whether their websites advertise a public sector practice. Do not filter candidates by whether they advertise a public sector practice
        + Include organizations whose names do not contain "consulting" when they have public consulting contract wins. Confirm their contract wins separately through the award record path
        + Obtain organization names by searching industry articles and reports of public service performance. After the search, record grounds of performance in the task field in the similar engagement or selection grounds column. If no grounds are confirmed, write "공공 용역 다수 수주 기관군" (group of organizations with many public contract wins) in that column. The confirmation source is the organization's website URL and the confirmation date
    + (Excluded organizations) For organizations excluded by eligibility, write the name, reason for exclusion, and confirmation path in the excluded organization memo under the competitor candidate table. If the previous performer or a confirmed organization cannot bid on this announcement, the intensity of competition changes. Reflect this in the strengths and weaknesses by type
    + (Search order) Run the award record and disclosed engagement paths first regardless of results. Organizations these two paths find are those with confirmed contract wins
        + If three consecutive queries on one path yield no new organization, move to the next path
        + Run the similar organization and industry search paths until at least one organization fills each competitor type of the competitive landscape table
        + Delete the rows of types that do not apply to the engagement. Add rows for new types derived through the industry search
    + (Table entries) Enter organizations with a confirmation source in the competitor candidate table
        + In the confirmation path column, enter one of the search path names (낙찰 기록, 수행 공개, 자사 유사 기관, 업종 탐색)
        + Organizations found through award records and disclosed engagements are confirmed organizations. Organizations found through similar organizations and industry search are estimated candidates. The strengths and weaknesses text marks estimated candidates as estimates
        + In the confirmation source column, enter the source URL and the posting date. If the posting date is not confirmed, enter the search date as "확인일" (confirmation date). The confirmation source for user-provided material is "유저 제공(나라장터)"
    + (Web search not allowed) Enter only the award results the user provided. Resolve `[확인]` in the other rows by asking the user
    + (Unconfirmed types) For types with no confirmed organization after running all search paths, attach `[확인]` and resolve by asking the user
- The three storyline field lines (Background and Necessity, Implementation Strategy, per module) are a draft that sets the direction. At step 2, 02_스토리라인.md expands these three lines into section messages and □ judgment statements. If the two files disagree, update the strategy file based on the approved version of 02_스토리라인.md
- Derive the implementation strategy from engagement characteristics and risk factors through key success factors. Record the derivation order only in the proposal strategy file. The body describes the strategy, the risk it resolves, and the value it secures in □ judgment statements and ❍
    + The implementation strategy derivation table is the author's internal reasoning record. Do not carry it into the manuscript. A table that lists risk factors or values secured by strategy stays out of the manuscript as well
        + A carried-over table repeats the content of the □ judgment statements and ❍. It also shows evaluators the list of risk factors and the author's derivation process as they are
    + Derive strategy from why this engagement is hard. The reason the client undertakes the engagement (the problem in the Background) is answered by the engagement as a whole. A strategy derived from the Background problem ends up as the Module list renamed as strategies
    + (Engagement characteristics) The scope the engagement must finish and the nature of what it must handle. Task content set by the RFP, institutional procedures, compliance duties, and constraints also go in this column. Duties are a premise every bidder carries out. Differentiating measures that fulfill a duty go in the strategy column. Examples are a scope that must run from plans to build requirements, unstructured materials mostly in HWP and PDF, a network-separated security system, technical characteristics that differ by field, an evaluation schedule set by an institution, the number of stakeholders, and the engagement period
    + (Risk factors) Points where the final results can go wrong because of the engagement characteristics. Examples are poor text extraction from documents, inability to send sensitive materials to external models, indicator interpretations that differ by technology field, missing performance evidence within the evaluation submission deadline, initiatives disconnected from field demand, and a plan shelved internally after it is developed
    + (Key success factors) The conditions the final results must meet to overcome the risks, with a one-line test. For example, the test for "effective initiative discovery" is "selecting initiatives that users feel reduce actual work"
    + (Value secured) The value the engagement and its final results give the client when the success factors are met. Write it paired with the risk it resolves. Examples are "오답 불신을 해소하는 신뢰성" (reliability that removes distrust of wrong answers) and "민감 자료의 외부 유출을 막는 안전성" (safety that prevents sensitive materials from leaking outside). An item that states only a value word without a risk becomes a phrase that fits any engagement
    + (Implementation strategy) Specialized measures that secure the success factors
        + (Design principles for final results) By what principle the final results are made. Examples are specialization based on regional capabilities, a staged response that runs from technology to policy and performance, answers that present evidence, and performance analysis with a comparison group
        + (Execution activities) Through which activities and operations the engagement is carried out. Examples are subcommittees by technical characteristic, pretests of indicators per subcommittee, early drafts of work products per issue at the start, advisory consultation combined with demand surveys, and briefing sessions on using the work products
    + (Validity conditions) An implementation strategy is a measure with specialization and differentiation for effective execution of this engagement. Specialization is design fitted to the characteristics of the engagement's subjects. Differentiation is design the proposer adds on top of the level that the RFP and institutions require
        + (Duty removal test) The measure that remains after removing compliance with RFP task content, institutional duties, and constraints from the judgment statement is the strategy. If nothing remains, it is a restatement of duties
        + An execution activity becomes a strategy when its design is pinned to the difficulties of the engagement. Examples are the criteria that divide subcommittees, the targets and judgment items of a pretest, and the timing and participants of sharing work product drafts
- The outcomes the client obtains are the material for the one-line storyline and the section messages. Write them in the storyline field
    + Outcomes are changes that happen to the client after the engagement. Examples are responding to a supervising agency's review, budget reflection, implementation of a system, start of a follow-up project, and agreement among implementing departments
    + Work products are means to reach outcomes. Writing the submission of work products in place of outcomes reads as a proposal that ends with delivering a report
    + Specify an outcome as whose what becomes which state by when. The materials are the procurement circumstances and persuasion targets of the underlying-need hypotheses
    + Specifying target, time, and state is the check criterion for how concrete an outcome is. Use time values only as design material
    + Do not use outcomes as the ending of implementation strategy judgment statements. When the distance between a strategy and an institutional event is long, the gap gets filled with the author's plans such as schedules and consultations
- The key wording dictionary holds noun phrases of RFP task items in their original notation. Entering the same notation in the proposal notation column also detects spacing variants
- The price direction records only the bid range against the budget cap and the grounds for the judgment

## RFP Dissection

- 01_요구항목표.md transfers the lowest-level items of the task details verbatim. A summary makes wording comparison impossible. The parent item column is the path of parent headings
- Enter section IDs in the placement section column. Separate multiple IDs with commas
- The `## 전개표` (breakdown table) of 01_배점표.md transfers the detailed evaluation items of the evaluation section verbatim. The deciding section (`결정 섹션`) is the ID of the section an evaluator reads to assign that score
    + Judge the deciding section for each detailed evaluation item. For example, a major item "연구내용의 타당성 30점" (validity of research content, 30 points) splits into different deciding sections by detailed item
    + For quantitative items (credit rating, number of track records), enter `정량` (quantitative) as the deciding section. Writing cannot raise the score of a quantitative item
    + If there is a lower bound for negotiation eligibility (85% of the technical evaluation, and so on), give priority to even completeness across all sections
- Record basic project conditions in the proposal strategy file after checking the source text
- Extract from the writing rules the ban on vague expressions, quantification duties, sanctions for false statements, reference table duties, volume cap, and abbreviation list. Enter vague expressions the RFP names in the `금지 표현` (prohibited expressions) section. Enter the rest in the writing rules row of basic project conditions
- Cite law articles that the RFP quotes, with numbers, only after checking the original article
- The reference date of the manuscripts is the time of writing. Describe systems, organization names, and figures that changed after the RFP announcement by the current standard. Give a source next to current values
- In the tables of 01_RFP원문.md, `^` marks a cell merged with the cell above and `<` a cell merged with the cell to the left. After transferring the scoring table, compare the point total with the RFP total score in code
- If the RFP requires a reference table, use the number and placement section columns of 01_요구항목표.md as the original of the attached reference table

## Framework Design

### Chapter Structure

- Use the names, order, and numbers of chapters and sections exactly as in the RFP's specified table of contents and proposal writing guidelines. Without a specified table of contents, apply the table below with the order of evaluation items as a reference
- For each section of a specified table of contents, enter the type and content model in 02_섹션대장.md. The user confirms them at the step 2 approval
    + (Type) A section written anew for each engagement is 오리지널 (original). A section filled with values from 회사자료.md is 공통 (common)
    + (Content model) Judge by the evaluation items and required content the section must answer. Procurement background and necessity use the background model, engagement purpose and scope the proposal scope model, the proposer's capabilities and distinctiveness the features and strengths model, execution strategy and application of methods the implementation strategy model, and execution measures per task the Task Description Standard
    + If one specified section spans two models, write it as one subsection (###) per model
    + For a section without a matching model (education and training, technology transfer, social value, and so on), use the RFP's required sentences as material for □ and write in volume units
- Section IDs use the chapter number and section number of the specified table of contents (defined in the Terms section)

| Order | Chapter | Section names | Type | Default file name |
|-------|---------|---------------|------|-------------------|
| Ⅰ | 제안 개요 (proposal overview) | 제안 배경 및 필요성 (31), 제안 범위 (32), 추진전략 (33), 제안의 특징 및 장점 (34) | 오리지널 | 3x |
| Ⅱ | 제안사 일반현황 (proposer general status) | 일반현황, 조직과 인원, 주요 사업실적 (41) | 공통 | 4x |
| Ⅲ | 사업 수행부문 (execution part) | 과업 추진체계 (51, when a separate section), 수행방법과 프로세스, 세부 수행내용 (52 onward) | 오리지널 | 5x |
| Ⅳ | 사업 관리부문 (management part) | 수행조직 및 업무분장 (61), 추진일정, 업무보고, 산출물 관리, 보안, 사후관리 (62) | 공통 | 6x |

- The first digit of a manuscript file name is its check type. 3 is an original of argument and overview character, 4 and 6 are common (`check fill` targets), and 5 is an original of execution measures (`check density` target). Use the digit that matches the section type in a specified table of contents as well
    + build merges in file name order. For an engagement with a specified table of contents, prefix every manuscript file name with a sequence number in table-of-contents order (`10-31_사업이해.md`, `20-52_세부수행방안.md`, `40-41_제안사현황.md`). The check type is read from the first digit after the sequence prefix
    + For an engagement without a specified table of contents, use the default file names of the table above without a sequence prefix
    + The file numbers in SKILL.md and the reference files (31-34, 41, 51, 52, 61, 62) are default file names. Under a specified table of contents they refer to the files to which the same content model or template applies
- Write chapter titles (`# title`) directly in the manuscripts. For each chapter, write it once on the first line of the first file, in file name order, among the manuscript files of that chapter
    + Replace the chapter titles, section titles, and section order of the templates (41, 61, 62) to match the specified table of contents. If sections split across chapters, split the file (keep the type digit)
- Classify a section of common character with 5 or more attributed points (principal investigator expertise, security management, and so on) as original. Even when it uses common material, write it at step 3 density
- If the RFP specifies a summary chapter (proposal overview) and a body chapter (implementation strategy) separately, put strategy names and one-line gists in the summary chapter. Put the full implementation strategy model in the body chapter
- If the RFP requires an abbreviation list or bibliography, put it as a table where the RFP specifies. Without a specified place, put it at the end of the last chapter
- Numbered levels go down to chapter (Ⅰ.), section (1.), subsection (가.), and item (1)). Absorb additional points into the □ level. Even when the numbering format of the RFP's table of contents differs ((1) after 가., and so on), levels below the subsection follow the Manuscript Hierarchy section

### Placement of the Implementation Structure

- The implementation structure (추진체계 or 수행체계) shows how Modules and Tasks are carried out, linked, and managed. The actors are the client, the proposer, and stakeholders. It plays a HOW role like the implementation strategy
- The implementation structure overlaps in material with the project organization. The project organization is an administrative description covering staff, participation rates, and division of duties. The implementation structure describes the same material from the practical view of committee operation, consultation with the client, and linkage between modules
- The model decides the placement based on the RFP's table of contents and evaluation items. The decision is reflected in 02_섹션대장.md at step 2. The user confirms it at the step 2 approval
    + If the RFP requires the implementation structure as a separate item, write it as a separate section (51)
    + If the RFP does not require it, merge it into the implementation strategy section (33) or the project organization section (61)
    + Large planning engagements that run a planning committee and subcommittees (preliminary feasibility study response, and so on) give the implementation structure a large weight. Consider a separate section first
- Whatever the placement, put implementation structure content in one section once. The implementation structure table, the committee operation (draft) table, and the member candidate (draft) table go in that section. Other sections describe only their own content
    + If committees are a means of the implementation strategy (subcommittees by technical characteristic, and so on), the implementation strategy describes the composition criteria and the value secured. The operation (draft) table with sessions, timing, and agenda goes in the section that holds the implementation structure content

### Background Framework

- Background and Necessity is the WHY section. It describes why the client needs this engagement now. It does not describe the proposer's capabilities (WHAT) or way of working (HOW)
- The background framework is SCQA or SCR. The definitions of the S, C, Q, and A stages follow how Barbara Minto's Pyramid Principle composes an introduction. SCR is a practical variant that omits Q and presents the resolution (R) directly. Skipping a stage makes the text read as generalities
    + (S situation) Facts the reader already knows, or facts about the topic the reader will accept without dispute
    + (C complication) A change or problem that arises in that situation and raises a question
    + (Q question) The question the complication raises in the reader's mind
    + (A answer) The answer to that question. Leads into Proposal Scope and Implementation Strategy
    + (R resolution) The last stage of SCR. Presents the resolution of the complication without Q
- Derive the material for each stage per engagement from the client needs, external environment, and proposal strategy of 00_제안전략서.md
- The recommended order for the whole Background narrows from the outside in. Opening with a narrow topic leaves the necessity of the engagement unconnected to the higher-level environment
    + The order of entry is the macro environment (policy, technology, society), conditions of the field and industry, and circumstances inside the client
    + Choose the stages to include to fit the engagement. Keep the order of the included stages
- Write □ headings and bracketed subheadings in the language of the engagement. Framework names, stage names, and framework language such as "과업의 답" and "전제조건" are design language (Terms section)
- The expanded form (business planning, informatization planning, strategic planning) develops S and C across several points
- The compressed form (performance analysis, management evaluation response, organization and HR, problem solving) gives S and C one or two points each. Each point still meets the lower bounds of composition units
- The length the user chose in the kickoff questions takes precedence over these lists

### Module Frameworks by Engagement Type

| Type | Identification signals | Module framework | Pitfalls |
|------|------------------------|------------------|----------|
| Strategic planning type (전략기획형) | 기본계획, 중장기 전략, 비전, 육성계획 (master plan, mid- to long-term strategy, vision, promotion plan) | 외부 환경 분석 → 내부현황 및 사례 분석 → 비전 및 전략 도출 → 실행계획 및 로드맵 (external environment analysis → internal status and case analysis → vision and strategy derivation → action plan and roadmap) | Mixing To-be into the environment analysis, jumping to strategy without implications |
| Informatization planning type (정보화계획형) | 정보화전략계획(ISP), 지능정보사회계획, 정보화 마스터플랜, the client's own IT planning (planning for system and platform builds, data and AI adoption plans, digital transformation plans, next-generation and upgrade plans) | 환경 분석 → 현황 분석 → 목표모델 설계 → 이행계획 (environment analysis → current state analysis → target model design → transition plan) | Not judging whether a mandatory ISP applies, forcing ISP procedures and work product names on IT planning outside mandatory scope, budget totals without calculation grounds, arbitrary classification codes |
| Business planning type (사업기획형) | 신규사업 기획, 사전기획, 타당성 검토 (new program planning, advance planning, feasibility review) | 정책 및 환경 분석 → 유사사업 및 지적사항 분석 → 목표체계 및 논리모형 설계 → 타당성 확보 → 심사 및 보고 대응 (policy and environment analysis → analysis of similar programs and findings → goal system and logic model design → securing feasibility → review and reporting response) | Confusing outputs with outcomes, describing an abolished system as current |
| R&D performance analysis and evaluation type (R&D 성과분석과 평가형) | 성과평가 대응, 자체평가, 성과관리, 효과성 분석 (performance evaluation response, self-evaluation, performance management, effectiveness analysis) | 대상사업 현황 → 분석 프레임워크 → 성과 조사 및 검증 → 투입, 산출, 효과 분석 → 대표성과 및 개선방안 → 보고서 및 점검 대응 (target program status → analysis framework → performance survey and verification → input, output, and effect analysis → representative outcomes and improvements → report and inspection response) | Output per input without a comparison group, ignoring the release date of guidelines |
| Problem-solving type (문제해결형) | 실태조사, 동향조사, 수요조사, 제도 개선, 과제 발굴, 사업 성과분석 (status survey, trend survey, demand survey, institutional improvement, initiative discovery, program performance analysis) | 현황 진단 → 갭 분석 → 개선안 도출 (current state diagnosis → gap analysis → improvement derivation). Survey-centered engagements inherit the RFP task structure as modules | Problem definition identical to the RFP summary, unspecified survey scale |
| Management evaluation response type (경영평가 대응형) | 경영평가 대응, 경영실적보고서, 편람 지표 (management evaluation response, management performance report, manual indicators) | 편람 지표 구조 분석 → 전년도 지적사항 분석 → 지표별 실적 논리 재구성 → 비계량 서술 전략 → 보고서 작성 지원 (manual indicator structure analysis → analysis of prior-year findings → rebuilding performance logic per indicator → non-quantitative writing strategy → report writing support) | Mixing in the R&D performance analysis framework, ignoring the manual revision date |
| Support program operation type (지원사업 운영형) | 프로그램 운영, 사업화 지원, 창업지원, 인력양성 운영기관 (program operation, commercialization support, startup support, workforce development operator) | 정책 및 사업 배경 → 수요자 현황 및 애로 → 프로그램 설계 → 성과관리 → 운영 및 집행 (policy and program background → beneficiary status and difficulties → program design → performance management → operation and execution) | Confusing outputs with outcomes, unspecified scale of program stages |

- A composite engagement mixes types per module. The RFP task details always take priority over the module framework. The status of frameworks (institution-based, conditionally institutional, discretionary) is in the track table at the opening of methods.md
- For institutional performance evaluation response of non-R&D programs, apply the R&D performance analysis and evaluation framework. Replace performance types with the classification of the applicable guidelines. For program performance analysis outside institutional evaluation response, apply the problem-solving framework
- For management evaluation response, apply the management evaluation response framework. For indicator development and organizational diagnosis, apply the strategic planning framework
- Strategic initiatives and implementation initiatives inherit the parent number (1. strategy, 1-1. strategic initiative, 1-1-1. implementation initiative)
- Choose the paths for securing initiatives and demand (demand survey, perception survey, expert participation, direct derivation) to fit the RFP's requirements. Set up Tasks for each chosen path. If only direct derivation is used, add an advisory or demand confirmation procedure
- Place every requirement item in at least one Task. `check rfp` judges empty cells in the placement section column. Task-level placement is checked by comparison with the module overview table

### Module Overview Table

- Write the table below in 02_모듈총괄표.md at the workspace root. This file is a step 2 design output like the section ledger and the storyline. This file is the single original of the table
- At the start of the execution measures in the manuscript, write one ❍ holding the gist of the table and one `(삽입: 모듈총괄표)` line, in that order. When build merges, it replaces this line with the caption, the long-table directive line, and the table
    + Choose the insertion point to fit the chapter structure. In a structure without a specified table of contents, it is the first section of the execution part chapter
    + If the directive line is missing or appears twice or more, build stops with ERROR
- List the items of a work content cell with `◦` and `<br>`
- When a Module or Task name joins two objects, use "및" (for example "현황 분석 및 진단"). The reason is the two-item listing rule in the Sentence Discipline section
- This table usually runs past one page. Apply the long-table handling from the kickoff answer. If the answer is engine, write the `(장표: engine)` directive line under the caption. If the answer is split, divide the table by Module (the split limit for tables with a vertically merged first column is in the Long Table Handling section). Write the divided tables one after another in this file with captions (1), (2). build inserts everything from the first caption to the last table at once

```
<표> 모듈별 수행내용과 산출물
| Module | Task | 수행내용 | 산출물 |
|---|---|---|---|
| Module 1. 현황 분석 | Task 1-1. 정책 문헌 분석 | 국정과제와 상위계획 12건 분석 | 정책 요건 목록 |
```

### Storyline Finalization

- Right after writing 02_모듈총괄표.md, the model copies `<SKILL>/assets/storyline.md` into the workspace as 02_스토리라인.md and fills it
- The storyline is the file that settles section messages and □ judgment statements before the manuscripts. Most of the user's revision requests concentrate on the argument (what is seen as the problem and what answers it). Agreeing on the argument in one file of a few dozen lines keeps revisions from spreading into manuscript rewrites
- The basic depth consists of the items below
    + (One-line storyline) One sentence in which the problem recognition of the Background leads through the implementation strategy and modules to the client's outcomes
    + (Section messages) One message line for each original section of the section ledger. Attributed points are shown alongside. The user judges weight with these values as well
    + (Point judgment statements) All □ judgment statements of the argument sections Background and Necessity, Implementation Strategy, and Features and Strengths. Background shows the stage (S, C, Q, A) and supporting material names alongside. Implementation Strategy shows the risk factor it resolves and the value it secures. Features and Strengths shows the differentiation point and its grounds
    + (Execution part) One line for each Module and Task. The order is target, action, results of work products and activities, and point of use. Definitions and sentence patterns are in the Purpose of Modules and Tasks section under Common Standards in methods.md. Show the underlying need or differentiation point it answers alongside
- The deep depth adds to the basic composition all □ headings of all original sections (including Proposal Scope and the implementation structure), 2-3 ❍ claim gists per □, and the tables or figures to place. For Tasks without □, write the gist per label and the tables to place
    + The depth follows the kickoff answer. Even after presenting the basic depth, if the user asks to deepen only specific sections or modules, add just that range to the deep table
    + Each time you present it, end the reply with a one-line option asking "whether to go further down to the □ heading and ❍ gist level for a specific section or module"
- Judgment statements carry over unchanged as □ headings of the manuscripts. Apply the writing norms already at this stage. Follow the style of sentence-type □, short sentences with nominal endings, the notation of the key wording dictionary, and the □ limit in the line-limit table of content-models.md
    + Keep design language such as stage names and differentiation points only in the side columns of the table
    + Apply the Reader-Perspective Writing section from this stage on. `check tone` and the in-depth review judge only the manuscripts. A supplier-view sentence approved at this stage becomes a □ heading as is
- Write the one-line storyline and section messages as sentences that end with the outcomes the client obtains. The definition of outcomes, how to specify them, and what to rewrite are in the Proposal Strategy section
    + The message of the Implementation Strategy section bundles the values the strategies secure into a sentence that qualifies the final result. Examples are "차별성, 혜택, 실현가능성을 갖춘 OO 기본계획 수립" (developing an OO master plan with distinctiveness, benefits, and feasibility) and "전문성과 실효성을 확보한 진흥전략 및 실행계획 수립" (developing a promotion strategy and action plan with expertise and effectiveness)
- An implementation strategy judgment statement puts in one sentence the means (a design principle or execution method) and the risk that means resolves or the value it secures
    + For example, "RAG 기술을 적용하여 시스템을 설계" (design the system by applying RAG) becomes "답변마다 근거 문서를 제시하는 검색 구조로 생성형AI 오답의 불신을 해소" (remove distrust of generative AI wrong answers with a retrieval structure that presents source documents for every answer). The latter has a principle (presenting evidence) and a risk it resolves (distrust of wrong answers)
    + A means that stops at an activity name (diagnosis, pilot application, advisory committee operation) repeats the Module or the implementation structure. If the means is a design principle for the final results, put the principle in the means position. If the means is an execution activity, write the design of the activity (composition criteria, target, timing). For example, "자문위원회를 운영" (operate an advisory committee) becomes "기술 특성별 분과 위원회 구성으로 지표의 분야별 타당성을 확보" (secure field-specific validity of indicators by forming subcommittees by technical characteristic)
    + Sentences that declare when a work product is complete, such as "N년까지 OO 확정" (finalize OO by year N) and "최종보고 즉시 현업 적용" (apply in the field right after the final report), are schedule plans set by the author. Their place is the schedule chart
    + Submission deadlines, compliance duties, and constraints set by institutions or the RFP are premises for all bidders. Write the judgment statement as a specialized measure that achieves the premise or a measure added on top of it. For example, "부처 대응일정 준수" (meet the ministry's response schedule) becomes "대상사업별 근거자료 선행 정리로 부처 평가 일정 내 대응을 확보" (secure a response within the ministry's evaluation schedule by organizing evidence per target program in advance), and "보안 규정 준수" (comply with security rules) becomes "자료 등급별 처리 경로 분리로 국가 망 보안체계 안에서 생성형AI를 활용" (use generative AI within the national network security system by separating processing paths per data grade). In the latter sentences the means (organizing evidence in advance, separating processing paths) remains even after removing the goal (response within the schedule, national network security system)
    + Put timing-aware design on the means side. For example, express linkage with the client's schedule as a property of the method, as in "[기관명]의 기획 일정에 맞춘 시범 적용으로 현업 문서에서 검증한 활용 방안을 확보" (secure use cases verified on working documents through pilot application aligned with [agency name]'s planning schedule)
- The subject of Features and Strengths and Background judgment statements follows the role of the section
    + A Features and Strengths judgment statement is where the proposer's held facts are written. The subject is the proposer. It ends with a held fact
    + A Background judgment statement describes the circumstances of the client and its higher-level environment. The subject is an actor or phenomenon of the client or the higher-level environment
- Before presenting, self-check the items below. Fix rows that deviate before presenting
    + Background judgment statements narrow from the macro environment to the client's internal circumstances (recommended)
    + For each risk factor in the derivation table of the proposal strategy file, a strategy that answers it exists in the implementation strategy table
    + Implementation strategy judgment statements do not repeat Module names and activities. If the module overview table conveys the same content after deleting the strategy table, it is a repetition
    + Each differentiation point of the proposal strategy file has a Features and Strengths judgment statement and an implementation strategy judgment statement. Strengths absent from the strategy file are absent from the judgment statements
    + For each underlying-need hypothesis, a Module or Task that answers it exists in the execution part table
    + The value column of the implementation strategy table pairs each row with the risk it resolves. No row holds only a value word
    + The outcomes in the one-line storyline and section messages are specified by target, time, and state. No sentence ends with the submission of work products
    + The implementation strategy judgment statement column has no declaration of completion timing (a sentence that something finishes by a year or reporting point). The judgment statement alone reveals the way of working
    + After removing RFP task content and institutional duties from implementation strategy judgment statements, a specialized measure remains
    + The section message table includes every row of original sections in the section ledger. Module and Task names are identical to the module overview table
- Present in one turn. Deliver 02_섹션대장.md, 02_모듈총괄표.md, and 02_스토리라인.md through the file delivery feature (Chat Replies section). The user reviews the files and instructs revisions
    + Also state in the same turn the long-table handling applied to the module overview table. If the user picks another handling, replace the directive line
    + State at most three items for confirmation. These items narrow what the user reviews. For example, "whether to see the second point of Background C as an audit finding or as a new system"
- Reflect revision requests in 02_스토리라인.md. If the names, order, or number of Modules and Tasks change, update the module overview table, the section ledger, and the placement section column of the requirement table together. Rerun `ledger` and `check rfp` after the update
    + Re-present by delivering the changed files again. The reply states only the position (section, order) of the changed rows
- When the user approves, write the date and scope on the `(Approval)` line at the top of the file. For example `- (Approval) YYYY-MM-DD 기본 깊이 전체, Module 2는 심화` (approved YYYY-MM-DD, basic depth for all, deep for Module 2)
- Change rules after approval
    + Changing the meaning of, adding, deleting, or reordering judgment statements needs user reconfirmation. Reflect in 02_스토리라인.md first, then in the manuscripts
    + Notation polishing with the same meaning, such as fitting character limits or replacing vocabulary flagged by `check tone`, is discretionary. Reflect it in 02_스토리라인.md with the same notation. Mention it in one line in the completion report of that step
    + Renaming Modules and Tasks after approval changes the source of the tone verdict whitelist. Run `check tone --reset-whitelist` only on the user's instruction
- The (Underlying need response) and (Section boundary) items of the in-depth review are checked by comparing the manuscripts with 02_스토리라인.md

## Writing Norms

### Manuscript Hierarchy

- Apply the table below to the notation of levels, tables, figures, footnotes, superscripts and subscripts, and directive lines

| Markdown | Typeset result | Use |
|----------|----------------|-----|
| `# title` | Ⅰ. title band (new page) | Chapter |
| `## title` | 1. title | Section |
| `### title` | 가. title | Subsection. Only when the section is long |
| `#### title` | 1) title | Item. Rarely |
| `Module 1. title` | Module band | Module |
| `Task 1-1. title` or `Step 1. title` | Task band | Task |
| `□ title` | □ point (bold) | A point within a section |
| `- text` | ○ text | One claim under a point. Under Module and Task bands, a label line |
| `    + evidence` | - evidence | Evidence that supports the ❍ claim right above. Under a label line, the content of that label |
| `        + detail` | · detail | Elaboration or detailed items of the evidence |
| `※ note` | ※ note | A note on the preceding item |
| `- (subheading) text`, `    + (subheading) evidence` | (subheading) text | Bracketed subheading. A noun phrase of 4-8 Korean characters in parentheses at the start of a ❍ or hyphen line. A marker that shows the name of a listed item before its text. The criteria for using it are in the Bracketed Subheadings section. Bracketed subheadings used as a fixed set, such as (목적), (분석 대상), (산출물) in Task descriptions, are called labels |
| `<표> title` followed by a pipe table | <title> | Unnumbered caption (proposal convention). Setting caption_prefix to "{c}-" in the profile gives automatic numbering <표 1-1> |
| `![caption](path)` | [caption] | Figure. Placed inside a transparent table. The source goes in a transparent row below the figure, and the caption goes below the transparent table |
| `[^1]` | Footnote | Source of evidence in the body |
| `^superscript^`, `<sup>up</sup>`, `<sub>down</sub>` | Superscript and subscript | For units and symbols |
| `(폭: group name)` or `(폭: 1,3,2)` | Table width directive | Between caption and table. Unifies the widths of tables with the same layout or sets ratios |
| `(삽입: 모듈총괄표)` | Module overview table | Inserts the table of 02_모듈총괄표.md at this point. Once in the whole manuscript set |
| `(장표: engine)` or `(장표: split N)` | Long-table directive | Between caption and table. How to handle a table that runs past one page. Written after the user chooses |

- SKILL.md and the reference files call levels by their manuscript notation (□, ❍, hyphen, ․, ※). The symbols in the typeset result are set by the bullet definitions of the skeleton
- build assigns heading numbers. Manuscript headings hold only the title
- Do not use code block fences (three backticks) in manuscripts. `check tone` flags them as FAIL. Fences in reference file examples mark the extent of the example
- The `(단위: )` (unit) line goes between caption and table. Give it only to numeric tables
- The source line `※ 출처: ` or `출처: ` goes right after tables and figures. Give it only to tables of external data and external figures
- Sources of body text are `[^n]` footnotes. A source line placed under a paragraph moves into a footnote of the preceding paragraph at typesetting
    + Keep footnote labels unique within one manuscript file. build separates labels per file, so the same number in another file is allowed
    + Do not attach footnotes to a ※ note line right after a table or figure. This line is typeset as the bottom row of the table and cannot hold a footnote. Put the source on a `※ 출처:` line
- The cell value `^` merges vertically with the cell above. `<` merges horizontally with the cell to the left. A line break in a cell is `<br>`. A line with only `---` is a page break
- When a cell holds two or more items, list each item with `◦` and `<br>` in every table (`◦ item<br>◦ item`). Columns with bullets are left-aligned at typesetting
- Set column alignment per table with alignment markers in the separator row while writing the manuscript. The basis is the meaning of the column (year 2005 goes center, amount 2,005 goes right)
    + Quantity columns (amounts, counts, ratios, durations, scores) take `---:` (right) so that digits are easy to compare
    + Identifier columns (years, year-months, dates, serial numbers, numbers, period ranges, codes) and short text columns take `:---:` (center)
    + Columns with bullets, line breaks, or long text (over 10 Korean or 20 half-width characters) take `:---` (left)
    + (Marker example) The separator row of the track record table `| 연번 | 과업명 | 발주처 | 기간 | 금액(천원) |` is `|:---:|:---|:---:|:---:|---:|`
- Columns without a marker take the default alignment (columns with bullets, line breaks, or long text go left, all other columns go center, number columns included). A table without quantity columns may omit markers because the default matches the criteria above

### Style of □ Headings

- Levels at subsection (가.) and above are keyword noun phrases. Sentence-type messages sit at the □ level and below
- For □, choose between keyword type and sentence type (a one-line message with a nominal ending) to fit the character of the section. Keep one type within the same subsection. For a section without subsections, keep one type per section
    + Argument sections (Background, Necessity, Implications, Implementation Strategy, Features and Strengths) use the sentence type. For example "정부는 공공부문 AI 도입의 실행력 제고를 위한 제도적 여건을 마련" (the government prepares institutional conditions to strengthen execution of public sector AI adoption)
    + Descriptive sections (engagement purpose and scope, implementation process, current state summary, list of laws, implementation structure, schedule) use the keyword type. For example "과업 범위", "정책동향", "수행 조직"
- Attach bracketed subheadings only to ❍ and hyphen lines
- A □ paragraph is typeset with automatic bullet alignment (hanging indent 0). The second line aligns with the text start of the first line. ❍ and hyphen use the same alignment. ․ and ※ write the symbol as body text. The skeleton's hanging indent handles alignment
- Character limits per level follow the line-limit table in the references/content-models.md Volume Units section. Resolve an overflowing sentence by splitting it and adding a lower level, or by converting to a table. `check volume` warns on overruns
- Put at least one ❍ under each □ (the ❍ lower bound for the original part is in the Volume Units section). □ is the head of a paragraph. A □ without ❍ is the same defect as markdown with only headings. Place tables and figures after that ❍
    + Putting only a table right under □ is also a defect. Place one ❍ holding the gist of the table before the table
    + In all manuscripts including the common part (4, 6), `check volume` judges a lone □ and a table right after □ as FAIL
- ❍ is a claim that composes the point of □. A hyphen is evidence that supports that claim. If they do not pair, raise the hyphen to ❍ or delete it
- Module introductions and Tasks place label ❍ lines directly under the band without □. The structure is in the Task Description Standard section

### Bracketed Subheadings

- A bracketed subheading is a marker that shows the name of an item before its text. It is information only when it shows first a name that the start of the sentence cannot reveal
- Whether to attach it is judged by the relation the item has with its sibling items and its parent item. The same criteria apply to ❍ and hyphen lines
    + (Enumeration) A sibling group that unfolds what the parent item points to into named components one by one. Examples are grades, stages, target divisions, strategies, and evaluation elements. Attach bracketed subheadings to all siblings. The reader grasps the composition of the group from the names alone. If the same noun appears at the start of the sentence, move that noun into the bracketed subheading and delete it from the sentence
    + (Argument) A sibling group of facts, figures, cases, and quotations that support a parent claim. The sentence subject (organization name, system name, material name) already shows the character of the item. Write this group without bracketed subheadings
    + (Summary) A long argument item whose subject cannot stand in for the topic. Present the topic first as a bracketed subheading
- Attach to all siblings of an enumeration group. Attaching to only some makes the reader look for the difference between items with and without one. Lines that do not belong to the enumeration (the point of use of the whole group, a note) go at the end of the group without bracketed subheadings
- Put every bracketed subheading through the deletion test
    + If the line loses no information when the bracketed subheading is deleted, delete it
    + If a word of the bracketed subheading appears again in the text of the same line, it is a repetition. In an enumeration group, delete the same word from the text. On other lines, delete the bracketed subheading. For example, on the argument line "(활용 기준) OO위원회는 데이터 활용 기준을 개정" (the OO committee revises data use criteria), delete the bracketed subheading
    + If almost every line on a one-page stretch of manuscript has a bracketed subheading, check whether bracketed subheadings have slipped into argument groups
- Do not use meaningless bracketed subheadings such as (설명) and (내용), or repeat the same bracketed subheading
- Labels used as a fixed set ((목적), (분석 대상), (산출물) of Tasks, and so on) are outside this judgment. The composition and application of the sets follow the Task Types section under Common Standards in references/methods.md
- In the first example below, the hyphens under the first ❍ enumerate evaluation elements and take bracketed subheadings. The second ❍ and its hyphens argue for the judgment statement and are written without bracketed subheadings. The second example shows hyphens under ❍ that enumerate grades. `-` lines in the manuscript are typeset as ❍ and indented `+` lines as hyphens

```
□ 공공부문 AI 도입은 사례 확산 단계에서 성과 관리 단계로 전환
- [부처명]은 기관별 AI 도입 실적을 기관 성과평가 항목에 반영하도록 지침을 개정
    + (평가 대상) 행정업무 자동화, 대민 상담, 정책 분석 영역의 도입 사업
    + (평가 방식) 도입 건수에 더하여 업무시간 절감과 이용자 만족도를 측정
- [기관명]은 상담 챗봇의 운영 성과를 측정할 지표를 아직 보유하지 않음
    + 챗봇 운영 로그는 [연도]부터 누적 중
    + 이용자 만족도 조사는 챗봇 개시 이후 실시 이력이 없음
```

```
- 기관 보유 문서의 보안 등급마다 사용방식을 지정
    + (공개 등급) 보도자료와 공개 통계는 상용 서비스에서 처리
    + (내부 등급) 내부 보고서와 회의자료는 기관 전용 환경에서 처리
    + (민감 등급) 개인정보 포함 자료와 심사 자료는 온프레미스 환경에서만 처리
```

### Volume Units

- Volume is made from the number of units. Lower bounds, how to fill, and the order of additions when below a lower bound are in the references/content-models.md Volume Units section
- One □ has two or more ❍, two or more evidence lines (hyphen, ※), and 350 or more characters. One Task has one or more tables (an adopted source figure also counts) and 900 or more characters. `check volume` judges a shortage of ❍ and a Task without table or figure as FAIL. Shortages of evidence lines and characters are warnings. The source of the numbers is the constants in the settings part of proposal.py
- Count ranges are 2-4 □ within a section (##) or subsection (###) (group into subsections at 5 or more), 2-4 ❍ under a □, and 1-3 hyphens under a ❍ (convert to a table at 4 or more). The maximum of each range is the cap
- 3-6 Modules, and 2-6 Tasks per module. Do not announce the counts in the body
- 5-10 pages for Features and Strengths and 2-3 pages for the implementation structure (as a separate section) are the usual ranges reached by filling the composition units

### Task Description Standard

- The band is the title of a Module or Task. Directly under the band, place label ❍ lines without □
    + A □ under a Task band creates a level without siblings. The band name, the □, and (목적) also repeat the same content
    + The module introduction also places ❍ directly under the band. Modules and Tasks need the same structure so that the two purpose ❍ lines read as items of their own bands
- Put only one kind of item on one level
    + (❍) A label line that states an attribute of the Task. Label sets are in the Task Types section under Common Standards in methods.md
    + (Hyphen) The content of that label. Target lists, steps of the method, criteria, composition of work products, the conclusion a table states
    + Findings and table conclusions go on the hyphen level. On the ❍ level, the reader reads them as one more attribute of the Task
- The module introduction starts with two ❍ lines that describe the purpose and the implementation approach (keep subheadings uniform within the section). The definition of purpose is in the Purpose of Modules and Tasks section under Common Standards in methods.md. Then place the module overview table (모듈 개요표). The overview table uses the same layout for all modules. Unify widths with `(폭: 모듈개요)` under the caption. Overview tables of modules with different Task counts are unified among tables with the same number of columns
    + Columns are Tasks. Rows are by default the three rows 추진과정 (process), 활용자료 (materials used), and 산출물 (work products)
    + (추진과정) Write 2-4 execution steps within the Task in order as cell bullets (`◦ step<br>◦ step`). A one-line summary such as "조사 및 분석" (survey and analysis) does not count as steps
    + (활용자료) Write material names and counts by their real names
    + (산출물) Write work product names
    + In all three rows, list cell items as cell bullets when there are two or more. The criterion is the table cell rule in the Manuscript Hierarchy section
    + The steps, materials, and work products of the overview table match the label descriptions in the Task body below
- The references/methods.md Task Types section under Common Standards is the single source for Task types (analysis-centered, derivation-centered), label sets per type, the scope of the (산출물) label, and where to state submission timing
- One Task consists of the basic description and a filled table. The filled table goes under the label that the table supports. Before the table, state its conclusion first in one hyphen under that label. Details are in the content-models.md Task Description section
    + An analysis-centered Task reveals the current state of the target (literature and material surveys, interviews and questionnaires, diagnosis and process analysis, data analysis). Its filled tables are two or more tables fitted to the analysis method. Examples are named target list tables, preliminary survey result tables, comparison matrices, question area and item structure tables, diagnosis item tables, and current procedure step tables
    + A derivation-centered Task makes implications, strategies, initiatives, indicators, and models from analysis results. Its filled table is a criteria table or a work product draft table
- Give scale figures only to countable work. For uncountable work, specify target organization names, material names, and judgment criteria by their real names
- Fill preliminary survey table values with actual survey results (model knowledge if web search is not allowed). Unconfirmed cells get `[확인]`. Add the note `※ 사전조사 결과 (착수 후 [기관명] 자료로 갱신)` (preliminary survey results, to be updated with [agency name] data after kickoff) under the table (kept regardless of whether web search is allowed)
- `check density` judges the presence of (목적), a table or figure, work products, and grounds of concreteness. Grounds of concreteness are scale figures with units (건, 명, 회, 개소, 개, 종, 차, 주, 일, 개월, 기관, 과제, 표본, 응답) or a bracketed subheading holding one of 대상, 자료, 방법, 기준, 절차, 범위, 규모, 구성, 설계, 산정, 선정, 편성, 기록
    + If one Task has more than six figures, it warns to check whether figures were attached to uncountable work

### Argument Section Structure

- Features and Strengths repeats a structure of 3-4 capability claims. Each claim consists of a □ judgment statement, ❍ elaboration per field, hyphens with named past engagements, and a track record table, in that order. Sentence pattern examples for judgment statements are in content-models.md
- Implementation Strategy has 3-4 strategies. Each strategy consists of a □ judgment statement, 2-3 ❍, and a supporting table or figure, in that order. For each risk factor in the derivation table of the proposal strategy file, provide a strategy that answers it
    + The implementation strategy is the measure the proposer chose for effective execution of this engagement. Its validity conditions are specialization and differentiation (defined in the Proposal Strategy section). Evaluators read how well the measure fits the difficulties of the engagement and how it differs from competitors
    + Work that the RFP and institutions require, compliance with given constraints, and completion timing appear in every bidder's proposal. Put this content under engagement characteristics. Write specialized measures that fulfill duties and measures added on top of duties as strategies
    + What ❍ describes is the grounds for choosing the means (facts about the engagement's subjects), how the means is implemented (steps, tools, judgment criteria, participants, work products), and the value secured. Describe the execution content being implemented by task names without number references
    + A value ❍ describes how the resolved risk shows up in the engagement and its final results. For example "답변마다 근거 문서와 쪽 번호가 붙어 담당자가 원문과 대조 가능" (each answer carries the source document and page number, so staff can check it against the original). Do not write sentences that declare completion timing or attained states, or design labels such as "(도달 상태)"
    + A supporting table is a sample of the method. Examples are a step execution table (step, tool, activity, work product), a quality indicator table (step, indicator, formula, target level), a usage scenario table (situation, user, processing path, result), a subcommittee composition table (subcommittee, target field, member composition, review agenda), an execution procedure table (step, timing, participants, work product), and a diagnosis criteria table. Add the note `※ 참고용 예시 (미확정)` (example for reference, not finalized) under the sample table
    + Put timing judgment into the grounds and the method. Write the client's schedule (budget review, planning cycle, supervising agency review) as facts in a grounds ❍. Describe the method as linkage with that schedule. For example, the grounds "「국가재정법」상 중앙관서의 예산요구서 제출 기한은 매년 5월 31일" (under the National Finance Act, the deadline for central agencies' budget requests is May 31 each year) and the method "예산 요구 일정에 맞춘 사업 근거 확보" (securing program grounds in line with the budget request schedule)
- Regardless of chapter placement, the three argument sections split into the roles WHY, WHAT, and HOW. Background and Necessity is WHY (why the client needs this engagement now). Features and Strengths is WHAT (the proposer's held assets: methodology, track record, staff, tools, data). Implementation Strategy is HOW (by what principles and activities to overcome this engagement's difficulties: design principles for final results, execution activities, verification methods)
    + If the same methodology appears in two sections, Features and Strengths holds the fact of possession and a table of application records, and Implementation Strategy holds how it is applied in this engagement
    + The WWH framework (WHY, WHAT, HOW) is design language (Terms section)
- Features and Strengths expands the differentiation points of 00_제안전략서.md. Implementation Strategy expands the differentiation points and the implementation strategy derivation table. Expanding means writing out each row of the derivation table as □ judgment statements and ❍. The derivation table itself does not go into the manuscript (the reason is in the Proposal Strategy section). Do not create in the body new strengths absent from the strategy file. The strategy example table in content-models.md is a reference for sentence patterns

### Committees

- In the section holding the implementation structure content (decided in the Placement of the Implementation Structure section), place the implementation structure table (or a figure if a source figure is adopted), the committee operation (draft) table, and the member candidate (draft) table. Standard composition and sessions are in the methods.md Committee Design section
- For each committee, specify the name, composition, sessions and timing, agenda, and the point of use of review results (by work product name). Select member candidates from the advisory network in 회사자료.md or a list the user provides. Do not invent names. The size and column composition of the candidate pool table are in the methods.md Committee Design section
- Specify the scale and procedure of opinion-gathering tools (questionnaire, interview, FGI, Delphi, AHP, demand survey) in figures

### Work Product Drafts

- Present the final report table of contents (draft) as a three-column table (chapter, section composition, expected volume). Present one key work product as a draft filled with actual values. Add the note `참고용 예시 (미확정)` (example for reference, not finalized) to the draft
- Present priority calculation tables and evaluation tables with reproducible criteria and formulas

### Schedule Chart

- The schedule chart is one table that marks periods and points in time with symbol cells (`■`, `●`). The first column is Module, the second Task, and the following columns are months (1M, 2M) or weeks
    + A period cell with only `■` becomes a gray shaded cell at typesetting. Reporting meeting rows mark the point in time with `●`
    + Cells with only one symbol (`■`, `●`) do not count as bullets in the column alignment judgment. Month columns are typeset center-aligned. The same Module in the first column is merged vertically automatically

### Long Table Handling

- A table that runs past one page is subject to long-table handling. Tables are typeset with the 'treat as character' (글자처럼 취급) property. A table longer than the remaining page space is pushed whole to the next page, leaving blank space on the previous page. A table longer than one page has its overflow cut off. The `build` lint alerts with `[long table HITL]` on tables over 25 rows or estimated at 30 lines or more
    + The default handling is the user's answer to the kickoff questions, passed to build with `--long-table`. Long tables of 25 rows or fewer are outside the default handling. For such a table, write a directive line of the same handling between caption and table
    + Report to the user the list of tables the lint flagged and the handling applied. If another handling seems better for a table, ask the user to choose for that table only
    + `(장표: engine)` removes the 'treat as character' property. 한/글 splits the table by rows at the page boundary (the header row repeats). `(장표: split N)` physically divides the table into several tables of N rows (the header row is reattached, 12 if N is omitted)
    + The removal applies to the one table with the directive line. Other tables and bands keep 'treat as character'
    + A `(장표: engine)` table has different spacing from surrounding paragraphs than other tables, because the property is removed. For a table that needs the spacing kept, offer `(장표: split N)` as the alternative
    + If split positions are awkward, divide the table in the manuscript by logical units (module, field, year). Attach (1), (2) to the captions of the divided tables
    + For tables with a long-table directive, review split positions, blank space, bottom margin intrusion, and header format bleeding in the rendered PNGs
- `(장표: split N)` splits by row count. It does not consider row height or cell merges. This constraint causes defects in the cases below
    + In a table whose cells each hold several bullet lines, a piece can be taller than one page. Such a piece intrudes on the bottom margin and page number. For tables with two or more bullet lines per cell, lower N to 6-8
    + In a table with a vertically merged first column (`^`), the header format bleeds into body rows from the second split page on. The merged values of the first column are also lost. Do not apply split to such a table
    + Handle a table with a vertically merged first column by splitting into logical units (Module, field, year) and marking captions (1), (2). The alternative is removing the vertical merge and repeating the value in each row
    + The module overview table has a vertically merged first column by default. Its default split unit is the Module
    + If one table divided by logical unit again runs past one page, divide that unit once more into Task groups. Write the first column value in the first row of each divided table. Tables of 25 rows or fewer and estimated below 30 lines are outside the lint alert. Check such tables in the PNG
    + If there are more than six columns, ask the user about transposing or splitting the table (columns filled with symbol cells, as in the schedule chart, are excluded from the column count)

## Reader-Perspective Writing

- The readers of a proposal are the evaluators and the client's staff. Sentences describe the outcomes the reader obtains and their means. They do not carry the author's thinking process
- The judging principle is the deletion test. If the evaluator loses no information when a sentence is deleted, the sentence is aimed at the author or the document. Delete it or replace it with engagement content. The type list below covers frequent forms. Variants not on the list are judged by the same principle
- Exposing the thinking process means sentences that record how the author thought, such as "역산하여" (working backward), "검토한 결과 판단하여" (judged after review), "이를 바탕으로 도출한" (derived on this basis), and "배점을 고려하여 배치한" (placed in view of the points). They carry no information for the reader and read from the supplier's viewpoint
- How to describe what the client obtains depends on the character of the section. The definition of outcomes is in the Proposal Strategy section
    + Background and Necessity and the section messages describe what the client obtains as outcomes. Implementation Strategy describes the risks resolved and the values secured. Work products are described as means to reach those outcomes and values. Ending rules per judgment statement are in the Storyline Finalization section
    + The execution part (Module, Task) describes work products by their real names. The Purpose of Modules and Tasks section under Common Standards in methods.md is the single source for module and Task purposes. A purpose ends with what the work products and activities supply to the final results
    + If the purposes of the execution part continue only as lists of work product names, without the content and point of use of the work products, the proposal reads as one that ends with delivering a report. The client's outcomes are the content of the argument sections and section messages. Do not repeat them for every module and Task
- Rewrite descriptions of the judgment process as what the client obtains. In their place, the Background writes outcomes, Implementation Strategy writes principles and the risks resolved, and the execution part writes work products and activities and their points of use
    + (Implementation strategy) "자료 특성을 고려하여 변환 방식을 설계" (design the conversion method in view of material characteristics) → "표와 그림까지 추출하는 문서 변환으로 HWP 보고서의 수치 누락을 방지" (prevent missing figures in HWP reports with document conversion that also extracts tables and figures)
    + (Purpose of modules and Tasks) "현황을 조사하여 결과표를 작성" (survey the current state and write a result table) → "기관별 현황 조사로 개선 대상 선정의 근거를 확보" (secure the grounds for selecting improvement targets with a status survey per organization)
    + "최종보고 시점에서 역산하여 조사를 편성" (schedule the survey working backward from the final report) → "중간보고 시점까지 조사 결과표를 제출" (submit the survey result table by the interim report)
    + "RFP 요구항목을 검토하여 누락 없이 배치" (review RFP requirement items and place them without omission) → "세부 과업별 산출물과 제출 시점을 조견표로 제시" (present work products and submission timing per detailed task in a quick-reference table)
    + "자료 확보 가능성을 판단하여 조사 대상을 선정" (select survey targets by judging data availability) → "OO공단이 보유한 시설 대장, 점검 이력, 도면 목록과 공공 통계를 조사 대상으로 확정(착수 전 목록표 협의)" (finalize the facility registers, inspection histories, drawing lists, and public statistics held by the OO Corporation as survey targets, with the list agreed before kickoff)
- Write methods in a form the reader can check as well. Show procedures as steps and work products, judgments as criteria tables, and selections as target lists
- The central content of a sentence is the change that happens after the engagement. Write the change in the predicate as target and state. Do not express it by changing the subject
    + In bullet-style sentences, omitting the subject is natural. "상급 기관 심의의 보완 요구를 사전에 해소" (resolve the supplementation requests of the supervising agency's review in advance) reads without a subject as to who obtains what
    + Use timing when facts of the client's schedule (budget review, planning start, system enforcement) support the argument. Put completion timing of work products in the schedule chart and the work product submission plan table
    + When the same subject repeats, as in "발주처는 OO을 확보" (the client secures OO) and "발주처가 OO을 달성" (the client achieves OO), evaluators read the sentences as ones that fit any organization
- '발주처' (client) is used in SKILL.md, the reference files, and the design files (00_제안전략서.md, 02_스토리라인.md, and so on). Manuscripts use the organization's real name (defined in the Terms section)
    + Readers do not call their own organization '발주처'. When the manuscript calls the reader '발주처', the reader becomes a third party in the sentence. Even in a sentence whose predicate is filled with outcomes, this naming reveals that the text was written from the supplier's seat
    + With the real name, the same sentence reads as text about that organization's circumstances. The demand-side perspective is complete when the predicate content and the naming come together
    + For naming, use the organization name in the Agency Naming section of 00_제안전략서.md. Use abbreviations only in the notation the RFP or the organization's official letters use
    + Use the real name only where needed. If the real name repeats under the same □, omit the subject after the first occurrence
    + Replace `[기관명]` slots in templates and examples with the notation of the agency naming section. The same applies to committee, consultation, security, and note wording. For example, "(발주처 협의)" becomes "(OO공단 협의)", and "※ 위원은 발주처와 협의하여 확정" becomes "※ 위원은 OO공단과 협의하여 확정". Match the following particle to the final consonant of the real name. `check tone` flags unfilled slots as FAIL
    + Also write real organization names in the boxes of figures such as the implementation structure diagram
    + The column names "발주처" and "발주기관" in track record tables are conventional notation for the contract counterpart of past engagements. Leave them as they are
- `check tone` flags the supplier declarations below as FAIL. Delete the sentence and enter with content
    + (Count declaration) "3대 전략", "4개 Module", "5개 영역", "자료 6종". Present the items themselves as □, ❍, or list tables. Do not declare the count of your own structure and materials. The reader does the counting. Count declarations increase toward the later part of the manuscripts. Recheck them in module overview tables and Task descriptions. Quantities of external facts (23개 출연연, 시행계획 3건) are used, with values confirmed by source, only where the argument needs them
    + (RFP compliance declaration) "RFP 요구사항에 부합하도록", "제안요청서의 취지에 맞게", "과업지시서에 따라". Compliance shows through the original requirement wording written as is in Task names and descriptions
    + ("This engagement" declaration) "본 과업은", "본 과업 기간", "본 제안은", "본 연구에서는". Delete the self-reference and start with engagement content. If a reference is needed, use "과업" or the real project name. The same applies to table captions and cells
- `check tone` also flags the supplier statements below as FAIL
    + (Precondition statement) "발주처의 자료 협조를 전제로" (on the premise of the client's data cooperation), "OO가 확보되어야 수행 가능" (possible only if OO is secured). Such sentences read as passing execution risk to the client. Describe how to obtain materials as the proposer's procedure. Present client cooperation items as a table in the management part only when the RFP designates that section
    + (Exclusion declaration) "본 과업 범위에 포함하지 않음", "OO은 다루지 않음". Do not declare exclusions the client did not ask about. Reflect in the engagement scope only the exclusions the RFP states
    + (RFP as subject) "RFP가 제시한 기능 구분", "RFP가 요구한 절차". Making the RFP the subject of a sentence shows the reader that the author is reading a document. Describe the presented content itself ("교통, 환경, 안전의 기능 구분과 대응"). Mentioning the RFP document itself is allowed only in the header of the requirement quick-reference table
    + (Distinction from key wording) Key wording (engagement name, detailed task names, work product names, client terms) is used in its original notation in □, ❍, and Task names. `check wording` judges its appearance. The target of the RFP-as-subject verdict is sentences that point at the document, such as "RFP에 따라" and "RFP가 요구한"
    + (Table-pointing meta statement) "아래 표는 OO을 보인 예시", "다음 표는 OO 계획". Delete sentences that introduce a table. Place a ❍ holding the gist of the table before it. If it must be stated that the table is an "예시" (example) or "시안" (draft), add a ※ note under the table
    + (Ordinal enumeration) "첫째 OO, 둘째 OO, 셋째 OO", "첫 번째는", "하나는 OO, 다른 하나는 OO", "마지막으로". Prose enumeration markers duplicate the bullet-style hierarchy. Give each item one ❍. The hierarchy shows the order. Convert to a table at four or more items

## Self-Contained Writing

- Each section, □, and Task must read on its own where it stands. Text that makes the reader look up another page or the source literature is a defect
- Do not point to other sections, modules, or Tasks by number. Do not write "Task 1-1의 정책 요건 목록을", "Module 2의 산출물은", "앞 절에서", or "전술한 바와 같이". Restate the needed content in place ("정책 요건 목록의 항목을")
    + Number references send the reader to the original location. A change in one place calls for changes in every place that refers to it. They also make it hard to break down and reassemble the manuscripts
    + Number references are allowed only in table cells (module overview table, requirement quick-reference table, schedule chart, division of duties table, committee operation (draft) table). `check tone` flags number references on body lines as FAIL (the verdict name is cross reference)
- Describe links between stages by work product names. Put the name of the earlier stage's work product and how the later stage uses it in one sentence, as in "현황조사에서 확보한 기관별 현황표는 개선 대상 선정의 후보 목록" (the per-organization status table from the status survey is the candidate list for selecting improvement targets)
- For cited materials, write the concluding figure and the source in place. Do not defer with "별첨 참조" (see attachment) or "원문 참조" (see original)
- Use software design phrasing only where system architecture is explained. "입력이 되고", "입력 자료로 사용", "출력", "연결을 확보", "연계 구조", "매핑", and "인터페이스" qualify. Even in the execution plan of an informatization engagement, do not describe a Task's work products as the input of another Task. Write "활용 자료", "OO에 활용", or "대응표"
- Do not write materials and people's opinions as if machine-processed. "면담 결과를 입력하여 도출" (derived by inputting interview results) → "면담에서 확인한 의견을 과제 후보의 실행 가능성 판단에 반영" (reflect opinions confirmed in interviews in judging the feasibility of initiative candidates). Describe who reflects what where
- Do not write framework language and internal judgments in manuscripts. "과업의 답", "과업 방향", "전제조건", "수행 여건", "일정 정합", "근거 누적", "누락 없이 대응", "빠짐없이 배치", "대응 관계", "도달 상태", and "도달 시점" are the author's checking language. Present only the results to the reader. The last stage of the Background (A) states directly in a □ judgment statement what the engagement does, without a "과업 방향" label
- Do not write design language (defined in the Terms section) in manuscripts. Explanations such as "분석형, 조사형, 도출형, 지원형 Task", "Task 배치", "수행내용 구성", and "(2주 단위, 열 번호는 주차)" describe how the skill works and carry no information for the reader. How a table is composed is visible in the table

## Sentence Discipline

- One message per sentence. A short sentence in which subject and predicate have only one relation
- One sentence per level item. Do not join two sentences on one line with a period. Split the second sentence into a hyphen level or the next ❍. Do not put a period at the end of a line. `check tone` flags periods inside lines and at line ends on □, ❍, hyphen, and ※ lines as FAIL (table cells, footnotes, source lines, and captions are excluded)
    + When a ※ note holds two facts, wrap one in parentheses. For example "※ 사전조사 결과 (착수 후 OO공단 자료로 갱신)"
- 5W1H short sentences. A sentence holds at most one element each of who, what, when, where, why, and how. If two or more of an element overlap, split the sentence
    + For example "제안사는 의사결정 속도를 높이기 위해 착수 2주 내에 OO공단 보유 자료 목록을 확정" (to speed up decisions, the proposer finalizes the list of materials held by the OO Corporation within two weeks of kickoff): one each of who, why, when, and what
    + A compound sentence example "자료를 확보하고 대상을 선정하여 조사를 수행" (secure materials, select targets, and carry out the survey) → split into three sentences or three hyphens
- Do not write ungrammatical sentences. Check subject-predicate agreement (write "제안사는 OO을 확보". "제안사는 OO이 확보" is ungrammatical), missing objects ("OO을 분석": analyze what), and mismatch between the nominal ending and the preceding particle (write "OO을 검토" for "OO에 대해 검토"). If reading the manuscript aloud catches on a sentence, it is ungrammatical
- Nominal endings (-함, -임, -필요, -추진, -제시). No honorific or colloquial style. For unnatural endings, see the Sentence Ending Vocabulary section of lexicon.md
- A proposal is in formal written style. Colloquial style that looks professional is easily mistaken for formal style. `check tone` flags the markers below as FAIL
    + (Hedged endings) -듯, -듯함, -인 셈, -하는 편, -할 만함, -로 봄, -로 보임, -로 여겨짐. Markers that blur the verdict. End with "-로 판단", "-로 확인", or "-로 집계" together with grounds. Dependent nouns are flagged only in their spaced form. Endings in "개편", "재편", "데이터", and "센터" are excluded from the verdict
    + (Explanatory endings) -는데, -인데, -더라, -거든, -잖아. Split the sentence and end with a nominal form
    + (Colloquial contractions) -하는 게, -할 거, -한 걸, -하는 건. Contractions of "것이" and "것을". Convert to a nominal form
    + (Colloquial modifiers and adverbs) -식으로, -쪽으로, 일단, 약간, 좀, 꽤, 딱, 그냥, 나름. Delete or replace with figures and criteria
- Do not use the colloquial "것" ending. "남은 것", "해야 할 것", "과업의 포인트인 것", and "OO것임" are endings of online community colloquial style. `check tone` flags them as FAIL. Convert to nominal endings ("OO 잔존", "OO 필요", "OO이 과업의 핵심"). The verdict target is a "것" ending at the end of a line
- Do not join two predicates with connective endings (-으며, -하며, -이며, -하고) or conjunctive adverbs (그리고, 그러나, 그래서). Split the sentences. Express relations between sentences through the hierarchy
- Use commas only for lists of three or more items of the same category. Write a list of two as "A 및 B". "및" is the conventional notation of client official letters
    + Established names in a field keep their customary wording. For example, the BSC perspective name "학습과 성장"
    + "와" and "과" marking a relation between two nouns (사이, 간, 격차, 차이, 일치, 불일치, 연계, 연동, 정렬, 비교, 구분, 분리, 협력) stay. For example, "현행과 기준의 격차" and "성과지표와 성과목표의 연계"
    + "와" and "과" marking the partner of an action stay. For example, "OO공단과 공유", "사유와 함께 관리", "지역 대학과 공동 운영"
- Do not use em dashes, tildes, separator symbols (/, ·, →), or connecting hyphens (hyphens for ranges are allowed). A line break inside a table cell is `<br>`
- Do not use contrast constructions ("X가 아닌 Y", "단순한 X를 넘어 Y"). Describe Y directly
- For count declarations, apply the verdict in the Reader-Perspective Writing section
- Do not write sentences that describe the text itself or the writing process. Delete "본 제안서는", "앞서 언급한", and "정리하면". Sentences start with content
- Do not expose thinking framework names (MECE, pyramid, first principles, SCQA, SCR, WWH) or skill-operation vocabulary (배점 역산, 밀도, 섹션대장) in the body. "역산" exposes the calculation process even in a schedule context. Do not use it. Describe schedules by result and character, as in "체계적 일정 수립" and "효율적 일정 편성". Module and Task names are the substance of the engagement design. Write them in the manuscripts
- Use the conventional vocabulary by function in references/lexicon.md. Do not create colloquial or figurative words ("쓰임새", "얼개", "손질") as workarounds for banned words. When `check tone` flags them, replace them from the replacement table
- Do not use management loanwords (작업분해도, 마일스톤, 임계경로) or software design phrasing ("입력값", "인계"). Replace semi-colloquial words (포인트, 세팅, 케이스, 니즈, 픽스, 체크, 컨펌, 어필, 메리트) with the formal words of the lexicon.md replacement table
- Secure formality through vocabulary and endings. Do not imitate formality by piling up difficult Sino-Korean words. The vocabulary level is that of the client's official letters and higher-level plans
- Do not use expressions that suggest shortcomings in the client's policy or the RFP. Convert to positive statements
- Do not state the budget of the project you are bidding on in the body. Turn unconfirmed figures into `[확인]` or a survey task
- Recalculate ratios and totals in code. Do not use ratios whose numerator and denominator have different reference dates
- For English abbreviations, give the full name alongside on first use
- Do not use exaggerating modifiers (획기적, 혁신적, 선도적) or glue expressions (이러한 맥락에서)

## Common Part

- 원고/41_제안사일반현황.md, 61_수행조직.md, and 62_관리부문.md are templates that init places. Their content only gets `[확인]` substitution and track record selection. Replacing titles for a specified table of contents, reordering sections, and splitting files follow the Chapter Structure section
- The source of substitution values is 회사자료.md. Do not create company information absent from that file
- Track record tables include only engagements that meet the RFP's recognition requirements for track records (period, amount, field, form of evidence)
- The default composition of the project organization section (61) is the participating staff table and the division of duties table by module. The committee operation (draft) table and member candidate (draft) table of the template are kept or deleted according to the placement decision for the implementation structure. If the implementation structure is in another section, delete the □ committee operation block (❍, two tables, note) from 61 (leftover `[확인]` makes `check fill` FAIL). Write committee agendas with Task names and work product names from the module overview table
- For `[확인]` the user could not supply a value for, delete that row or item after user approval
- Compare the participation rate column (`참여율`) with the person-month calculation. `check fill` judges overruns above 100%
- The default post-delivery support period is 12 months. If the RFP specifies a period, replace the value in 62
- If the RFP requires specific items in the common part (safety and health, social value, shared growth cooperation), write only those sections anew

## Checks

| Verdict | Target | FAIL condition |
|---------|--------|----------------|
| Requirement placement | 01_요구항목표.md | A row with no placement section, an ID absent from the section ledger |
| Task density | 원고/5*.md | Any of (목적), table or figure, work products, or grounds of concreteness missing. No text under □ |
| Volume composition | All manuscripts (lower bounds for 3*, 5*) | Lone □, table right after □, fewer than two ❍ under □ (original), Task without table or figure (character count and evidence line count are warnings) |
| Wording | Key wording dictionary and all manuscripts | A key wording dictionary term appearing 0 times, one or more prohibited expressions. Prohibited expressions are the default list (가용가능, 할 수 있다, 할 수 있음, 고려하고 있, 검토할 예정, 노력하겠, 가능할 것으로, 필요시 검토) plus the items in the `금지 표현` section of the proposal strategy file |
| Tone and vocabulary | All manuscripts | Implying client policy shortcomings, criticizing client practice, correcting the RFP, internal logic vocabulary, instruction vocabulary leak, client as subject, leftover agency naming slot, management loanwords, semi-colloquial vocabulary, unconventional vocabulary, framework name exposure, count declaration, RFP compliance declaration, "this engagement" declaration, precondition statement, exclusion declaration, RFP as subject, table-pointing meta statement, ordinal enumeration, '것' ending, colloquial style (hedged endings, explanatory endings, contractions, colloquial adverbs), software design phrasing, framework language exposure, cross reference, N-kinds declaration, code block fence, period on hierarchy line (two sentences joined, period at line end) |
| Figure check | All manuscripts | A table's total row does not match the sum of its items |
| Common part substitution | 원고/4*.md, 6*.md | Leftover `[확인]`, participation rate above 100% |

- Warnings detect em dashes, compound sentences with connective endings, conjunctive adverbs, contrast constructions, meta statement markers, exposure of thinking framework names, mentions of the RFP, leftover '발주처' naming, superlative assertions, exaggerating modifiers, and level counts over the cap (`check volume` of the original part). They do not count toward the verdict. Check them in the manuscripts and fix
- The source of the judgment criteria is the constants and verdict lists in the settings part of scripts/proposal.py (FORBIDDEN_DEFAULT, TONE_FAIL, TONE_WARN, SENTENCE_WARN, VOLUME_*). If SKILL.md and the settings part disagree, the settings part rules
- The whitelist (Terms section) is collected automatically from the key wording dictionary of 00_제안전략서.md (RFP terms, proposal notation), the `RFP 용어` table of 00_진단서.md, and the Module and Task names of 02_모듈총괄표.md. Original RFP terms ("데이터 인터페이스 개선") and Module and Task names the user confirmed are masked from the tone verdict
    + It is fixed after step 2 is complete. The fixing conditions are that the module overview table exists and the dictionary has zero `[확인]`. The first `check tone` after the conditions are met fixes it in state.json. Before that, only masking of the collected terms applies. An unfixed state is reported as WARN
    + Adding or deleting terms in the whitelist sources after fixing is a source change FAIL
    + Korean terms shorter than four characters ("조사", "매핑") are excluded from masking. Masking short common nouns disables other verdicts such as "조사형". Uppercase English abbreviations (RFP, ISP) are collected even when short
    + Refix with `check tone --reset-whitelist` only when the user instructs a change to the dictionary or the module overview table
    + If vocabulary outside the whitelist is FAIL, replace it from the lexicon.md replacement table. Adding to the dictionary or renaming modules to avoid FAIL is a defect
- To handle a FAIL, check the flagged item in the manuscript and fix it. If it is a misjudgment of the verdict logic, record the reason in the final report
    + If only misjudged FAILs remain, no `check all` PASS record is created. Report the misjudged items and reasons to the user. After user approval, run `build --force`
- For manuscripts not written in Korean, skip the Korean-specific verdicts with `check all --skip`, then build
    + The Korean-specific verdicts are density (the (목적) label, the word 산출물, Korean count units), wording (key wording dictionary and Korean prohibited expressions), tone (Korean vocabulary and ending rules), and numbers (detects total rows and ratio columns by Korean words)
    + The language-neutral verdicts are rfp, volume, and fill. The FAIL conditions of volume are structural. Its character count and line cap warnings are calibrated on Korean glyph widths, so for manuscripts in another language they are for reference only
    + The form is `check all workspace --skip density,wording,tone,numbers --skip-reason "English manuscripts"`. The skipped checks and the reason are recorded in the skipped checks section of 05_점검기록.md and in state.json. build accepts this PASS record and reports the skipped checks
    + There is no language detection. The manuscript language and the checks to skip are settled by the kickoff answers
    + Do not use it to get past FAILs in Korean manuscripts. Misjudgments in Korean manuscripts follow the misjudged FAIL procedure above
- `[확인]` in the original part (3*, 5*) is a temporary marker during writing. Do not leave it in the delivered file
    + `check fill` prints the leftover locations as warnings. At step 5, bundle the leftover list into one turn and ask the user
    + When the user gives values, fill them in. For cells whose values could not be secured, delete the row or column after user approval
- Check results are recorded in 05_점검기록.md and state.json. What a reply states is set in the Chat Replies section
    + Records of the self-review, in-depth review, render review, and discretionary adjustments go under the `## 수동 기록` (manual records) section of 05_점검기록.md. check all rewrites only the automatic verdict results above it. This section and everything below it are preserved

### In-Depth Review

- Defects that code cannot catch are found through a review from the evaluator's perspective. The in-depth review is a default step 5 procedure carried out regardless of the execution environment. The review intensity is set by the section's attributed points

| Attributed points | Self-review (default) | Independent review (with user approval) |
|---|---|---|
| 10 or more | Once | Repeated. Until no defects remain or three times |
| 5 or more and below 10 | Once | Once |
| Below 5 | Once | Not performed |

- The model carries out the self-review directly in the same session. Do not skip it even in environments without subagents or new sessions. Compare the manuscripts, reread from the files, with the review items below one by one
- The independent review (new session, separate instructions, subagent) is carried out only in environments that support it, after asking the user. Bundle the question in the same turn as the self-review result report
    + (Advantage) A reviewer who does not know the writing process finds defects the author repeatedly misses
    + (Disadvantage) The reviewer does not know the proposal strategy or what the user confirmed. This can produce misjudged findings. Time and token use also increase
    + On approval, give the reviewer 00_제안전략서.md, 02_스토리라인.md, and the review items together
- Limit the findings of one round to the five with the greatest impact. More findings make fixes create new defects
- Do not repeat findings on items the code already handled. Reject a reviewer's misjudged finding with grounds
- The review items consist of defect types the code checks cannot judge
    + (Figure integrity) Check that the numerator and denominator of a ratio share the same reference date. Check whether figures that point to the same fact exist with two values
    + (Source reliability) Check that every cited figure comes from material that can be submitted as an attachment. Replace paid reports and news figures of unknown origin with public statistics
    + (Logical leaps) Check that intermediate steps exist between materials and conclusions. Check whether two facts under different conditions were equated
    + (Underlying need response) Check that a Task answers each underlying-need hypothesis in the proposal strategy file
    + (Discrimination) Check whether a competitor could write the same sentence. Check that grounds only the proposer can cite (track record, data, staff) are attached
    + (Section boundary) Check that the □ of each section reads in that section's role (Background is WHY, Features and Strengths is WHAT, Implementation Strategy is HOW). Move a □ that reads in another section's role to that section
    + (Strategy pairing) Check that each implementation strategy □ reads with one risk factor from the derivation table and one value secured. Rewrite a □ that has only an activity name or reads as a generic operating means, with a principle or activity design and a risk. Rewrite as a specialized measure a □ that leaves no measure after removing RFP task content and institutional duties
    + (Leaked derivation table) Check whether the manuscript holds a table that lists risk factors or values secured by strategy. The fix is in the Failure Patterns section
    + (Reader perspective) Check whether sentences state the author's thinking process or work procedure. Convert such sentences into descriptions of the outcomes the reader obtains. Also check whether argument sections end with the submission of work products, and whether module and Task purposes lack the results and points of use of work products and activities
    + (Bracketed subheadings) Check for bracketed subheadings attached to argument groups, bracketed subheadings that repeat words of the text, and enumeration groups with bracketed subheadings on only some items. The criteria are in the Bracketed Subheadings section
- Rerun `check all` after fixing manuscript defects. Rerun it after bulk style fixes as well

## Reusing Source Images

- If submitted originals exist (RFP, client public materials, pdf, hwpx, pptx, docx submitted by the user), extract insertion candidates with `extract_images.py`. The output is img_NNNN.png and manifest.json (size, ratio, type photo, logo, map, diagram, source page)
- Adoption targets are the client's project concept diagrams and implementation structure diagrams, field photos and final result screens from similar track records, charts, structure and architecture diagrams, maps, and company and agency logos. Inserting original charts and structure diagrams in body-text documents is common practice
- Non-adoption targets are images capturing tables (rebuild them as tables), bullet and background fragments, images whose low resolution breaks in print, and diagrams of other proposers
- Insert only after user confirmation. The model presents a candidate list (file, source page, type, insertion point, draft caption) based on the manifest and the source pages. Place only the items the user adopts in the manuscripts
- Insert in the manuscript as `![caption](path)`. For a figure taken from outside, put `※ 출처: 기관명(연도), 자료명` (source: organization (year), material name) on the next line. Size, placement, and caption follow the typesetter's figure rules as is (width 140mm for landscape, width 90mm for near-square, height 110mm for portrait, centered in a transparent table, source below the figure, caption below the transparent table)
- Relative paths resolve from the location of 납품/_합본.md, which build creates. Write figures in the workspace as a relative path that points to the same file from both 원고/ and 납품/ (for example `../그림/파일.png`) or as an absolute path
- If the build log shows `WARN: image not found`, that figure and its caption are missing from the delivered file. Fix the path and typeset again
- State the source even when using a figure from the RFP body as is. The proposer confirms the copyright and usage rights of source images
- Diagrams in decks (process and structure diagrams drawn with shapes and text boxes) are not extracted as embedded images. Capture the region of the reference PDF with the `figure` command. The user confirmation rule is the same. The procedure is in the deck-conversion.md Diagram Capture section
- If there are many candidates, raise the lower bounds with `--min-px` and `--min-kb`. Logos are inserted small, so keep the lower bound for logo extraction low. Select logo candidates from the logo type

## Typesetting

- The default skeleton (workspace/_양식/proposal.hwpx) is an empty template that defines only styles. Table width, column alignment, header background, unit and source rows, caption attachment, figure placement, and vertical merges follow the norms of the typesetter (scripts/hwpx_report.py) as is
    + The sources are the SKELETON_* definitions in the settings part of proposal.py and an empty new document of python-hwpx. init and build regenerate it with the same content on every run
    + Change the template by editing the settings part or by setting `build --skeleton`. Direct edits to the _양식 file are overwritten by the next build
    + The typeface is the single NanumBarunGothic (나눔바른고딕) family. Differences in importance between levels are expressed by font size and weight
    + Color applies only to bands. The theme is navy (default) or mono (black and gray), chosen by the kickoff answer. Color values are in `THEMES` in the settings part of proposal.py
    + Table format, regardless of theme, is black 0.15mm rules and a gray (#D9D9D9) header. Period cells of the schedule chart use the same gray. The reason is to keep the conventional format of editors who fix tables in 한/글
    + Level symbols are □, ○, hyphen, ·, and ※. The basis is the special symbols (□, ○, -, ·) that Article 2 of 「행정업무의 운영 및 혁신에 관한 규정 시행규칙」 (Enforcement Rule of the Regulation on the Operation and Innovation of Administrative Affairs) allows for item marking. Table cell bullets are ·
- docx is generated from the same manuscripts, the same settings definitions, and the same typesetting judgments as hwpx
    + Style values (font, size, weight, alignment, margins, line spacing), level symbols, bands, tables (column widths, rules, header fill, merges, cell margins), captions, figures, footnotes, headers, page numbers, and the table of contents are the same as hwpx
    + Level symbols are shown with Word's bullet feature. Line spacing converts 한/글 percentage values to fixed spacing. Space width matches the 한/글 standard (half the font size)
    + When both formats are produced, build compares the character order of paragraphs. `WARN: hwpx and docx paragraph text mismatch` signals a defect in the typesetting code. Report it to the user. Removing the WARN by editing manuscripts is a defect
    + 한/글 and Word calculate line breaks and page breaks differently, so some line-end positions and page boundaries differ. Table of contents page numbers are computed from each format's own rendering
- Table width is computed per table by the typesetter's rules. The cap is the body width minus the level indent, and the floor is 50% of the cap
    + If every column fits on one line, each column gets its one-line width. If the table is narrower than the floor, it is scaled up proportionally
    + If not everything fits on one line, the table width is set to the cap. Short columns get their one-line width first. Long columns share the remaining width evenly
    + Every column is guaranteed a width that does not break words
- The model specifies width unification for tables with a repeated layout in the manuscript. Whether tables share a layout is a document design judgment
    + The directive line goes between caption and table. A group name such as `(폭: 실적)` unifies the tables of the same group at the largest needed width in the group. `(폭: 1,3,2)` distributes the cap by ratio. `(폭: 1,3,2, 80%)` distributes 80% of the cap by ratio
    + Usual targets for unification are module overview tables (all modules), track record tables of the principal investigator and participating staff, committee operation (draft) tables, and survey target list tables
    + `build --unify auto` is an auxiliary means that automatically groups tables with the same header or first-column labels. The default is manual
    + Check every width-specified table in the rendered PNGs. Check for squeezed columns, large empty widths, and mismatches among tables in a group. If a defect shows, remove the directive or change the ratio values and retypeset (a table without a directive returns to per-table calculation)
- Elements specific to the proposal are Roman chapter numbers, Arabic section numbers, 가나다 subsections, bands (chapter, Module, Task), and table width directives
    + A band is a one-row table of a number cell, an empty cell, and a title cell. Differences in importance between bands are expressed by the weight of the number cell. A chapter has a white Roman numeral in a dark filled cell, a Module a dark label in a light filled cell, and a Task a dark label in a cell with a dark border
    + Title text is bold 20pt for chapters, 13.5pt for Modules, and 12pt for Tasks. The number cells of Modules and Tasks have the same width, so the title start lines of the two bands align
    + Captions are unnumbered by default. Tables use <title> and figures use [title]. Band tables are excluded from the number count (numberingType NONE). With automatic numbering on, numbers restart from 1 in each chapter
    + Spacing before and after bands and keep-with-next are handled by the band position style. Cell widths, colors, font sizes, and heights are in `BAND_STYLE` in the settings part of proposal.py
- A divider page is a page placed before the body of each chapter. It places the chapter number and title as a large chapter band slightly above the middle of the page. The body starts from the first section on the next page
    + Divider pages show no header, footer, or page number. They are included in the page count
    + hwpx achieves this with the hide feature of 한/글, docx with a different first page per section
    + Band size and position are in `BAND_STYLE["divider"]` and `DIVIDER_TOP_LINES` in the settings part of proposal.py
- Delivered hwpx and docx use NanumBarunGothic regular and bold. Both weights include the KS X 1001 Hanja set. On PCs without the font, 한/글 and Word show substitute fonts, and line ends and page boundaries change
- Record font installation guidance in the final report of the first delivery with the items below. Skip it after the user says installation is done
    + (Source) Nanum fonts from the Naver Hangeul distribution site (hangeul.naver.com). The required fonts are NanumBarunGothic regular and bold
    + (How to install) On Windows, install for all users from the right-click menu of the font file. On macOS, open the font file and install it with Font Book
    + (Confirmation) Close 한/글 and Word completely and restart them. Done when the font name of the delivered file's body shows NanumBarunGothic
    + (Sending outside) If it is unknown whether the recipient's PC has the font, send along a PDF saved from 한/글 or Word
- build's `--toc` (table of contents) and `--page-number` (page numbers) are separate options. Both are OFF by default. The defaults for the pre-diagnosis report are in the references/report.md Typesetting section
    + Turn them on only when the user asked or the RFP writing rules explicitly require them. Record the reason for turning them on (kickoff answer or RFP writing rule) in the writing rules row of basic project conditions in 00_제안전략서.md. For the pre-diagnosis report, record it in the basic report information table of 00_진단서.md, and for the planning report in the basic information table of 00_기획설계.md
    + If the RFP requires only page numbers, turn on only `--page-number`
    + With `--toc` on, check after rendering the count of page numbers filled in the table of contents. If the approximate renderer cannot find some chapter titles, their page numbers stay blank. Page numbers are filled only when `--page-number` is also on. Compare `TOC page numbers filled n/m` in the build log with the PNG of the table of contents page
    + For a proposal, if even one entry is missing, turn off the table of contents and retypeset. If the table of contents must stay, state in the final report that the table of contents needs updating in 한/글. Handling for the pre-diagnosis report and the planning report is in the report.md Typesetting section
- Extract a client template with `skeleton template.hwpx skeleton.hwpx`. Fill style names into the null roles of the draft profile, then run `build --profile profile.json --skeleton skeleton.hwpx`

### Document Labels

- Fixed strings printed into documents, manuscript notation, docx language tags, and delivered file names are labels. The default labels produce Korean documents (목  차, 표 목차, <표 1-1>, [그림 1-1], 가., 제1장, 납품/제안서)
- For a document in another language, set a label file (JSON) with `build --labels file` or `check --labels file`. A path set for a workspace is recorded in state.json, and later check and build runs use the same labels. `--labels none` clears the record
- The key groups are formats (heading number formats), letters (the 가나다 level), toc (table of contents titles), caption (caption word and brackets, docx number field), notation (added manuscript notation), language (docx language tags), and output (delivered file names). The key table, defaults, and an English example are in references/labels.md
- A file may hold only some keys. Missing keys keep the default. Unknown keys and format errors stop build and check with ERROR
- notation only adds tokens. Korean default notation such as `출처:`, `<표>`, and `(단위: )` stays recognized
- Roman chapter numbers and level symbols do not depend on language and are not labels
- The default docx language tags are Latin en-US and East Asian ko-KR. With Latin ko-KR, LibreOffice breaks English words and numbers mid-token
- For manuscripts not written in Korean, skip the Korean-specific checks with `check all --skip` (Checks section)

## Render Review

- After rendering, review the items below on every page PNG
    + Level symbols and indent steps, band positions, and spacing before and after bands
    + Centered tables, consistent column alignment, header background, caption position, unit row position, source row position, and appropriate merging of label columns
    + Figure size and caption, clipped and overlapping text
    + Spacing before and after tables and figures. It is a defect if the next numbered title (chapter band, section 1., subsection 가., item 1)), a Module or Task band, □, or ❍ touches the bottom border of a table or figure, or if the table overlaps the paragraph above. Check for each table that it has the same spacing as other tables
    + Spacing defects occur mainly after `(장표: engine)` tables. When found, replace the directive line of that table with `(장표: split N)` and retypeset. Then check the PNG again
    + Tables separated from captions at page boundaries, split positions and header row repetition of tables that run past one page, blank pages right after a section starts, and bands, titles, and □ left alone at the end of a page
- After the item review, do one free review without a list. Look together at left alignment lines across levels, the balance between table width and body width, consistency of margins, visual weight within a page, and differences in font size and weight across levels
- If the cause is the manuscript, fix the manuscript. If the cause is a norm, fix the settings part of proposal.py. With three or more defects of the same kind, stop individual fixes and adjust the norm in the settings part of proposal.py

### Discretionary Adjustment of Defects Outside the Rules

- The review items list only frequent defects. Treat a point outside the rules as a defect if a practitioner seeing it for the first time finds it odd
- If a rendering typeset by the rules looks bad, choose what looks better
- Fix sentences that read oddly even if they fall outside Sentence Discipline. The criterion is whether an evaluator stops while reading
- The means of adjustment are editing manuscripts, changing the form of tables and figures, splitting and merging □, and adjusting settings constants. Apply an adjustment to the whole level
- Record each discretionary change in the final report in one line stating what changed and why
- rhwp and H2Orestart are approximate renderers. `render` applies display corrections only to the review copy. Inserting characters for table cell bullets (·, -) applies only to the soffice path (rhwp draws cell bullets directly, and H2Orestart does not draw them). On both paths the normal state is one bullet visible per item in the review PNG. The delivered hwpx is unchanged (한/글 shows style bullets)
    + With automatic caption numbering, missing numbers (`<표 1- >`), page numbers per section, font substitution, and header row repetition display of `(장표: engine)` tables are excluded from the verdict
    + Known approximate displays of rhwp are also excluded from the verdict. They are narrow display of Latin text in Nanum fonts, lost spacing after ※, footnote separators overlapping body text, line breaks in the middle of words, keep-with-next settings not being applied (titles and □ left alone at page end), the last body line overlapping the page number when page numbers are on, and `(장표: engine)` tables intruding on the bottom margin
    + Cross-check layout defects seen only in rhwp with `render --engine soffice --outdir folder`. `--outdir` preserves the PDF rhwp produced. If soffice shows it correctly, judge it an approximate display. Approximate displays are not a reason to edit manuscripts (manual page breaks change the actual layout in 한/글)
    + Known approximate displays of H2Orestart are also excluded from the verdict. They are missing captions and ignored cell padding
    + Differences in LibreOffice's docx display are also excluded from the verdict. They are automatic spacing between Korean and numbers (it does not read docx's setting that turns off automatic spacing) and header rows not repeating in tables split at page boundaries
    + Final confirmation is the user's check in 한/글 (in Word for docx). State this in one line in the final report

### PDF Copy

- Whether to include a PDF is set by the answer to the kickoff questions. Not included by default
- Output the review PDF and PNGs outside the delivery folder with `render --outdir`. Output the cross-check rendering to a different folder
- If the user chose a PDF, copy the PDF of the last render for each format into the delivery folder and deliver it with the hwpx or docx
- (Approximate rendering notice) Give the following in the kickoff questions and in the final report of a delivery that includes the PDF
    + The PDF is drawn by an approximate renderer, so it may look different from 한/글 and Word
    + A PDF of an hwpx document is likely to contain display defects in line breaks, spacing, and page breaks
    + Save a PDF for submission from 한/글 or Word

## Failure Patterns

- (Late renderer) Trying to secure a renderer for the first time at step 6. Context pressure shrinks or skips the procedure. Secure `selftest` PASS in the start sequence of the Preparation section before the kickoff questions
- (Starting without storyline approval) Entering step 3 with only the module framework settled. Argument revisions come after the manuscripts are complete, and rewrites repeat. Start after checking the `(Approval)` line of 02_스토리라인.md
- (Arbitrary judgment statement changes) Writing new □ judgment statements or reordering them while writing manuscripts. The delivered file diverges from the argument the user approved. For changes in meaning, reconfirm and revise from the storyline
- (Lone □) A table or the next □ comes under □ without ❍. Place at least one ❍ or delete the □
- (Stretching sentences) Filling a volume shortfall with connective endings and modifiers. The fix is to add composition units (evidence lines, ※, tables, □ splits)
- (Deepening only named parts) Expanding only the sections the user asked about while other sections with the same points stay at framework level. Check with the attributed points of the section ledger
- (Tables with only column headers) Preliminary survey tables without values. Fill in actually surveyed values or `[확인]`. Add the update note under the table
- (Listing only work product titles) Ending with "○○보고서(안)". A filled draft is needed
- (Showing off methodology names) Repeatedly exposing framework names. Persuade with execution content
- (Adjectives in Features and Strengths) Ending with "풍부한 경험" (rich experience) or "전문성 보유" (holding expertise). Named engagements and track record tables are the evidence
- (Listing strategy names) Strategy names without grounds or implementation content. One supporting table per strategy
- (Strategy names ending in a name) Strategy names end with a work product name, a meeting body name, or a methodology name. The strategy reads as the name of a result or a held asset. End with an action noun that names the measure's action (for example, 수립, 연계, 운영, 제시). The criteria are in the content-models.md Implementation Strategy section
- (Module-repeating strategy) Strategy judgment statements restate Module names and activities (diagnosis, pilot application, analysis). The module overview table conveys the same content after the strategy table is deleted. Rewrite with risk factors and means from the derivation table
- (Generic operating means as strategy) Operating means unrelated to the engagement's difficulties, such as three advisory committee meetings or a monthly working council, serve as the strategy's means. Pin the design of activities to the engagement's difficulties, such as the criteria that divide subcommittees, the targets of a pretest, and the targets of a demand survey. If there is no difficulty to pin, move it to the implementation structure
- (Schedule-declaring strategy) Strategy □ and value ❍ end in the form "OO으로 N년까지 OO을 확정" (finalize OO by year N through OO). A schedule the author worked out backward reads as strategy. Rewrite with a design principle and the risk it resolves. Move completion timing to the schedule chart
- (Duty-restating strategy) Work the RFP and institutions already require becomes the content of the strategy, as in "요구 산출물의 충실한 작성" (faithful preparation of required work products), "부처 대응일정 준수" (meeting the ministry's response schedule), "보안 규정 준수" (security rule compliance), and "국가 망 보안체계 기반 설계" (design based on the national network security system). Every bidder could write the same sentence. Write as the judgment statement the specialized way the duty is achieved. For example "자료 등급별 처리 경로 분리로 국가 망 보안체계 안에서 생성형AI를 활용"
- (Leaked derivation table) A table that lists risk factors or values secured by strategy, such as the implementation strategy derivation table, goes into the manuscript. The author's internal reasoning shows to evaluators as it is. Delete the table, then write the content found only in the table into the □ judgment statement and ❍ of the strategy it belongs to
- (Supplier-view storyline) Implementation strategy judgment statements and section messages end with the proposer's way of working. The user ends up repeating the same correction at the approval step. Before presenting, move the endings of section messages to the outcomes the client obtains and the endings of implementation strategy judgment statements to the risks resolved or values secured
- (Repeating an abstract naming) Implementing the demand-side view by swapping subjects makes "발주처는" and "발주처가" repeat throughout the manuscripts (the reason is in the Reader-Perspective Writing section). Delete the subject and write target and state in the predicate. Where naming is needed, use the organization's real name
- (Outcomes that end in work products) Describing what the client obtains as the submission of reports and result tables. It reads as a proposal that ends with delivering a report. Rewrite as the change that happens to the client after the work products
- (Listing committee names) No composition, sessions, agenda, or point of use. Specify them with an operation (draft) table
- (Analysis-centered writing for a derivation-centered Task) Only analysis targets and scale are stated, without criteria and procedures. Place a criteria table
- (Skipping the module introduction) Going straight from the Module band to Tasks. Place (목적), (추진방안), and the overview table for every module
- (Mixed levels inside a Task) A □ that repeats the band name under the Task band, or conclusion ❍ lines without labels between label ❍ lines. Place only label ❍ lines under the band. Move conclusions down to hyphens under the relevant label
- (Literal workaround of banned words) Replacing "게이트" with "관문" or "활용" with "쓰임새". Use the conventional vocabulary of lexicon.md
- (Mechanical transplant of a standard framework) Applying the strategic planning framework ahead of the RFP's task structure. The RFP task details always take priority
- (Planning out of proportion to scale) Presenting analysis procedures for large fiscal programs to a project worth a few hundred million won. Scale analysis procedures to the project size
- (Describing an abolished system as current) Describing a reorganized system, such as the preliminary feasibility study for national R&D programs, as if it were current. Check whether it is current at the start
- (Creating document TOC pages) Creating a cover and a table of contents directly in the manuscripts. Use the build options `--cover` and `--toc` or insert them in 한/글 (the conditions for turning on `--toc` are in the Typesetting section)
- (Deciding long-table handling arbitrarily) Typesetting with engine or split chosen without asking the user. Apply the kickoff answer to `--long-table` and the directive lines
- (Reposting in replies) Printing manuscripts in chat replies. Output only as files
- (Bypassing the typesetter) Assembling a new document by calling the python-hwpx or python-docx API directly. Resolve script errors in the settings part of proposal.py or in the manuscripts (fixing call sites for API changes is in the Preparation section)
- (Generating figures) Inserting diagrams and charts drawn with code. Out of scope. Rebuild them as tables or adopt from source images

## Format Notice

- 본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.
    + (English) This product was developed with reference to Hancom's published HWP document file (.hwp) specification
- (Trademarks) 한/글 (Hangul), Hancom Office, and HWPX are trademarks of Hancom Inc. (한글과컴퓨터)
- (Independence) This tool is an independent tool with no affiliation with Hancom Inc.
