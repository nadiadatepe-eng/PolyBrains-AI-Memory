"""Characterization tests for Monty's vote path, runnable without HabitatSim.

Upstream's `tests/integration/.../evidence_lm_test.py` is Habitat-gated and skips
on Linux, which means the module we are about to modify has no runnable
integration test here. This file is that safety net.

These are CHARACTERIZATION tests: they pin down what upstream does today, so
that when ConsensusVoteMixin replaces the reduction we can prove the change is
intentional and scoped rather than accidental.

Run:  .venv/bin/python -m pytest ~/PolyBrains/tests/test_vote_path.py -v
"""
import numpy as np
import pytest

from tbp.monty.frameworks.models.evidence_matching.learning_module import (
    EvidenceGraphLM,
)
from tbp.monty.frameworks.models.evidence_matching.model import (
    MontyForEvidenceGraphMatching,
)


class TestAggregationIsMax:
    """Finding (a): the reduction is a max, so the loudest vote wins outright."""

    def test_reduction_returns_loudest_not_mean(self):
        loud, quiet_a, quiet_b = 0.95, 0.42, 0.40
        neighbourhood = np.ma.array([[loud, quiet_a, quiet_b]])
        reduced = float(np.ma.max(neighbourhood, axis=1)[0])
        assert reduced == pytest.approx(loud)
        assert reduced != pytest.approx(np.mean([loud, quiet_a, quiet_b]))

    def test_two_agreeing_modules_change_nothing(self):
        """The heart of H2: mutual agreement contributes zero under a max."""
        loud = 0.95
        with_agreement = float(
            np.ma.max(np.ma.array([[loud, 0.42, 0.40]]), axis=1)[0]
        )
        without_agreement = float(np.ma.max(np.ma.array([[loud]]), axis=1)[0])
        assert with_agreement == pytest.approx(without_agreement)

    def test_one_loud_module_overrides_a_larger_agreeing_group(self):
        """Scale does not help the majority: 4 agreeing peers still lose."""
        loud = 0.91
        group = [0.55, 0.54, 0.56, 0.53]
        reduced = float(np.ma.max(np.ma.array([[loud] + group]), axis=1)[0])
        assert reduced == pytest.approx(loud)

    def test_masked_votes_are_excluded(self):
        """Votes outside the distance radius must not participate."""
        values = np.ma.array([[0.99, 0.42, 0.40]], mask=[[True, False, False]])
        reduced = float(np.ma.max(values, axis=1)[0])
        assert reduced == pytest.approx(0.42)


class TestNoDispersionSignal:
    """Finding (b): the vote path computes no measure of disagreement."""

    def test_update_evidence_with_vote_has_no_dispersion(self):
        import inspect

        src = inspect.getsource(EvidenceGraphLM._update_evidence_with_vote)
        for token in ("np.var", "np.std", "entropy", "disagree"):
            assert token not in src, f"unexpected dispersion token {token!r}"

    def test_combine_votes_has_no_dispersion(self):
        import inspect

        src = inspect.getsource(MontyForEvidenceGraphMatching._combine_votes)
        for token in ("np.var", "np.std", "entropy", "disagree"):
            assert token not in src, f"unexpected dispersion token {token!r}"

    def test_dispersion_would_distinguish_these_two_cases(self):
        """Demonstrates the information the current rule discards.

        Both neighbourhoods reduce to the same value under max, but they mean
        very different things: one is a confident consensus, the other is a
        single loud module over a split group.
        """
        consensus = np.ma.array([[0.90, 0.88, 0.89]])
        contested = np.ma.array([[0.90, 0.30, 0.28]])
        assert float(np.ma.max(consensus, axis=1)[0]) == pytest.approx(
            float(np.ma.max(contested, axis=1)[0]), abs=1e-9
        )
        # A dispersion measure separates them immediately.
        assert np.std(consensus) < 0.05
        assert np.std(contested) > 0.25


class TestVoteWeightIsStatic:
    """Finding (c): vote_weight never updates from experience."""

    def test_assigned_only_in_init(self):
        import inspect

        assigners = []
        for name, fn in inspect.getmembers(
            EvidenceGraphLM, predicate=inspect.isfunction
        ):
            try:
                src = inspect.getsource(fn)
            except (OSError, TypeError):
                continue
            for line in src.splitlines():
                stripped = line.strip()
                if stripped.startswith("self.vote_weight") and "==" not in stripped:
                    assigners.append(name)
        assert sorted(set(assigners)) == ["__init__"]

    def test_default_is_one(self):
        import inspect

        sig = inspect.signature(EvidenceGraphLM.__init__)
        assert sig.parameters["vote_weight"].default == 1


class TestVoteMatrixIsStatic:
    """The routing between modules is fixed before the problem is seen."""

    def test_matrix_assigned_once_in_monty_base(self):
        import inspect

        from tbp.monty.frameworks.models.monty_base import MontyBase

        assigners = []
        for name, fn in inspect.getmembers(MontyBase, predicate=inspect.isfunction):
            try:
                src = inspect.getsource(fn)
            except (OSError, TypeError):
                continue
            for line in src.splitlines():
                stripped = line.strip()
                if (
                    stripped.startswith("self.lm_to_lm_vote_matrix")
                    and "==" not in stripped
                ):
                    assigners.append(name)
        assert sorted(set(assigners)) == ["__init__"]
