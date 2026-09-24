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

The next collection step is to run targeted, independent scenarios that ask for narrow answers across different intents, roles, record states, and tools. Those traces will be reviewed by the human before any additional labels are accepted. No judge prompt, data split, or test inspection will occur until the dataset has at least 30 accepted Pass and 30 accepted Fail conversations.

## Decision record

The switch to `overinformative_response` was reviewed and approved by the human on September 24, 2026. The selected label convention is the Homework 5 convention: `1 = Pass` and `0 = Fail`.
