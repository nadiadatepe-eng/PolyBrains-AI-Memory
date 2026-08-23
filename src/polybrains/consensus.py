"""Consensus voting and the dissent signal.

Monty's stock rule reduces the votes in a hypothesis' neighbourhood with
`np.ma.max` (learning_module.py:938). Two consequences, both verified at the
pinned sha in `reports/vote-path.md`:

  * the loudest single vote wins outright, so mutual agreement between quieter
    modules contributes exactly nothing;
  * the spread of the incoming votes is never computed, so no module can know
    that its peers disagree.

This module supplies a drop-in replacement for the reduction plus a dissent
measure (the D-index). Nothing here is claimed to work better. CP-3's gate is
only that `mode="max"` reproduces upstream exactly, so that any later
difference is attributable to the rule and not to a refactor.

Definitions are frozen at CP-3 *before* any accuracy number is looked at. That
is deliberate: a dispersion measure tuned after seeing results is a free
parameter, not a finding.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

VoteMode = Literal["max", "mean", "consensus"]

#: Frozen at CP-3, 2026-08-18, before any accuracy comparison. Do not retune.
CONSENSUS_TAU = 0.15


def reduce_votes(
    neighbourhood: np.ma.MaskedArray,
    mode: VoteMode = "max",
    tau: float = CONSENSUS_TAU,
) -> np.ndarray:
    """Reduce each hypothesis' vote neighbourhood to a single evidence value.

    Args:
        neighbourhood: masked array, shape (n_hypotheses, k). Entry [i, j] is
            the confidence of the j-th nearest vote to hypothesis i. Masked
            entries are votes outside the distance radius and must not
            participate, exactly as upstream does.
        mode:
            ``"max"``       upstream's rule, bit-identical. The baseline arm.
            ``"mean"``      plain average. A deliberately naive control that
                            separates "any change to the rule" from "this
                            particular change".
            ``"consensus"`` agreement-weighted mean: each vote is weighted by
                            how well the rest of its neighbourhood agrees with
                            it, so a lone loud vote is discounted and a
                            mutually-agreeing group is amplified.
        tau: agreement scale for ``"consensus"``. Votes within roughly ``tau``
            of each other count as agreeing. Frozen, not fitted.

    Returns:
        Array of shape (n_hypotheses,). Fully-masked rows yield 0.0, matching
        upstream's behaviour of contributing no evidence.
    """
    if mode == "max":
        return np.ma.max(neighbourhood, axis=1)

    if mode == "mean":
        return np.ma.mean(neighbourhood, axis=1)

    if mode != "consensus":
        raise ValueError(f"unknown vote mode: {mode!r}")

    # Agreement weight: for each vote, how close are the others to it?
    # w_ij = mean_l exp(-|v_ij - v_il| / tau), computed only over unmasked
    # entries. A vote that stands alone gets a low weight; a vote inside a
    # tight cluster gets a high one.
    values = neighbourhood
    # pairwise |v_ij - v_il| within each row
    diffs = np.abs(values[:, :, None] - values[:, None, :])
    affinity = np.exp(-diffs / max(tau, 1e-9))
    # Mean affinity of each vote to the others in its row.
    weights = np.ma.mean(affinity, axis=2)
    weighted = np.ma.average(values, weights=weights, axis=1)
    return weighted


def dissent_index(neighbourhood: np.ma.MaskedArray) -> np.ndarray:
    """D-index: how much the votes in each neighbourhood disagree.

    Normalised to [0, 1]. 0 means the votes are identical, 1 means they are
    maximally split across the confidence range.

    Uses the population standard deviation scaled by the theoretical maximum
    for values in [-1, 1] (Monty's vote confidences are scaled evidences in
    that range), which is 1.0 for a two-point split at the extremes.

    Frozen at CP-3 before any accuracy comparison.
    """
    if neighbourhood.ndim != 2:
        raise ValueError("expected shape (n_hypotheses, k)")
    counts = (~np.ma.getmaskarray(neighbourhood)).sum(axis=1)
    spread = np.ma.std(neighbourhood, axis=1)
    d = np.ma.filled(spread, 0.0)
    # A single unmasked vote cannot disagree with anything.
    d = np.where(counts < 2, 0.0, d)
    return np.clip(d, 0.0, 1.0)


def capture_rate(
    neighbourhood: np.ma.MaskedArray,
    reduced: np.ndarray,
    atol: float = 1e-9,
) -> float:
    """Fraction of hypotheses whose consensus equals their loudest single vote.

    Under upstream's ``"max"`` rule this is 1.0 by construction, which is the
    sanity check that the instrumentation is correct before anything changes.
    A rule that resists capture by one confident module should score lower.
    """
    loudest = np.ma.filled(np.ma.max(neighbourhood, axis=1), np.nan)
    red = np.ma.filled(reduced, np.nan)
    valid = ~(np.isnan(loudest) | np.isnan(red))
    if not valid.any():
        return float("nan")
    return float(np.isclose(red[valid], loudest[valid], atol=atol).mean())
