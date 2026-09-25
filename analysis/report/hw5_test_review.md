# Homework 5 held-out test review

## Frozen configuration

- Judge: `overinformative_response-v0`
- Model: `gpt-4o-mini`
- Status: frozen before the first test prediction
- Held-out test set: 29 traces, comprising 17 human Pass and 12 human Fail labels
- Prompt revisions after test inspection: none
- Test-label changes after test inspection: none

## Test result

| Measure | Result |
| --- | ---: |
| Agreement | 21/29 (72.4%) |
| Human Pass correctly judged Pass | 11/17 |
| Human Pass incorrectly judged Fail | 6/17 |
| Human Fail correctly judged Fail | 10/12 |
| Human Fail incorrectly judged Pass | 2/12 |
| TPR (Pass recall) | 0.647 (95% Wilson CI 0.413–0.827) |
| TNR (Fail recall) | 0.833 (95% Wilson CI 0.552–0.953) |

The judge returned Fail for 16 traces. Ten were human Fail cases and six were human Pass cases, so 37.5% of the cases it would send to review were false alarms. It returned Pass for 13 traces and missed two of the twelve human failures.

## Disagreement review

All eight disagreements were inspected after the judge was frozen. The held-out human labels remain unchanged.

| Scenario | Human | Judge | What the disagreement shows |
| --- | --- | --- | --- |
| `hw5-oir-018` | Fail | Pass | The requested refund destination was answered, but the judge treated the unrequested 5–10 business-day timing as useful context. |
| `hw5-oir-030` | Fail | Pass | The requested rule for unopened items was answered, but the judge accepted the percentage and disclosure rules for opened items as relevant context. |
| `support-0059` | Pass | Fail | The judge treated the monetary breakdown by status as unnecessary even though the user requested the main totals and statuses. |
| `support-0136` | Pass | Fail | The refund amount, approval state, refund ID, and follow-up describe the actual result of the requested action; the judge treated them as optional. |
| `support-0126` | Pass | Fail | The approval queue, ticket, and follow-up are needed to avoid implying that a large refund completed immediately; the judge treated them as optional. |
| `support-0230` | Pass | Fail | The judge applied the strict boundary to shipping dates and refund eligibility after explaining that a delivered order could not be cancelled. |
| `support-0088` | Pass | Fail | The judge treated the store-policy override caveat as unnecessary even though it limits the applicability of the standard return window. |
| `support-0195` | Pass | Fail | Four products matched an ambiguous product name, but the judge assumed one price would have been sufficient. |

The two missed failures share one pattern: additional facts remain close to the subject of the question, so the judge rationalizes them as useful background even when the direct question was already answered. The six false alarms share the opposite pattern: the judge discounts operational details, applicability caveats, and ambiguity resolution that make an answer accurate or actionable.

## Recommendation

Do not use this judge for autonomous enforcement or automatic response rejection. The held-out result is too uncertain and the boundary errors affect both directions: it misses 2 of 12 known failures and rejects 6 of 17 acceptable answers. The confidence interval for Fail recall is especially wide because the test set contains only 12 Fail examples.

The judge can be used as a conservative triage signal if every flagged trace receives human review and the workflow can tolerate false alarms. Under this test distribution, reviewing all 16 judge-Fail cases would find 10 of the 12 human-labeled failures. It should be described as a prioritization aid rather than a reliable substitute for human judgment.

## Human decision

On September 25, 2026, the human reviewer approved the recommendation: reject the judge for autonomous enforcement and retain it only as a human-review triage aid.
