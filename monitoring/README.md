# Homework 7 monitoring result

The frozen `overinformative_response-v0` judge monitored the same 50 scenarios
on `gpt-5.6-luna` in both periods. The 20% uniform samples estimate prevalence;
the `policy_lookup` group is a separate inspection slice.

## Did the corrected estimate move?

Yes. The random-sample raw flag rate increased from 70% (7/10) before to 90%
(9/10) after. Correction for the frozen judge's 0.8333 failure sensitivity and
0.6471 pass specificity moved the estimates from 0.7224 to 1.0, an increase of
0.2776. The after estimate is capped at the valid upper bound.

## Do the intervals support a conclusion?

The direction is worse, but the result is uncertain. The 95% bootstrap
intervals overlap substantially: 0.0–1.0 before and 0.5929–1.0 after. Ten
random conversations per period and an imperfect held-out judge are not enough
to claim that the underlying failure rate increased.

## What did the risk group reveal?

Policy-lookup conversations increased from 8 to 10. The judge flagged 5/8
(62.5%) before and 7/10 (70%) after. Those rates are lower than the corresponding
uniform-sample rates, so the signal is not concentrated in policy lookups. The
flagged policy traces are still useful examples for review, while only the
uniform samples support an overall prevalence estimate.

## What happens after a threshold crossing?

Both point estimates exceed the precommitted 0.15 threshold. Start a new error
analysis on the flagged traces and have a human confirm each candidate because
this judge was approved only for triage. Turn confirmed failures into new
Homework 6 evaluation cases before changing or enforcing agent behavior.

## Operational evidence

- Langfuse dashboard: [HW7 Overinformative Response Monitor](http://localhost:3000/project/cartwheel-dev/dashboards/cmullpxhx000fsc072jm9t4l9)
- Successful manual workflow: [behavior monitor run 36467153998](https://github.com/SCRKT/cartwheel-homeworks/actions/runs/36467153998)
- The manual 24-hour run grouped 91 traces into 88 conversations, judged 30
  unique records, wrote 33 scores, and uploaded the history, latest result, and
  prevalence chart as workflow artifact `behavior-monitor-36467153998`.
- The repository-scoped `cartwheel-mac` runner keeps the local Langfuse host
  reachable for scheduled runs.
