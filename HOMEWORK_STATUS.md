# Cartwheel homework completion index

Last audited: 2026-09-29

All assignments currently released by the course, Homework 1 through Homework
7, have been completed. The repository contains the required implementation,
saved evidence, and evaluation data for each assignment. A screenshot PDF was
created for every homework and copied to `~/Desktop/Cartwheel Homework PDFs/`.

The course handouts ask for a short screen recording for each homework. The
student chose the screenshot PDFs as the submission record instead. The PDFs
document the work, but they are not literal video files; confirm that the
instructor accepts this substitution before final submission.

## Completion summary

| Homework | Status | Main evidence | Milestone commit | Report |
| --- | --- | --- | --- | --- |
| HW1 - Support tools | Complete | Five required tools, added support capabilities, and 12 reviewed conversations across all three roles | [`b839451`](https://github.com/SCRKT/cartwheel-homeworks/commit/b839451) | [HW1 report](output/pdf/Cartwheel_HW1_Report.pdf) |
| HW2 - Authenticated tracing | Complete | Authenticated sessions and messages, trace attributes, authorization tests, and exactly two selected trace records | [`ac8d805`](https://github.com/SCRKT/cartwheel-homeworks/commit/ac8d805) | [HW2 report](output/pdf/Cartwheel_HW2_Tracing_Report.pdf) |
| HW3 - Scenario dataset | Complete | 30 pilot scenarios, 250 final scenarios, 50 monitoring scenarios, and a 260-trace export covering all 250 scenario IDs | [`5b0266b`](https://github.com/SCRKT/cartwheel-homeworks/commit/5b0266b) | [HW3 report](output/pdf/Cartwheel_HW3_Scenario_Evaluation_Report.pdf) |
| HW4 - Human trace review | Complete | 121 distinct traces across 111 sessions, six-mode taxonomy, 726 structured judgments, and zero new consequential modes in the final 15 | [`68337ee`](https://github.com/SCRKT/cartwheel-homeworks/commit/68337ee) | [HW4 report](output/pdf/Cartwheel_HW4_Error_Discovery_Report.pdf) |
| HW5 - LLM judge | Complete | 74 human labels, three development prompts, one frozen judge, and a held-out 29-trace test | [`d86dfe8`](https://github.com/SCRKT/cartwheel-homeworks/commit/d86dfe8) | [HW5 report](output/pdf/Cartwheel_HW5_Judge_Evaluation_Report.pdf) |
| HW6 - Evaluation CI | Complete | 11 cases from two failure modes, five-run baselines, regression/capability classifications, two CI runs, and a 15-run stability analysis | [`6b2aad8`](https://github.com/SCRKT/cartwheel-homeworks/commit/6b2aad8) | [HW6 report](output/pdf/Cartwheel_HW6_CI_Evaluation_Report.pdf) |
| HW7 - Behavior monitoring | Complete | Two comparable 50-scenario periods, trace sampling, frozen judging, prevalence correction, Langfuse dashboard, and a successful scheduled workflow | [`fa2b6c8`](https://github.com/SCRKT/cartwheel-homeworks/commit/fa2b6c8) | [HW7 report](output/pdf/Cartwheel_HW7_Behavior_Monitoring_Report.pdf) |

## Validation record

The final offline regression run used the saved HW5 trace source:

```text
CARTWHEEL_JUDGE_TRACE_SOURCE=analysis/state/store_traces.json uv run pytest -q
154 passed, 14 skipped, 12 xfailed, 15 xpassed in 9.03s
```

The expected failures are the repository's intentionally unfinished exercise
markers. The unexpected passes are completed homework functions whose starter
tests are still marked as expected failures.

All seven PDFs were opened successfully during the audit. Matching copies are
present in both `output/pdf/` and `~/Desktop/Cartwheel Homework PDFs/`.

## Assignment evidence

### Homework 1

- Required source: `agent/tools.py`, `agent/agent.py`
- Conversation record: `hw1-session.jsonl`
- Verified: 12 valid records; shopper, merchant, and support roles represented;
  required orders 4127, 3980, and 4455 covered
- Result: five required support tools and the recorded prompt behavior are
  committed

### Homework 2

- Required source: `observability/instrument.py`, `server/app.py`,
  `tests/test_observability.py`
- Trace record: `hw2-traces.json`
- Verified: exactly two completed trace records with the required fields
- Prompt comparison: the controlled comparison produced hashes
  `d108f6949e5e` and `f4cf9d1978a4`; the current prompt was restored. The two
  traces selected for `hw2-traces.json` both use the restored prompt, while the
  comparison evidence is preserved in the HW2 report.

### Homework 3

- Required scenarios and reviews are saved under `scenarios/`
- Verified: 30 pilot scenarios, 12 pilot reviews, 250 final scenarios, 15 final
  reviews, and 50 monitoring scenarios
- Final execution: all 250 scenarios completed
- Trace export: 260 traces, 250 unique scenario IDs, zero missing IDs

### Homework 4

- Review interface: `analysis/review_app/`
- State: `analysis/state/annotations.json`, `patterns.json`, `suggestions.json`,
  and six final label files
- Verified: 121 reviewed traces across 111 sessions; multi-turn sessions are
  counted by trace rather than session
- Taxonomy: six final modes and 726 present/absent judgments
- Stability: the final 15 traces introduced zero new consequential modes
- Recorded limitation: later review-batch membership is not fully
  reconstructable, although stable trace, session, scenario, and timestamp
  identifiers preserve the final reviewed set

### Homework 5

- Human evidence: 74 labels for `overinformative_response` (33 Fail, 41 Pass)
- Development: three saved prompt versions and development reports
- Frozen judge: `overinformative_response-v0`
- Held-out test: 29 traces; TP 11, TN 10, FP 2, FN 6; agreement 72.41%
- Saved reports include TPR, TNR, confidence intervals, disagreements, and the
  decision to use the judge with calibration and human review

### Homework 6

- Evaluation suite: 11 cases covering `missing_required_escalation` and
  `missing_policy_grounding`
- Classification: 10 regression cases and one capability case
- CI evidence: intentional regression run
  [36215130310](https://github.com/SCRKT/cartwheel-homeworks/actions/runs/36215130310)
  and reverted run
  [36216043198](https://github.com/SCRKT/cartwheel-homeworks/actions/runs/36216043198)
- The target case moved from 0/5 to 5/5 after the intentional regression was
  reverted. The second workflow remained red because another case had one
  behavioral failure and one literal evaluator check produced a false negative;
  this is documented in `ci-runs.json`.
- Capability analysis: 4/15 successes for `e-011`; pass@1, pass@3, and pass@5
  moved materially from 10 to 15 runs, so the estimate was not stable

### Homework 7

- Comparable periods: 50 conversations and 53 traces in each period
- Before: 7/10 random traces flagged; corrected prevalence 72.24%, 95% CI
  0%-100%
- After: 9/10 random traces flagged; corrected prevalence 100%, 95% CI
  59.29%-100%
- Operational 24-hour run: 91 traces across 88 conversations; corrected
  prevalence 88.44%, 95% CI 33.33%-100%
- Automation: successful workflow
  [36467153998](https://github.com/SCRKT/cartwheel-homeworks/actions/runs/36467153998),
  retained artifact, idempotent score IDs, and a three-widget Langfuse dashboard
- Interpretation: the point estimates exceed the 15% threshold, but the wide
  intervals do not support a precise population estimate. The recommended next
  step is to ship the concise-response constraint, expand the random sample,
  label fresh examples, and recalibrate the judge.

## Open items

1. Confirm whether the instructor accepts screenshot PDFs in place of the seven
   requested videos.
2. HW7's successful GitHub Actions run contains a non-blocking warning that
   several third-party actions still target Node.js 20. Upgrade those actions
   when compatible releases are available.
3. Wait for the course repository to release Homework 8. As of this audit,
   upstream `main` and all upstream branch names contain no HW8 assignment.
