"""CP-4 gate: w(t) must move correctly and never silence a module.

The gate has three parts:

1. w(t) demonstrably moves on a toy task with one deliberately unreliable
   module, and the run log shows it.
2. The two invariants hold: a module is never silenced (w > 0 always), and it
   can recover from the floor. A one-way ratchet would encode the very
   entrenchment the project studies.
3. `frozen=True` never moves, so the ablation arm reproduces upstream exactly.

No accuracy claim is made at CP-4.
"""
import numpy as np
import pytest

from polybrains.weights import (
    EMA_ALPHA,
    W_MAX,
    W_MIN,
    AdaptiveVoteWeight,
)


class TestGateMovesCorrectly:
    """Part 1: the toy task with a known-unreliable module."""

    def test_persistently_wrong_module_gets_quieter(self):
        w = AdaptiveVoteWeight()
        start = w.weight
        for _ in range(50):
            w.update(was_correct=False)
        assert w.weight < start
        assert w.weight == pytest.approx(W_MIN, abs=0.05)

    def test_persistently_right_module_gets_louder(self):
        w = AdaptiveVoteWeight()
        start = w.weight
        for _ in range(50):
            w.update(was_correct=True)
        assert w.weight > start

    def test_two_modules_diverge_on_a_toy_task(self):
        """The demonstration CP-4's gate asks for, with a log."""
        rng = np.random.default_rng(20260818)
        reliable = AdaptiveVoteWeight()
        unreliable = AdaptiveVoteWeight()
        log = []
        for step in range(100):
            # reliable is right 90% of the time OOD, unreliable 20%
            reliable.update(was_correct=rng.random() < 0.9)
            unreliable.update(was_correct=rng.random() < 0.2)
            if step % 25 == 0:
                log.append((step, reliable.weight, unreliable.weight))
        assert reliable.weight > unreliable.weight
        # the separation must be substantial, not noise
        assert reliable.weight - unreliable.weight > 0.5
        # and monotone-ish in the log
        assert log[-1][1] > log[0][1]
        assert log[-1][2] < log[0][2]

    def test_neutral_record_stays_at_init(self):
        """A module with no evidence either way must not drift."""
        w = AdaptiveVoteWeight(w_init=1.0)
        assert w.score == pytest.approx(0.5)
        assert w.weight == pytest.approx(1.0)


class TestInvariantNeverSilenced:
    """Part 2a: 'a beginner without losing intellectual confidence'."""

    def test_weight_never_reaches_zero(self):
        w = AdaptiveVoteWeight()
        for _ in range(1000):
            w.update(was_correct=False)
        assert w.weight > 0.0
        assert w.weight >= W_MIN

    def test_floor_is_strictly_positive(self):
        assert W_MIN > 0.0

    def test_weight_stays_in_bounds_under_random_history(self):
        rng = np.random.default_rng(7)
        w = AdaptiveVoteWeight()
        for _ in range(500):
            w.update(was_correct=bool(rng.integers(0, 2)))
            assert W_MIN <= w.weight <= W_MAX


class TestInvariantCanRecover:
    """Part 2b: no one-way ratchet, or we encode entrenchment."""

    def test_module_at_floor_climbs_back(self):
        w = AdaptiveVoteWeight()
        for _ in range(200):
            w.update(was_correct=False)
        floored = w.weight
        assert floored == pytest.approx(W_MIN, abs=0.02)

        for _ in range(200):
            w.update(was_correct=True)
        assert w.weight > floored
        assert w.weight > 1.0, "must recover past its starting point"

    def test_recovery_is_not_instant(self):
        """Recovery should take evidence, not a single lucky episode."""
        w = AdaptiveVoteWeight()
        for _ in range(200):
            w.update(was_correct=False)
        at_floor = w.weight
        w.update(was_correct=True)
        assert w.weight > at_floor
        assert w.weight < 0.5, "one success must not restore full influence"


class TestInDomainConfidenceBuysNothing:
    """The H2 clause, enforced in the weight mechanism itself."""

    def test_in_domain_success_does_not_raise_weight(self):
        w = AdaptiveVoteWeight()
        start = w.weight
        for _ in range(100):
            w.update(was_correct=True, out_of_domain=False)
        assert w.weight == pytest.approx(start)
        assert w.n_updates == 100

    def test_in_domain_failure_does_not_lower_weight(self):
        w = AdaptiveVoteWeight()
        start = w.weight
        for _ in range(100):
            w.update(was_correct=False, out_of_domain=False)
        assert w.weight == pytest.approx(start)


class TestFrozenAblation:
    """Part 3: the ablation arm must reproduce upstream."""

    def test_frozen_never_moves(self):
        w = AdaptiveVoteWeight(frozen=True)
        for correct in (True, False, True, False):
            for _ in range(50):
                w.update(was_correct=correct)
        assert w.weight == pytest.approx(1.0)
        assert len(set(np.round(w.history, 12))) == 1

    def test_frozen_default_matches_upstream_vote_weight(self):
        """Upstream's default is vote_weight=1."""
        assert AdaptiveVoteWeight(frozen=True).weight == 1.0


class TestConstantsFrozen:
    """Guard against silently retuning pre-registered constants."""

    def test_constants(self):
        assert W_MIN == 0.1
        assert W_MAX == 2.0
        assert EMA_ALPHA == 0.1

    def test_invalid_bounds_rejected(self):
        with pytest.raises(ValueError):
            AdaptiveVoteWeight(w_init=5.0, w_max=2.0)
        with pytest.raises(ValueError):
            AdaptiveVoteWeight(w_min=0.0)
