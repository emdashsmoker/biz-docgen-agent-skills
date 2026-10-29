# Proposal strategy

- For a new proposal deck, write the formats below in procedure step 2
- For a proposal deck conversion, arrange the content extracted back from the manuscript in the same formats

## RFP analysis format (00_rfp.md)

```
## Basic conditions      Program name, contracting agency, period, budget (not written in slide body), contract method, submission deadline, submission documents, presentation or not, presentation time
## Eligibility           Business type, region, certifications, minimum track record, staff qualifications (report unmet items to the user at kickoff)
## Evaluation table      Expanded by detailed evaluation item (columns: evaluation item, detailed item, original evaluation criterion text, score weight, quantitative or not, matching chapter)
## Work details (all)    Every RFP item moved over verbatim, one per line (IDs in [T1] [T2] format)
## Outputs and reports   Outputs, number of reports and delivery format set by the RFP
## Writing rules         Length, page size, whether a table of contents is prescribed, expressions the RFP restricts, mandatory reference tables
## Key wording
| Standard spelling | Variants to replace | Basis |
| 실행과제 | 이행과제, 세부과제 | RFP Ⅱ-3 |
```

- Key wording is 5-15 engagement names, output names, stage names and subject names the RFP uses
- Register key wording in `meta.rfp.wording` of the storyboard
- lint checks the appearance of variant spellings as FAIL
- Use of the standard spellings is checked in the RFP response item of the in-depth review
- (Matching chapter) The deck chapter that carries the evaluation evidence for a detailed evaluation item
- The matching chapter is the basis for the slide allocation per chapter
- The score weight of a main item is the sum of its detailed item weights
- The calculation unit for slide allocation is the detailed item weight
- Quantitative items (credit rating, number of track records) are excluded from slide allocation
- If there is a presentation evaluation, write the presentation time and Q&A time in the basic conditions
- The page limit is derived from the presentation time

## Proposal strategy format (00_strategy.md)

- The item order is the order of thinking
- Later items are derived from earlier items
- `[확인]` items are filled with user answers, the RFP text and competitor search results
- Estimated candidates in the competitor item are used with their search sources

```
## 1 Stated purpose and underlying needs   Purpose in the RFP background sentence. The outcome the contracting agency actually wants (hypothesis) and its basis. Circumstances at the time of the call
## 2 Minimum requirements                  Whether eligibility and track record are met. Workload against period and budget. Elements that cannot be delivered
## 3 Go or no-go                           Participation or not, reason, conditions for holding
## 4 External conditions                   Policy schedule, higher-level plans, budget review and similar programs around the contracting agency (opportunities and threats, where they are reflected)
## 5 Competitors                           Eligibility judgment, expected strengths and weaknesses by competitor type, competing candidate table, previous contractor of the same agency, excluded organizations (competitor table format below)
## 6 Own strengths and weaknesses          4 columns: track record, staff, domain knowledge, methodology. Missing elements and how to cover them (consortium, advisors)
## 7 Proposal strategy                     Differentiation point table (2-4 points, basis, tile). Strategy derivation table (2-4 rows). One-line storyline. 3 key keywords
## 8 Execution decisions                   Principal investigator and staffing. Advisor candidates. Success points and failure points. Price direction (bid range)
```

- Candidates for the underlying needs hypothesis: the revision cycle of a higher-level plan, audit findings, the first year of a new institution, reorganization, budget review, gaps left by a previous engagement's results
- The hypothesis names where the contracting agency will use the output
- The one-line storyline is a sentence running from the problem awareness in the background to the modules and outputs
- The deck's table of contents and headline flow follow the storyline sentence
- Item 7 consists of the differentiation point table and the strategy derivation table
    + The differentiation point table is the source of the capability tiles on the "제안의 특징 및 장점" slide (features)
    + The strategy derivation table is the source of the strategy pillars on the "추진전략" slide (strategy)
- The features slide shows what the bidder holds (methodology, track record, staff, tools, data)
- The strategy slide shows the measures that overcome the task's difficulties (output design principles, the design of activities)
- When the same methodology appears on both slides, each slide carries different content
    + (Feature tile) The holding of the methodology and its application record
    + (Strategy pillar) How the methodology is applied in this task

### Differentiation point table

| Differentiation point | Basis | Tile |
|---|---|---|
| [확인] | [확인] | [확인] |

- Match the number of points to the range of capability tiles (2-4)
- Attach at least one basis to each point: track record, data or staff
- The named past tasks, tools and staff in the basis column are the material of the tile items
- When a strategy pillar uses a point as its basis, add the pillar number in the tile column

### Strategy derivation table

- Strategies are derived from the task's difficulties (one row per strategy, 2-4 rows)
- A strategy derived from the problem in the background ends up as the module list under a new name
- The derivation table stays in 00_strategy.md only (the writer's internal reasoning)
- Write pillar titles, items and results as the positive form of the measure and the value
    + Every phrase on a slide reads as an independent element of equal weight
    + A negative phrase reads loudest in the result box, which is bold and framed
    + The strategy slide keeps its logic by showing only the measures that answer the issues (the task's difficulties) on the purpose slide
    + (Rewrite example) The derivation table's "현장 거부를 해소하는 수용성" becomes "부서가 수용하는 지표" on the slide

| Task trait | Risk | Strategy | Value secured |
|---|---|---|---|
| [확인] | [확인] | [확인] | [확인] |

- (Task trait) The scope the task must complete and the nature of what it handles
    + RFP task items, statutory procedures, compliance duties and constraints also go in this column
    + Duties are the premise shared by every bidder
- (Risk) The point where the output can go wrong because of the task trait
- (Strategy) The specialized measure that overcomes the risk
    + An output design principle
    + The design of an activity (composition criterion, target, timing)
- (Value secured) What the contracting agency gains when the risk is removed
    + Write it paired with the risk it removes
    + (Example) "reliability that removes distrust of wrong answers"
- The conditions of a strategy are specialization and differentiation
    + (Specialization) Design fitted to the traits of the task's subject
    + (Differentiation) Design the bidder adds above the level the RFP and the institution require
- (Duty removal test) What remains in the strategy column after removing compliance with RFP task items and statutory duties is the strategy
- A row with nothing remaining restates a duty and is rewritten
- Rows where both the risk and the measure are generic (schedule delay and a monthly meeting) move to the organization or schedule slide

### Strategy slide slot mapping

| Slot | Content | Source |
|---|---|---|
| goal | Final goal (same wording as the goal and scope slide) | 00_rfp.md basic conditions |
| strategies[].title | Strategy name. Name the measure in the task's terms (module names and activity names are excluded) | Strategy column of the derivation table |
| strategies[].items | 4-5 design details of the measure (target, composition criterion, timing, tool, judgment criterion) | Strategy column of the derivation table |
| strategies[].result | Positive form of the value secured (the risk removed is not written) | Value column of the derivation table |
| conclusion | A sentence that bundles the values to qualify the output (e.g. "an evaluation indicator system with acceptance, validity and readiness to start") | Value column of the derivation table |

- End each strategy name with an action noun that names the measure's action (for example, 수립, 연계, 운영, 제시, 설계, 도출, 반영 in a Korean deck; establishment, linkage, operation, design in an English deck)
    + (Output name ending) A name ending in "지표 체계" or "로드맵" reads as an output on the goal and scope slide
    + (Meeting body name ending) A name ending in "자문위원회" or "실무협의회" reads as an operating means on the organization slide
    + (Methodology name ending) A name ending in "로직모델" or "델파이" reads as a held asset on the features slide
- Rewrite examples of strategy names
    + "임무 연계형 지표 체계" becomes "임무와 부서 지표 정렬"
    + "분야별 분과 위원회" becomes "기술 분야별 분과 구성"
    + "성과 로직모델" becomes "로직모델 적용 성과 경로 설계"
- Write each pillar item to fit one line of the pillar width (about 16 Korean characters at 16:9)
- One pillar with a two-line item tightens the item spacing of every pillar to match it (the build uses the smallest per-pillar spacing as the shared spacing)
- The headline substitutes the strategy names, worded the same as the pillar titles, into the strategy pattern in `references/headline-patterns.md`
- When each strategy gets its own slide (IT planning convention, high-score sub-items), promote the pillar items to the body
    + Place a supporting table that is a specimen of the method (step table, quality indicator table, subcommittee table, survey design table) as the Sample
    + Do not place a table that lists risks or values secured by strategy, such as the derivation table, as the Sample
    + Write "참고용 예시 (미확정)" (illustrative example, not finalized) in the `footnotes` of the specimen table

### Self-check before presenting

- Every risk has a pillar that answers it
- Pillar titles and items do not repeat module names or activity names (diagnosis, survey, advisory committee operation)
- Strategy names in the pillar titles and the headline end with an action noun
- A measure remains in the strategy column after removing RFP task items and statutory duties
- Every value in the derivation table is paired with the risk it removes
- Pillar titles, items and results are in the positive form without a declared completion date
- Every differentiation point has a capability tile
- Every strength on a capability tile is in the differentiation point table

## Competitor search

- In environments where web search is allowed, fill the competitor item through the search paths (award records, public disclosure, peers of the bidder, industry search)
- Few organizations publish the fact that they carried out a public engagement
- The public disclosure path alone rarely fills the competing candidate table
- Use the award record path together with the estimation paths (peers of the bidder, industry search)
- In environments without web search, list only award results provided by the user
- In environments without web search, ask the user for the other items
- Also ask the user about types for which no organization was confirmed after running every path

### Eligibility judgment

- Before searching for competing candidates, judge which company sizes can bid on this call
- (Purpose) Build the competing candidates from companies eligible to bid
- The first basis for the judgment is the eligibility text of the bid notice and the RFP
- If the text differs from the amount-based criteria, follow the text
- If there is no text or it is ambiguous, estimate with the institutional criteria below
- Mark estimated judgments with `[확인]`

#### Service contract amount criteria

- Article 2-2 of the 「중소기업제품 구매촉진 및 판로지원에 관한 법률 시행령」 (Enforcement Decree of the Act on Facilitation of Purchase of SME Products) sets company size limits for public agency service contracts
- (Estimated price under KRW 100 million) Restricted competition among small enterprises or micro businesses (medium, mid-sized and large enterprises cannot bid)
- (Relaxation under KRW 100 million) For calls where eligible small enterprises or micro businesses are clearly 3 or fewer, or the call failed, restricted competition among SMEs (medium enterprises can bid)
- (Estimated price from KRW 100 million up to the notified threshold) Restricted competition among SMEs (mid-sized and large enterprises cannot bid)
- (At or above the notified threshold) No company size limit by amount
- Services designated by the Minister of SMEs and Startups as products for competition among SMEs are competed among SMEs regardless of amount
- Check the bid notice for whether the service is such a designated product

#### Amount conversion

- The amount criteria apply to the estimated price (amount excluding VAT)
- If the base amount or program budget of the call includes VAT, divide by 1.1 to get the estimated price
- The boundary amounts including VAT are KRW 110 million (for the KRW 100 million criterion) and KRW 253 million (for the KRW 230 million notified threshold)
- The notified threshold is the amount for goods and services notified every 2 years by the Minister of Economy and Finance under Article 4(1) of the 「국가를 당사자로 하는 계약에 관한 법률」 (Act on Contracts to Which the State Is a Party)
- The notified threshold for 2025-2026 is KRW 230 million
- If the call date is in 2027 or later, check the new notified threshold by web search

#### Academic research exception

- Article 2-3 of the same Enforcement Decree allows exceptions to preferential procurement for policy advisory services (academic work, research, surveys, evaluation, etc.)
- The exception requires a need for nonprofit corporations to bid
- A call applying the exception states the reason in the bid notice
- Large consulting firms can also bid on exception calls
- For academic research services, judge by the eligibility text of the bid notice and whether an exception reason is stated

#### SW project amount criteria

- Article 48 of the 「소프트웨어 진흥법」 (Software Promotion Act) and Appendix 1 of the Ministry of Science and ICT notice 「중소 소프트웨어사업자의 사업 참여 지원에 관한 지침」 (Guidelines on Supporting Project Participation of SME Software Businesses) set the minimum project size for large enterprise participation in software projects
- Check the latest notice number and Appendix 1 at kickoff (the notice is revised often)
- Large enterprises under this criterion are all software businesses except SMEs (mid-sized enterprises included)
- The minimum project size for large enterprise participation differs by company category
    + (Companies with sales of KRW 800 billion or more) Projects of KRW 8 billion or more
    + (Companies with sales under KRW 800 billion) Projects of KRW 4 billion or more
    + (Companies that grew from SME to mid-sized within 5 years) Projects of KRW 2 billion or more
- Only SMEs can bid on projects under KRW 2 billion
- Companies in business groups subject to cross-shareholding restrictions can join only exception projects
- The project amount of a SW project is the estimated price including VAT (computed differently from the estimated price of the service contract criteria)
- The contracting agency must state in the bid notice or RFP whether the large enterprise participation limit applies
- For SW projects, check the large enterprise participation limit text in the bid notice or RFP first
- For IT planning services such as ISP and ISMP, check whether they count as SW projects from the bid notice text
- (Government improvement plan of January 2024) SME-only projects raised to KRW 3 billion, design and planning projects opened, business groups subject to cross-shareholding restrictions allowed on projects of KRW 70 billion or more
- Check at kickoff whether the improvement plan is reflected in the current guideline Appendix 1
- If the reflection status and the bid notice text differ, apply the bid notice text first

#### Applying the judgment

- If the judgment limits bidding to SMEs or smaller, delete the large consulting firm type from the competitive landscape
- The large consulting firm default candidate rule applies only to calls where the large consulting firm type remains
- The university industry-academic cooperation foundation type stays regardless of the company size judgment
- Include company size and region conditions in the queries of the peer and industry search paths
    + (Reason) Search the group of organizations meeting the conditions from the start
    + (Sample queries) "[지역] 소재 [업종] 소기업", "[과업 유형] 연구용역 중소기업 제한 낙찰"
- Write the judgment and its basis (bid notice text, or estimated price and applicable article) in the eligibility judgment item of the competitor table format

#### Turning filtering off

- If the user asks for a competitor search without eligibility filtering, skip the eligibility judgment and its application
- The request to turn filtering off gives the user's judgment priority (the timing and application of the rules change often)
- With filtering off, the large consulting firm default candidate rule applies regardless of the call amount
- With filtering off, skip the eligibility exclusion and the excluded organization memo of the industry search path
- With filtering off, write "Filtering off (user request)" in the eligibility judgment item

### Search paths

#### Award records

- Check bid opening results and award results on 나라장터 (KONEPS) by web search
- Automated collection is often restricted on the original KONEPS site
- If the original site is blocked, use republished pages exposed in search results
- Usable republished pages
    + Call detail pages on private bid information sites
    + Bid notice boards on the contracting agency website
    + Preferred bidder selection result boards on the contracting agency website
    + Contract information disclosure boards on the contracting agency website
- Search engines mainly index call names
- Check award records in 2 stages
    + (Stage 1) Search by call name for the call pages of past programs of the same name at the same agency and of the same type at other agencies
    + (Stage 2) Check the bid opening result, awardee and preferred bidder items on the call page
    + (Re-search) If the call page lacks these items, search again by call number
- Sample queries: "[과거 사업명] 개찰결과", "[과거 사업명] 우선협상대상자", "[공고번호] 낙찰자", "[발주기관명] 계약정보 공개 [과업 키워드]"
- KONEPS award results provided by the user are also recorded under the award record path

#### Public disclosure

- Search for contract wins that contractors announced in press releases, website track record lists, blogs and social media
- The search covers programs of the same agency and programs of the same type at other agencies
- Sample queries: "[발주기관명] 연구용역 수주", "[발주기관명] 착수보고회 수행기관", "[과업 유형] 수립 연구용역 최종보고회 수행기관"

#### Peers of the bidder

- The peer path searches for organizations that repeatedly compete with the bidder in the same contracting agency market
- Summarize the bidder profile from the business areas, staff size and track record areas in company.md in the work folder
- Search for organizations with the same profile
- Sample queries: "[자사 사업 분야] 전문 컨설팅 기업", "[자사 대표 과업 유형] 연구용역 수행기관"
- If company.md is empty, use the answer to kickoff question 11
- If neither exists, skip the peer path

#### Industry search

- Derive from the engagement characteristics the industries that can deliver this engagement
- Search for companies and organizations in those industries
- Examples of derived industries
    + (ISP) IT consulting firms, SI affiliates
    + (R&D performance analysis) Science and technology consulting firms, specialized research institutes
    + (Regional development plan) Regional research institutes, urban planning engineering firms
- Search material: association member lists, mentions of major companies in industry articles, combined queries
- Combined queries combine the engagement field, engagement type and contracting agency type of the RFP (e.g. "OO 기본계획 수립 연구용역", "OO 분야 산학협력단 정책연구")
- Exclude organizations that cannot bid under the RFP eligibility (business registration, large enterprise participation limits, regional limits)

#### Large consulting firm default candidates

- Applies to calls where the eligibility judgment lets mid-sized and large enterprises bid
- With a request to turn filtering off, it applies to every call
- Large consulting firms that do not advertise a public sector practice on their websites also win many public engagements
- Leave out whether a firm advertises a public sector practice from the candidate selection criteria
- The default candidates are large consulting firms with many public consulting contract wins
- Organizations whose names do not contain "consulting" are also candidates when they have public consulting contract wins
- Confirm the contract wins of these organizations separately through the award record path
- Get organization names by searching industry articles and reports of public engagement awards
- Search for evidence of work in the engagement field and write it in the selection basis column
- If no evidence is found, write "공공 용역 다수 수주 기관군" (group winning many public engagements) in the selection basis column
- The source is the organization website URL and the check date

#### Excluded organizations

- For organizations excluded by eligibility, write the name, exclusion reason and check path in the excluded organization memo
- If a previous contractor or confirmed organization cannot bid on this call, the competitive intensity changes
- Reflect the exclusions in the strengths and weaknesses by type

### Path order

- Run the award record and public disclosure paths first
- Organizations confirmed by these two paths carry more weight as evidence than estimated candidates
- Run the award record and public disclosure paths whether or not they return results
- If 3 consecutive queries on one path find no organization, move to the next path
- Use the remaining searches to fill competitor types that have no organization yet
- Run the peer and industry search paths until each competitor type has at least 1 organization
- Remove competitor types that do not apply to the engagement
- Add new competitor types derived from the industry search

### Source notation

- The check path column of the competing candidate table holds one of the search path names
- (Confirmed organization) Found through the award record and public disclosure paths
- (Estimated candidate) Found through the peer and industry search paths
- The strengths and weaknesses mark confirmed organizations and estimated candidates separately
- Estimate the expected strengths and weaknesses by type from the competing candidate table
- Give a source URL for each organization
- Give the posting date when it can be confirmed
- If the posting date cannot be confirmed, give the search date as the "check date"
- Organizations listed from searches must have a source URL
- The source of user-provided material is "User-provided (KONEPS)"

### Competitor table format

- Copy the format below as is into item 5 Competitors of 00_strategy.md and fill it in
- Keep the column names, order and count as in the format
- Write each cell value on one line (line breaks and the `|` character break a markdown table)
- Separate several values in one cell with commas
- Delete or add competitor type rows to fit the engagement

```
- (Eligibility judgment) Company sizes eligible to bid, basis (bid notice text, or estimated price and applicable article)
- With filtering off, write "Filtering off (user request)" in the judgment
- If the judgment limits bidding to SMEs or smaller, delete the large consulting firm row
- The university industry-academic cooperation foundation row stays regardless of the judgment

| Competitor type | Expected strengths | Expected weaknesses |
|---|---|---|
| University industry-academic cooperation foundation | [확인] | [확인] |
| Large consulting firm | [확인] | [확인] |
| Specialized research institute | [확인] | [확인] |
| Consulting firm of similar size | [확인] | [확인] |

- (Competing candidates) Organizations found through the search paths
- The source is the URL and posting date (check date if the posting date is unconfirmed) or "User-provided (KONEPS)"

| Organization | Competitor type | Check path | Similar engagement or selection basis | Source |
|---|---|---|---|---|
| [확인] | [확인] | [확인] | [확인] | [확인] |

- (Previous contractor of the same agency) Organization name, check path ("Unconfirmed" if not found)
- (Excluded organizations) Names excluded by eligibility, exclusion reason, check path ("None" if not applicable)
```

## Score attribution

### Attribution table format (in 00_storyline.md or ledger.json)

| Evaluation item | Detailed item | Weight | Quantitative | Matching chapter | Attributed slide IDs | Slides | Weight share | Slide share | Judgment |
|---|---|---|---|---|---|---|---|---|---|
| 사업수행계획 | 과업 이해도 | 10 | No | Ⅰ | S04, S05 | 2 | 12.5% | 5% | WARN |

- The sample row assumes a non-quantitative weight total of 80 points and 40 body slides

### Attribution criteria

- Attribute every non-quantitative detailed item to the `evalItems` of at least 1 slide (0 attributions is a lint FAIL)
- (Weight share) The share of the item weight in the total non-quantitative detailed item weight
- (Slide share) The share of attributed slides in the body slide count
- Body slides are all slides except cover, contents, dividers and closing
- If the slide share is half the weight share or less, or double or more, lint WARN
- Staff weights (principal investigator, participating staff) are attributed to profile slides
- Management weights (schedule, quality, security) are attributed to project management slides
- If the track record weight is quantitative, limit track record slides to 1
- If the track record weight is qualitative, add track record card slides
- For headers paired with evaluation items (RFPs that adopt the item order of the score table as the table of contents), put the evaluation item number in section
- Internal evaluation vocabulary in slide body text (배점, 채점, 방어 논리, 결정 장소, 귀속) is a lint FAIL
- Show correspondences only in the section ledger and the attached reference table
