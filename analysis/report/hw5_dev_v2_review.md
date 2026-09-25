# Homework 5 development review: `overinformative_response-v2`

## Three-version comparison

| Version | TP | FN | TN | FP | TPR | TNR | Agreement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v0 after label corrections | 6 | 7 | 15 | 0 | 0.462 | 1.000 | 0.750 |
| v1 | 7 | 6 | 13 | 2 | 0.538 | 0.867 | 0.714 |
| v2 | 6 | 7 | 10 | 5 | 0.462 | 0.667 | 0.571 |

Version 2 did not resolve the false alarms and missed five human Fail cases. The explicit decision procedure encouraged the judge to rationalize independent extra facts as relevant context. It is the weakest version and should not be frozen.

## Disagreement review

All twelve disagreements were reviewed. No additional human label corrections are recommended.

The five missed failures were direct questions where the reply added an independent subject: delivery date after a refund-eligibility answer, dispute handler after a dispute-window answer, return advice after a cancellation-cutoff answer, other-role permissions after a merchant-scope answer, and extended policy exposition after explaining that a missing delivery date prevented an exact deadline.

The seven false alarms concern details the human rubric treats as necessary: the fallback rule for policy applicability, exact contradictory dates and the verification handoff, dates requested as part of a timeline, a warning about an impossible negative price, a requested account-change escalation, a concise scope redirect, and the privacy rationale plus verification path for an authorization refusal.

## Selection recommendation

Select `overinformative_response-v0` for the held-out test. It has the best development agreement and, most importantly for a failure detector, detected all 15 human Fail cases after label review. Its TNR is 1.000 with a 95% Wilson interval of 0.796–1.000.

Version 0 also has a serious limitation: it flagged seven of thirteen human Pass cases, for a TPR of 0.462 with a 95% Wilson interval of 0.232–0.709. That would create a large manual-review burden. The held-out test should determine whether v0 is useful as a conservative triage signal. It should not be trusted for autonomous enforcement unless test performance is substantially stronger and the intended workflow tolerates its false alarms.

Development stops here because the handout permits at most two prompt revisions, and both revisions performed worse overall than v0. The test split remains untouched.
