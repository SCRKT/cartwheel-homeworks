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
