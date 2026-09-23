# Homework 4 review summary

## Reviewed sample

I reviewed and labeled **121 distinct traces across 111 sessions** from the
Module 1 corpus of **260 traces across 250 sessions**. The review unit for all
completion and labeling counts is a trace. Sessions remain useful for showing
multi-turn context, but they are not counted as reviewed traces.

The initial selection manifest contains 30 anchors: 15 uniform random traces
and 15 cluster representatives. Those anchors belong to 30 sessions. Expanding
the selected sessions for conversation context produces 34 traces because
`support-0241`, `support-0244`, `support-0247`, and `support-0248` each contain
two traces. The later evaluation task added 100 distinct traces across 90
sessions to 21 previously reviewed one-trace sessions, yielding the final
121-trace, 111-session review set.

The committed manifest preserves the initial 30 anchor selections and their
methods. Later batch membership was not appended to the manifest during the
review. The final trace set and review history remain reproducible from the
stable trace IDs, session IDs, scenario IDs, and timestamps in
`annotations.json`, but the precise assignment of those later traces among the
role-balanced, depth-search, and final-uniform batches is not fully
reconstructable. This is a provenance limitation of the saved review state.

### Composition by trace

| Dimension | Value | Traces | Fraction |
| --- | --- | ---: | ---: |
| Role | Shopper | 88 | 72.7% |
| Role | Merchant | 16 | 13.2% |
| Role | Support | 17 | 14.0% |
| Scenario group | Challenge | 85 | 70.2% |
| Scenario group | Coverage | 36 | 29.8% |
| Turn count | One-turn scenario | 101 | 83.5% |
| Turn count | Two-turn scenario | 20 | 16.5% |

The reviewed traces cover all 15 support intents in the scenario set:

| Intent | Traces | Intent | Traces |
| --- | ---: | --- | ---: |
| Account change | 5 | Cancellation | 7 |
| Dispute | 10 | Find order | 14 |
| List recent orders | 4 | List store orders | 2 |
| Order details | 5 | Order status | 16 |
| Order timeline | 6 | Out of scope | 4 |
| Policy question | 6 | Product search | 19 |
| Refund | 8 | Return deadline | 5 |
| Return policy | 10 |  |  |

## Final taxonomy and structured labels

Every reviewed trace received a separate present-or-absent judgment for each
of the six final modes. The 121 traces therefore produced **726 binary
judgments**. Matching local JSONL files were saved under
`analysis/state/labels/`, submitted to Langfuse as trace scores, and read back
by stable trace ID. Read-back verification found 121 unique remote judgments
for each mode with no missing trace IDs.

These quantities are **sample fractions**, not prevalence estimates. The
review intentionally combines uniform sampling, cluster representatives,
role coverage, and focused failure searches, so it does not represent the
source corpus as a simple random sample.

| Final failure mode | Present | Absent | Sample fraction |
| --- | ---: | ---: | ---: |
| `overinformative_response` | 5 | 116 | 4.1% |
| `missing_policy_grounding` | 9 | 112 | 7.4% |
| `unresolved_data_inconsistency` | 10 | 111 | 8.3% |
| `missing_required_escalation` | 11 | 110 | 9.1% |
| `ambiguous_candidate_overcommitment` | 5 | 116 | 4.1% |
| `retrieved_evidence_misstatement` | 6 | 115 | 5.0% |

The final 15 reviewed traces produced **zero previously unseen consequential
failure modes**. They added examples to existing modes, including policy
grounding, escalation, and retrieved-evidence errors, without requiring a new
category. This supports stopping discovery with the six-mode taxonomy.

## Taxonomy decisions

Workshop inspection caused one material revision. In run
`f5e302e5-0aee-48d8-a6c0-ba7f24f93963` (Langfuse trace
`d49fd692998b130c632d64da163f45a9`), the response claimed that it found no
conflicting records after making only one `get_order` call. I accepted the
observation but revised it into `retrieved_evidence_misstatement`: the mode now
covers claims about a broader evidence check than the recorded tool activity
supports, as well as direct contradictions and deterministic calculation
errors. This boundary separates overstatement of usable evidence from
`unresolved_data_inconsistency`, where the source data itself is suspect.

The AgentDebug comparison suggested inefficient planning or tool use as a
possible omitted group. I did not add it. The reviewed evidence contained one
human efficiency note and one harmless Workshop overfetching case, and the
latter did not degrade the response. That evidence did not meet the required
three confirmed positives for a final mode.

After revising `retrieved_evidence_misstatement`, a focused search returned
five suggestions: `support-0051`, `support-0052`, `support-0050`,
`support-0061`, and `support-0173`. I rejected all five after review because
their responses faithfully summarized or correctly scoped the recorded tool
evidence. One response was verbose, but verbosity alone does not cross this
mode's evidence-accuracy boundary.

The complete definitions, positive examples, close negatives, nearest-mode
boundaries, evaluator recommendations, requirement sources, and decision
history are in `analysis/state/patterns.json`. Workshop run details and all
accepted, revised, rejected, and uncertain suggestions are in
`analysis/report/workshop_notes.md`.
