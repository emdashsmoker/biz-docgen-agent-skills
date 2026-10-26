# In-depth review

## Criteria

- Run it right after check_layout passes in procedure step 7
- Run it once
- Review the slides attributed to detailed evaluation items worth 10 points or more (by `evalItems`)
- The scope is defects that lint and check_layout cannot catch
- Judgment and adjustment of defects outside the rules follow the SKILL.md sections on judging defects outside the rules and on visual adjustment discretion
- The reviewer plays an evaluation committee member
- Write the record as answers to the review item questions
- For each defect, write the slide ID and the fix direction in the review item of `state.json`
- Warning handling follows the SKILL.md completion conditions
- File delivery timing follows the SKILL.md procedure section

## Review items

| Item | Question | Defect example |
|---|---|---|
| Numeric integrity | Do the numerator and denominator of a ratio share the same reference date? Does the product or quotient of two indicators match a third? Does the same fact appear with two values? | Execution rate for 2025 against the 2023 budget. A total of 120 tasks against a detailed sum of 118 |
| Source reliability | Can each cited figure be submitted as an attachment? Are there paid reports or press figures without a source? Are well-known organizations missing from an industry top list? | Market size taken from press coverage. Growth rate without a source |
| Logical leaps | Are there intermediate steps from the data to the conclusion? Are facts with different conditions equated, such as stock and flow or amount and count? Does a cited figure support the opposite conclusion? | Treating growth in patent filings as proof of technological competitiveness |
| Underlying needs | Is there a slide that answers the underlying needs hypothesis in 00_strategy.md? | No module responding to audit findings |
| Distinctiveness | Could a competitor write the same sentence? Is there evidence only the bidder can offer (track record, data, staff)? Does a measure remain in a strategy pillar after the RFP task items and statutory duties are removed? | "풍부한 경험을 바탕으로". "요구 산출물의 충실한 작성" |
| RFP response | Does the slide content hold every requirement of the matching RFP work item text? Are the output names and the standard spellings of key wording required by the RFP kept as is? | Part of the survey targets set by the work item text missing. Altered output names |
| Respect for the contracting agency | Is there a sentence implying shortcomings in the contracting agency's policies or RFP? | "기존 지표가 부실하여" |

## Checks after fixing

- Fix found defects in the storyboard
- Rerun lint and the build after fixing
- Also rerun lint and the build after bulk style edits (to keep lint FAIL expressions from coming back)
- If the project organization chart and the project lead profile are both present, check that the leader title is consistent
- After editing an existing slide, contrast the shape coordinates with the original
- The coordinate contrast should show only the intended changes
- check_layout also reads `<file name>.build.json` in the same folder as the pptx
- Keep the pptx and `<file name>.build.json` in the same folder
