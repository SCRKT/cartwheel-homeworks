# Homework 5 mode selection

## Selected failure mode

**Mode:** `overinformative_response`

**Question:** Does the assistant answer the user's request directly, without adding unnecessary detail that materially makes the answer harder to scan?

**Pass:** The response gives the information needed to answer the request. It may include details needed to disambiguate a result, explain a decision, disclose a limitation, or safely complete an action.

**Fail:** The response adds order fields, history, policy exposition, or other details the user did not request when a shorter response would fully answer the question, and the extra material makes the answer materially harder to scan.

**Required evidence:** The judge needs the user's request, the assistant's final reply, and any earlier conversation or tool evidence needed to tell whether a detail was necessary. A response can Pass this mode even if it has a different failure.

**Boundary with neighboring modes:** This mode concerns unnecessary detail. False claims or claims that exceed retrieved evidence belong to `retrieved_evidence_misstatement`; missing policy citations belong to `missing_policy_grounding`; and failures to hand off a case belong to `missing_required_escalation`.

## Why the initial mode was rejected

The first candidate was `unresolved_data_inconsistency`. We narrowed its boundary to ask whether the response avoids treating known missing, invalid, or inconsistent source data as reliable while clearly communicating uncertainty. Six deduplicated Homework 4 examples established the initial boundary, and migration of independent Homework 4 decisions produced 30 Pass and 2 Fail labels.

To seek more Fail examples, we generated and ran 40 targeted one-turn scenarios with `gpt-5.6-luna` on the Fast service tier. The batch included hidden cross-record mismatches, invalid numeric values, lifecycle contradictions, missing information, and duplicate or conflicting records.

The post-run evidence audit found that the mode was not suitable for this assignment. In ten store-mismatch scenarios, the agent called only `get_order`; the contradiction existed in scenario-generation metadata rather than in the observable trace. A judge could identify those cases only if that hidden metadata were added to its input, which would violate Homework 5's prohibition on label and generation-metadata leakage. Most anomalies that were visible in the trace were handled correctly, leaving too few independent Fail examples to reach the required 30 without distorting the task.

The exploratory labels, exclusions, batch plan, and results are preserved under `tmp/hw5/unselected_unresolved_data/` and `tmp/hw5/`. They are excluded from the selected judge dataset.

## Why `overinformative_response` was selected

This mode is fully observable from the conversation presented to the judge and is explicitly aligned with the Homework 5 example of judging whether a reply contains enough information for the user's next decision without unnecessary detail. Homework 4 already contains 116 human Pass decisions and 5 human Fail decisions for the mode.

For the initial HW5 set, we retained the five Fail conversations and selected 30 Pass conversations from distinct scenario families. We excluded Pass candidates from the same scenario families as the five Fail examples. The resulting seed set has:

| Human label | HW5 value | Conversations |
| --- | ---: | ---: |
| Pass | 1 | 30 |
| Fail | 0 | 5 |
| **Total** |  | **35** |

We then ran 36 targeted, independent, one-turn scenarios that asked for narrow answers across different intents, roles, record states, and tools. All 36 runs completed with `gpt-5.6-luna` on the Fast service tier. The batch produced 25 human-confirmed Fail decisions and 11 human-confirmed Pass decisions. Combined with the seed set, the selected dataset now contains:

| Human label | HW5 value | Conversations |
| --- | ---: | ---: |
| Pass | 1 | 41 |
| Fail | 0 | 30 |
| **Total** |  | **71** |

Each new trace has a unique session and scenario family. The human approved the complete 25 Fail / 11 Pass recommendation set before the decisions were appended to the HW5 label file.

During the first development disagreement review, the human corrected three migrated return-window labels from Pass to Fail because the replies independently appended refund-eligibility information. The current live label counts are **38 Pass and 33 Fail** across the same 71 conversations. The append-only label file retains the three superseded decisions and their replacements.

One scenario exposed an additional behavior worth recording. When asked whether support chat could change a password, the agent correctly said that the change must happen in account settings, then unnecessarily created support ticket 182 and explained the escalation SLA. This was labeled Fail for overinformation. It also showed that a prompt designed to be read-only can still cause an agent to choose a mutating tool, so future run plans should distinguish requested actions from possible agent-selected actions.

## Judge data preparation

The exact judge input export contains all 71 accepted conversations. It retains user and assistant messages plus tool calls, tool results, and retrieved policy passages needed to interpret the final reply. It excludes system prompts, human labels, review evidence, expected outcomes, scenario identifiers, and generation metadata. Its SHA-256 digest is `a07a1cc97ccfd3579fc0d46e6aea8a51101c7c9f656c41f7d35294f980345450`.

An identity audit before the first judge run found that the initial migration for `support-0245` and `support-0250` pointed to the first trace in each two-turn session while its written evidence described the final turn. Both turns carried the same original human Pass decision. The HW5 records were corrected to the final-turn trace IDs, and the input export and split were regenerated before any judge prompt was run.

The final split uses seed 7 and the required 20/40/40 fractions:

| Split | Pass | Fail | Total |
| --- | ---: | ---: | ---: |
| Training | 8 | 6 | 14 |
| Development | 16 | 12 | 28 |
| Test | 17 | 12 | 29 |

Prompt version 0 uses four examples from the training split: a clear Pass, a clear Fail, a borderline Fail, and a borderline Pass. No development or test record appears in the prompt.

## Development outcome

Three prompt versions were evaluated on the fixed 28-record development split. After the approved label corrections, v0 achieved TPR 0.462, TNR 1.000, and 0.750 agreement. Version 1 achieved TPR 0.538, TNR 0.867, and 0.714 agreement. Version 2 achieved TPR 0.462, TNR 0.667, and 0.571 agreement.

Development stopped after the two revisions allowed by the handout. Version 0 was selected because it had the best agreement and detected every human Fail example on development. Its low Pass agreement indicated that it would likely be suitable only as a conservative triage signal that sends many cases to human review.

## Held-out test outcome

Version 0 was frozen before any held-out prediction was generated, then evaluated once on all 29 test traces with `gpt-4o-mini`. The test set contained 17 human Pass and 12 human Fail labels. The judge achieved TPR 0.647 (95% Wilson CI 0.413–0.827), TNR 0.833 (95% Wilson CI 0.552–0.953), and 0.724 agreement, with 11 true Pass, 6 false Fail, 10 true Fail, and 2 false Pass decisions.

The eight disagreements were inspected without changing test labels or the frozen prompt. The result supports using the judge only as a human-review triage signal. It should not make autonomous enforcement decisions because it missed two known failures and incorrectly rejected six acceptable responses. The human reviewer approved this final decision on September 25, 2026. The full assessment is recorded in `analysis/report/hw5_test_review.md`.

## Decision record

The switch to `overinformative_response` was reviewed and approved by the human on September 24, 2026. The selected label convention is the Homework 5 convention: `1 = Pass` and `0 = Fail`.
