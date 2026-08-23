"""Iterated voting: vote, then vote on the result of that vote.

Nadi's question (2026-08-19): what if we vote on an already-voted result?

## The bug this file was rewritten to fix (2026-08-19)

The first version transcribed the vote loop from `monty_base.py:302`. That is
the WRONG `_vote`. `MontyForGraphMatching` overrides it at
`graph_matching.py:389`, and that override is what actually runs, because
`MontyForEvidenceGraphMatching` inherits from it. The real one does three
things the base one does not:

    votes_per_lm    = [lm.send_out_vote() for lm in self.learning_modules]
    combined_votes  = self._combine_votes(votes_per_lm)   # <-- transforms votes
    for i, lm ...   : self.send_vote_to_lm(lm, i, combined_votes)
                      self.update_stats_after_vote(lm)

`_combine_votes` (evidence_matching/model.py:38) transforms each sender's votes
into the receiver's reference frame using the sensor displacement between them.
Skipping it means `receive_votes` is called with raw, untransformed vote lists,
and the evidence update is a no-op.

Consequence: the entire first P9 sweep exchanged NO votes in ANY round --
including rounds=1 -- while completing without error and producing plausible
numbers. It was caught by the pre-registered replication control (rounds=1 came
out +3.60 pp from P7's max arm instead of 0.00) and confirmed by a probe showing
zero evidence change per round.

The lesson generalises: overriding a method requires checking the MRO for which
class actually defines it, not the one that happens to be easiest to read.

## The mechanism

Iteration works without touching the vote rule because `receive_votes` mutates
the receiving module's evidence (`learning_module.py:902`
`_update_evidence_with_vote` writes `graph_hyps.evidence`). Calling the whole
block again makes `send_out_vote()` read the ALREADY-VOTED evidence, so round 2
votes on round 1's result rather than re-tallying the same votes.

## Contract

Upstream is read-only, so this is a subclass in our own layer overriding one
method. `vote_rounds=1` must be upstream's `_vote` call-for-call; that is gated
by `tests/test_iterated_vote.py` against a transcription of the REAL parent, and
by `tests/probe_p9_dead_rounds.py` which asserts non-zero evidence movement.
"""

from __future__ import annotations

import logging

from tbp.monty.frameworks.models.evidence_matching.model import (
    MontyForEvidenceGraphMatching,
)

logger = logging.getLogger(__name__)


class IteratedVotingMonty(MontyForEvidenceGraphMatching):
    """Monty that repeats the full vote exchange `vote_rounds` times per step.

    Args:
        vote_rounds: number of gather-combine-scatter exchanges per step.
            ``1`` reproduces upstream exactly. Must be >= 1.

    Attributes:
        vote_round_stats: one entry per round per step,
            ``(round_index, n_voting, n_silent)``. `send_out_vote()` returning
            ``None`` is an abstention, and P6 established that silence and
            disagreement look identical in output statistics while being
            opposite at the mechanism -- so silence is recorded, not inferred.
    """

    def __init__(self, *args, vote_rounds: int = 1, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if vote_rounds < 1:
            raise ValueError(f"vote_rounds must be >= 1, got {vote_rounds}")
        self.vote_rounds = vote_rounds
        self.vote_round_stats: list[tuple[int, int, int]] = []

    def _vote(self) -> None:
        """Repeat the REAL vote exchange (graph_matching.py:389) N times.

        Each round re-reads state from the modules, so round r>1 votes on the
        result of round r-1. The final possible-matches logging runs once at the
        end, exactly as upstream does it, rather than once per round.
        """
        if self.lm_to_lm_vote_matrix is not None:
            for r in range(self.vote_rounds):
                votes_per_lm = []
                silent = 0
                for lm in self.learning_modules:
                    v = lm.send_out_vote()
                    if v is None:
                        silent += 1
                    votes_per_lm.append(v)

                self.vote_round_stats.append(
                    (r, len(self.learning_modules) - silent, silent)
                )

                # The step the first version omitted: transform each sender's
                # votes into the receiver's reference frame.
                combined_votes = self._combine_votes(votes_per_lm)

                for i, lm in enumerate(self.learning_modules):
                    self.send_vote_to_lm(lm, i, combined_votes)
                    self.update_stats_after_vote(lm)

        # Upstream logs possible matches after voting, outside the vote guard.
        for lm in self.learning_modules:
            pm = (
                lm.get_possible_matches()
                if lm.buffer.get_num_observations_on_object()
                else []
            )
            logger.info(f"Possible matches for {lm.learning_module_id}: {pm}")

    def vote_round_summary(self) -> dict:
        """Silence rate per round -- mandatory alongside any accuracy number.

        If silence CLIMBS with rounds, modules are dropping out rather than
        converging, and any accuracy change is that instead of consensus (P6).
        """
        if not self.vote_round_stats:
            return {}
        out = {}
        for r in range(self.vote_rounds):
            rows = [s for s in self.vote_round_stats if s[0] == r]
            if not rows:
                continue
            total = sum(v + s for _, v, s in rows)
            silent = sum(s for _, _, s in rows)
            out[f"round_{r + 1}_send_none_pct"] = (
                100.0 * silent / total if total else 0.0
            )
        return out
