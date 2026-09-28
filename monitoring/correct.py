"""Bias-corrected failure prevalence for a monitoring period."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def corrected_mode_prevalence(
    sample_preds: Sequence[int],
    test_labels: Sequence[int],
    test_preds: Sequence[int],
    confidence: float = 0.95,
    bootstrap_iterations: int = 20000,
    seed: int | None = 7,
) -> dict[str, Any]:
    """Bias-corrected live prevalence for one mode from sampled verdicts.

    The contract, precisely:

      1. ``raw`` is the uncorrected flag rate: ``mean(sample_preds)``.
      2. Compute the frozen judge's failure sensitivity and pass specificity
         from ``test_labels`` and ``test_preds``. Both use the monitoring
         convention that 1 means a failure is present. Failure sensitivity is
         the flagged fraction of human-labeled failures. Pass specificity is
         the unflagged fraction of human-labeled passes.
      3. Compute the Rogan-Gladen point estimate, then resample the held-out
         records and sampled predictions to obtain a percentile-bootstrap
         interval. Use a seeded NumPy generator so the committed result is
         reproducible.
      4. Resample the monitoring predictions and the paired held-out records
         independently with replacement. Keep their original sample sizes.
         Discard a draw if the correction cannot be computed. Clamp each
         retained estimate to [0, 1], then take the percentile interval.
         Raise ``ValueError`` if no replicate is valid.

    Args:
        sample_preds: the judge's 0/1 verdicts over the UNIFORM BASE sample
            only (never the risk strata; they are biased toward failure by
            design).
        test_labels: human labels for the frozen Homework 5 judge's test
            split.
        test_preds: the frozen judge's predictions on that test split.
        confidence: interval confidence level.
        bootstrap_iterations: number of percentile-bootstrap replicates.
        seed: numpy seed for a reproducible interval; None leaves the RNG
            untouched.

    Returns:
        {"raw", "corrected", "ci_low", "ci_high", "confidence",
         "failure_sensitivity", "pass_specificity", "n_sample"}
        with "corrected" clamped to [0, 1] and rates rounded to 4 places.

    Raises:
        ValueError: if an input is empty, the held-out inputs have different
            lengths, a value is not 0 or 1, a class is absent, the judge is
            missing a usable correction, or no bootstrap replicate is valid.
    """
    sample = np.asarray(sample_preds)
    labels = np.asarray(test_labels)
    predictions = np.asarray(test_preds)

    if not len(sample) or not len(labels) or not len(predictions):
        raise ValueError("prediction and held-out inputs must not be empty")
    if len(labels) != len(predictions):
        raise ValueError("held-out labels and predictions must have equal lengths")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    if bootstrap_iterations < 1:
        raise ValueError("bootstrap_iterations must be at least 1")
    if any(value not in (0, 1) for value in sample):
        raise ValueError("sample predictions must contain only 0 and 1")
    if any(value not in (0, 1) for value in labels):
        raise ValueError("test labels must contain only 0 and 1")
    if any(value not in (0, 1) for value in predictions):
        raise ValueError("test predictions must contain only 0 and 1")

    def correction(
        live_predictions: np.ndarray,
        held_out_labels: np.ndarray,
        held_out_predictions: np.ndarray,
    ) -> tuple[float, float, float, float] | None:
        failures = held_out_labels == 1
        passes = held_out_labels == 0
        if not failures.any() or not passes.any():
            return None
        sensitivity = float(held_out_predictions[failures].mean())
        specificity = float(1 - held_out_predictions[passes].mean())
        denominator = sensitivity + specificity - 1
        if denominator <= 0:
            return None
        raw = float(live_predictions.mean())
        corrected = (raw + specificity - 1) / denominator
        return raw, corrected, sensitivity, specificity

    point = correction(sample, labels, predictions)
    if point is None:
        raise ValueError("the held-out judge has no usable prevalence correction")
    raw, corrected, sensitivity, specificity = point

    rng = np.random.default_rng(seed)
    bootstrapped: list[float] = []
    for _ in range(bootstrap_iterations):
        live_indices = rng.integers(0, len(sample), size=len(sample))
        test_indices = rng.integers(0, len(labels), size=len(labels))
        replicate = correction(
            sample[live_indices], labels[test_indices], predictions[test_indices]
        )
        if replicate is not None:
            bootstrapped.append(float(np.clip(replicate[1], 0, 1)))
    if not bootstrapped:
        raise ValueError("no valid bootstrap replicate could be computed")

    tail = (1 - confidence) / 2
    ci_low, ci_high = np.quantile(bootstrapped, [tail, 1 - tail])
    return {
        "raw": round(raw, 4),
        "corrected": round(float(np.clip(corrected, 0, 1)), 4),
        "ci_low": round(float(ci_low), 4),
        "ci_high": round(float(ci_high), 4),
        "confidence": confidence,
        "failure_sensitivity": round(sensitivity, 4),
        "pass_specificity": round(specificity, 4),
        "n_sample": len(sample),
    }
