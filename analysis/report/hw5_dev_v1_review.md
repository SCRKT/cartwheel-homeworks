# Homework 5 development review: `overinformative_response-v1`

## Comparison

| Version | TP | FN | TN | FP | TPR | TNR | Agreement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v0 after label corrections | 6 | 7 | 15 | 0 | 0.462 | 1.000 | 0.750 |
| v1 | 7 | 6 | 13 | 2 | 0.538 | 0.867 | 0.714 |

Version 1 recovered one human Pass but missed two human Fail cases. It reduced the original over-strictness only slightly and weakened failure detection, so it should not be frozen.

## Disagreement review

| Scenario | Human | Judge | Resolution |
| --- | --- | --- | --- |
| `hw5-oir-008` | Pass | Fail | Keep Pass. The store and product identifier locate the record while the explanation discloses why the requested product name is unavailable. |
| `hw5-oir-032` | Fail | Pass | Keep Fail. The answer adds shopper-data and support-role permissions after answering the merchant-scope question. |
| `support-0092` | Pass | Fail | Keep Pass. The fallback rule is necessary to decide which policy applies when no override is posted. |
| `support-0180` | Pass | Fail | Keep Pass. The user requested the ship and delivery dates; their contradiction and the verification ticket are directly relevant. |
| `support-0166` | Pass | Fail | Keep Pass. The user requested the shipping and delivery timeline. The critique also refers to quantity and price that do not appear in the final reply, showing that the judge did not stay grounded in the evaluated text. |
| `support-0200` | Pass | Fail | Keep Pass. A negative price is visibly suspect, so the warning and verification advice are needed to make the requested price safe to use. |
| `support-0215` | Pass | Fail | Keep Pass. The privacy rationale and account/order verification steps make the authorization refusal understandable and actionable. |
| `support-0183` | Fail | Pass | Keep Fail. Explaining the missing delivery date and ticket is necessary, but the reply adds extended platform and store-override policy exposition when a shorter answer would suffice. |

No additional human labels require correction. The final permitted revision should use an explicit decision procedure based on the function of each detail. It should distinguish ordinary direct answers from unavailable or unsafe answers, keep exact dates when the user requested a timeline, permit warnings for visibly suspect values, and flag unrelated role permissions or policy exposition. The critique must identify text actually present in the final reply.
