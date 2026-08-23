"""Equivalence test: our LM in max mode must match upstream's exactly.

This is the strongest form of the CP-3 gate. Rather than comparing the
reduction in isolation, it drives the real `_update_evidence_with_vote` on both
upstream's `EvidenceGraphLM` and our `ConsensusEvidenceGraphLM`, with identical
inputs, and requires the resulting hypothesis evidence to be bit-identical.

If this passes, any accuracy difference measured later is attributable to the
vote rule and not to the transcription.
"""
import numpy as np
import pytest

from tbp.monty.frameworks.models.evidence_matching.learning_module import (
    EvidenceGraphLM,
)

from polybrains.learning_module import ConsensusEvidenceGraphLM
from polybrains.weights import AdaptiveVoteWeight


def _frozen_w():
    """Weight object matching upstream's constant, for the baseline arm."""
    return AdaptiveVoteWeight(w_init=1.0, frozen=True)

RNG = np.random.default_rng(20260818)


class _FakeVote:
    """Minimal stand-in for a CMP Message, carrying only what the method reads."""

    def __init__(self, location, confidence):
        self.location = location
        self.confidence = confidence


class _FakeHyps:
    def __init__(self, locations, evidence):
        self.locations = locations
        self.evidence = evidence


def _make_lm(cls, n_hyps, n_votes, seed, **kwargs):
    """Build a bare instance and inject only the state the method touches.

    EvidenceGraphLM.__init__ pulls in a lot of machinery that is irrelevant
    here, so we bypass it with __new__ and set the handful of attributes
    _update_evidence_with_vote actually reads.
    """
    rng = np.random.default_rng(seed)
    lm = cls.__new__(cls)
    lm.past_weight = 0.5
    lm.present_weight = 0.5
    lm.vote_weight = 1.0
    # read by _get_node_distance_weights; sets the radius outside which a vote
    # is masked out. 0.05 leaves a realistic mix of in- and out-of-radius votes
    # given the +/-0.1 coordinate range below.
    lm.max_match_distance = 0.05
    locations = rng.uniform(-0.1, 0.1, size=(n_hyps, 3))
    evidence = rng.uniform(-1, 1, size=n_hyps)
    lm._hypotheses = {"obj": _FakeHyps(locations, evidence.copy())}
    lm.max_nneighbors = 3
    # attributes only our subclass uses
    for k, v in kwargs.items():
        setattr(lm, k, v)
    return lm


def _make_votes(n_votes, seed):
    rng = np.random.default_rng(seed + 991)
    return [
        _FakeVote(rng.uniform(-0.1, 0.1, size=3), float(rng.uniform(-1, 1)))
        for _ in range(n_votes)
    ]


@pytest.mark.parametrize("seed", [0, 1, 2, 7, 42])
@pytest.mark.parametrize("n_votes", [1, 2, 5, 20])
def test_max_mode_matches_upstream_evidence_exactly(seed, n_votes):
    n_hyps = 30

    up = _make_lm(EvidenceGraphLM, n_hyps, n_votes, seed)
    ours = _make_lm(
        ConsensusEvidenceGraphLM,
        n_hyps,
        n_votes,
        seed,
        vote_mode="max",
        consensus_tau=0.15,
        record_dissent=True,
        dissent_history=[],
        capture_history=[],
        last_dissent=None,
        adaptive_weight=False,
        _w=_frozen_w(),
    )

    votes = _make_votes(n_votes, seed)

    up._update_evidence_with_vote(votes, "obj")
    ours._update_evidence_with_vote(list(votes), "obj")

    a = np.ma.filled(up._hypotheses["obj"].evidence, np.nan)
    b = np.ma.filled(ours._hypotheses["obj"].evidence, np.nan)
    assert np.array_equal(a, b), "max mode diverged from upstream"


@pytest.mark.parametrize("seed", [0, 3, 11])
def test_consensus_mode_actually_differs(seed):
    """Sanity: the knob must do something, or the experiment is vacuous."""
    n_hyps, n_votes = 30, 12

    as_max = _make_lm(
        ConsensusEvidenceGraphLM, n_hyps, n_votes, seed,
        vote_mode="max", consensus_tau=0.15, record_dissent=False,
        dissent_history=[], capture_history=[], last_dissent=None,
        adaptive_weight=False, _w=_frozen_w(),
    )
    as_cons = _make_lm(
        ConsensusEvidenceGraphLM, n_hyps, n_votes, seed,
        vote_mode="consensus", consensus_tau=0.15, record_dissent=False,
        dissent_history=[], capture_history=[], last_dissent=None,
        adaptive_weight=False, _w=_frozen_w(),
    )

    votes = _make_votes(n_votes, seed)
    as_max._update_evidence_with_vote(list(votes), "obj")
    as_cons._update_evidence_with_vote(list(votes), "obj")

    a = np.ma.filled(as_max._hypotheses["obj"].evidence, np.nan)
    b = np.ma.filled(as_cons._hypotheses["obj"].evidence, np.nan)
    assert not np.array_equal(a, b), "consensus mode changed nothing"


def test_dissent_is_recorded():
    lm = _make_lm(
        ConsensusEvidenceGraphLM, 30, 10, 5,
        vote_mode="consensus", consensus_tau=0.15, record_dissent=True,
        dissent_history=[], capture_history=[], last_dissent=None,
        adaptive_weight=False, _w=_frozen_w(),
    )
    lm._update_evidence_with_vote(_make_votes(10, 5), "obj")
    assert lm.last_dissent is not None
    assert 0.0 <= lm.last_dissent <= 1.0
    summary = lm.dissent_summary()
    assert summary["n_steps"] == 1
    assert summary["vote_mode"] == "consensus"


def test_capture_rate_is_one_under_max_in_situ():
    """Instrumentation check against the real method, not a synthetic array."""
    lm = _make_lm(
        ConsensusEvidenceGraphLM, 40, 15, 9,
        vote_mode="max", consensus_tau=0.15, record_dissent=True,
        dissent_history=[], capture_history=[], last_dissent=None,
        adaptive_weight=False, _w=_frozen_w(),
    )
    lm._update_evidence_with_vote(_make_votes(15, 9), "obj")
    assert lm.dissent_summary()["mean_capture_rate"] == pytest.approx(1.0)


class TestAdaptiveWeightWiring:
    """CP-4 wired into the LM: the weight must reach the blend, and the
    ablation must remain exactly upstream."""

    def _lm(self, adaptive, seed=13):
        return _make_lm(
            ConsensusEvidenceGraphLM, 30, 10, seed,
            vote_mode="max", consensus_tau=0.15, record_dissent=False,
            dissent_history=[], capture_history=[], last_dissent=None,
            adaptive_weight=adaptive,
            _w=AdaptiveVoteWeight(w_init=1.0, frozen=not adaptive),
        )

    def test_ablation_uses_upstream_constant(self):
        lm = self._lm(adaptive=False)
        assert lm.effective_vote_weight == pytest.approx(lm.vote_weight)

    def test_adaptive_weight_changes_after_ood_failures(self):
        lm = self._lm(adaptive=True)
        before = lm.effective_vote_weight
        for _ in range(50):
            lm.record_episode_outcome(was_correct=False)
        assert lm.effective_vote_weight < before
        assert lm.effective_vote_weight > 0.0, "never silenced"

    def test_in_domain_outcomes_do_not_move_the_weight(self):
        lm = self._lm(adaptive=True)
        before = lm.effective_vote_weight
        for _ in range(50):
            lm.record_episode_outcome(was_correct=True, out_of_domain=False)
        assert lm.effective_vote_weight == pytest.approx(before)

    def test_adaptive_weight_actually_reaches_the_evidence(self):
        """A quieter module must produce different evidence, or the wiring is
        decorative."""
        votes = _make_votes(10, 13)

        loud = self._lm(adaptive=True)
        quiet = self._lm(adaptive=True)
        for _ in range(80):
            quiet.record_episode_outcome(was_correct=False)
        assert quiet.effective_vote_weight < loud.effective_vote_weight

        loud._update_evidence_with_vote(list(votes), "obj")
        quiet._update_evidence_with_vote(list(votes), "obj")
        a = np.ma.filled(loud._hypotheses["obj"].evidence, np.nan)
        b = np.ma.filled(quiet._hypotheses["obj"].evidence, np.nan)
        assert not np.array_equal(a, b), "w(t) never reached the blend"
