"""CP-3 gate: prove the refactor is behaviour-preserving before trusting it.

The gate has three parts:

1. `mode="max"` must be BIT-IDENTICAL to upstream's `np.ma.max(..., axis=1)`
   across randomised inputs including masks. If it is not, any later accuracy
   difference could be a refactor artefact rather than the rule change.
2. Capture rate must be 1.0 under `"max"`. That is true by construction, so it
   is the check that the instrumentation itself is correct.
3. The D-index must behave sanely at its boundaries.

Run:  .venv/bin/python -m pytest ~/PolyBrains/tests/test_consensus.py -v
"""
import numpy as np
import pytest

from polybrains.consensus import (
    CONSENSUS_TAU,
    capture_rate,
    dissent_index,
    reduce_votes,
)

RNG = np.random.default_rng(20260818)


def _random_neighbourhood(rows=40, k=3, mask_p=0.0):
    vals = RNG.uniform(-1.0, 1.0, size=(rows, k))
    if mask_p > 0:
        mask = RNG.random((rows, k)) < mask_p
        # keep at least one unmasked entry per row, as upstream's radius does
        mask[np.arange(rows), RNG.integers(0, k, rows)] = False
    else:
        mask = np.zeros((rows, k), dtype=bool)
    return np.ma.array(vals, mask=mask)


class TestGateBehaviourPreserving:
    """Part 1: max mode must reproduce upstream exactly."""

    @pytest.mark.parametrize("mask_p", [0.0, 0.2, 0.5])
    @pytest.mark.parametrize("k", [1, 2, 3, 5])
    def test_max_is_bit_identical_to_upstream(self, mask_p, k):
        n = _random_neighbourhood(rows=60, k=k, mask_p=mask_p)
        upstream = np.ma.max(n, axis=1)
        ours = reduce_votes(n, mode="max")
        assert np.array_equal(
            np.ma.filled(upstream, np.nan), np.ma.filled(ours, np.nan)
        )

    def test_max_preserves_mask_semantics(self):
        n = np.ma.array([[0.99, 0.42]], mask=[[True, False]])
        assert float(reduce_votes(n, "max")[0]) == pytest.approx(0.42)


class TestGateInstrumentation:
    """Part 2: capture rate must be 1.0 under max, or our metric is wrong."""

    @pytest.mark.parametrize("mask_p", [0.0, 0.3])
    def test_capture_rate_is_one_under_max(self, mask_p):
        n = _random_neighbourhood(rows=100, mask_p=mask_p)
        assert capture_rate(n, reduce_votes(n, "max")) == pytest.approx(1.0)

    def test_capture_rate_drops_under_consensus_when_contested(self):
        contested = np.ma.array([[0.95, 0.42, 0.40]] * 20)
        rate = capture_rate(contested, reduce_votes(contested, "consensus"))
        assert rate < 0.5


class TestConsensusBehaviour:
    """What the new rule is supposed to do, stated as tests."""

    def test_lone_loud_vote_is_discounted(self):
        contested = np.ma.array([[0.95, 0.42, 0.40]])
        assert float(reduce_votes(contested, "consensus")[0]) < 0.95

    def test_genuine_agreement_is_preserved(self):
        agreeing = np.ma.array([[0.90, 0.88, 0.89]])
        out = float(reduce_votes(agreeing, "consensus")[0])
        assert out == pytest.approx(0.89, abs=0.02)

    def test_identical_votes_are_unchanged_by_any_mode(self):
        same = np.ma.array([[0.7, 0.7, 0.7]])
        for mode in ("max", "mean", "consensus"):
            assert float(reduce_votes(same, mode)[0]) == pytest.approx(0.7)

    def test_agreeing_majority_beats_lone_voice_unlike_max(self):
        """The behaviour H2 says the stock rule lacks."""
        n = np.ma.array([[0.91, 0.55, 0.54, 0.56, 0.53]])
        assert float(reduce_votes(n, "max")[0]) == pytest.approx(0.91)
        assert float(reduce_votes(n, "consensus")[0]) < 0.70

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError):
            reduce_votes(np.ma.array([[0.1, 0.2]]), mode="nope")


class TestDissentIndex:
    """Part 3: D-index boundaries."""

    def test_identical_votes_give_zero(self):
        n = np.ma.array([[0.5, 0.5, 0.5]])
        assert float(dissent_index(n)[0]) == pytest.approx(0.0)

    def test_split_votes_give_high_value(self):
        n = np.ma.array([[1.0, -1.0]])
        assert float(dissent_index(n)[0]) == pytest.approx(1.0)

    def test_single_vote_cannot_disagree(self):
        n = np.ma.array([[0.9, 0.1]], mask=[[False, True]])
        assert float(dissent_index(n)[0]) == pytest.approx(0.0)

    def test_bounded_in_unit_interval(self):
        n = _random_neighbourhood(rows=200, k=5, mask_p=0.3)
        d = dissent_index(n)
        assert d.min() >= 0.0 and d.max() <= 1.0

    def test_ordering_is_sensible(self):
        tight = np.ma.array([[0.50, 0.52, 0.51]])
        loose = np.ma.array([[0.90, 0.10, 0.50]])
        assert float(dissent_index(tight)[0]) < float(dissent_index(loose)[0])


def test_tau_is_frozen():
    """Guard against silently retuning a pre-registered constant."""
    assert CONSENSUS_TAU == 0.15
