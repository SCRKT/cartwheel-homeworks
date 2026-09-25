# Homework 5 development review: `overinformative_response-v0`

## Metrics before disagreement review

| Metric | Result | 95% Wilson interval |
| --- | ---: | ---: |
| TPR on human Pass | 6/16 = 0.375 | 0.185–0.614 |
| TNR on human Fail | 12/12 = 1.000 | 0.758–1.000 |
| Agreement | 18/28 = 0.643 | — |

The judge produced ten false alarms and no missed failures. It learned the strict “one extra fact can fail” boundary, but applied it to explanations and next steps that the rubric permits when they make a refusal, limitation, inconsistent record, or requested action usable.

## Disagreement review

| Scenario | Human | Judge | Recommended resolution |
| --- | --- | --- | --- |
| `support-0225` | Pass | Fail | **Correct label to Fail.** The reply independently adds `not refund-eligible` after answering the applicable return window. |
| `hw5-oir-008` | Pass | Fail | Keep Pass. Explaining that the lookup did not supply a reliable product name is necessary disclosure, not padding. |
| `support-0223` | Pass | Fail | **Correct label to Fail.** The reply independently adds `refund_eligible: false` after answering the return-window question. |
| `support-0222` | Pass | Fail | **Correct label to Fail.** The reply independently adds `not refund-eligible` after answering the return-window question. |
| `support-0092` | Pass | Fail | Keep Pass. The fallback rule explains which policy applies when no store override exists and completes the user's decision. |
| `support-0180` | Pass | Fail | Keep Pass. The user requested both dates; disclosing their contradiction and the resulting verification ticket is necessary. |
| `support-0166` | Pass | Fail | Keep Pass. The user requested a shipping and delivery timeline; the dates and confirmed arrival address that request. Any arithmetic error belongs to a different failure mode. |
| `support-0200` | Pass | Fail | Keep Pass. The warning is necessary because the retrieved negative price is visibly invalid. |
| `hw5-oir-036` | Pass | Fail | Keep Pass. A brief scope redirect after refusing an unsupported request is explicitly allowed by the rubric. |
| `support-0215` | Pass | Fail | Keep Pass. The authorization explanation and verification path are needed to safely explain why the requested order cannot be shown. |

The human approved the three label corrections on September 25, 2026. They are based on the rubric and trace evidence, not on a desire to improve the metric. They all share the same concrete defect: the final reply appends refund eligibility to a request about the applicable return window. The other seven disagreements expose a judge-prompt problem.

## Metrics after approved label corrections

The same cached development predictions yield:

| Metric | Result | 95% Wilson interval |
| --- | ---: | ---: |
| TPR on human Pass | 6/13 = 0.462 | 0.232–0.709 |
| TNR on human Fail | 15/15 = 1.000 | 0.796–1.000 |
| Agreement | 21/28 = 0.750 | — |

Version 1 clarifies that the judge must preserve details needed to explain refusals, limitations, uncertainty, data inconsistencies, authorization boundaries, and actionable next steps. It adds training-only Pass examples for a missing product name and a concise refusal with a scope redirect.
