"""Parliamentary voting: propose, then oppose, then oppose again.

Nadi's design (2026-08-19). Instead of one exchange per step, three phases:

    phase 1  PROPOSE   LMs 0,1,2 vote normally
    phase 2  OPPOSE    LM 3 plays devil's advocate against phase 1
    phase 3  OPPOSE    LM 4 plays devil's advocate against phases 1 and 2

Within a phase modules vote ONE BY ONE: each sees the evidence updates caused by
the modules before it, so ordering is a real variable.

## What "devil's advocate" means concretely

A vote is a per-hypothesis `Message` carrying a `confidence`, built in
`send_out_vote` (learning_module.py:403) from the sender's own scaled evidence.
A normal voter sends hypotheses for every object above `vote_evidence_threshold`,
which is dominated by its best-supported object.

An opposing module instead sends votes for its **runner-up object** -- the object
with the second-highest total evidence -- and withholds its best. It argues the
case it does NOT believe, which is what makes it an advocate for the devil rather
than merely a quiet voter.

This is deliberately the mildest of the three possible readings. It changes WHICH
hypotheses are argued, not the sign or magnitude of evidence, so it needs no
change to the reduction rule and cannot smuggle in an unrelated effect. Veto
(negative evidence) and abstain-if-agree are the other two readings, left for
later if this one shows signal.

## The risk, recorded before any result

The reduction is `np.ma.max` (learning_module.py:938): the loudest vote in a
neighbourhood wins outright. **Max cannot represent opposition, only volume.** A
dissenting vote is simply a lower number that loses. If P10 shows no effect, this
is the first thing to check -- and it would be a finding about the aggregation
rule, not about parliaments.

Pre-registered at 5b8d64f, before this file was written.

## Contract

Upstream is read-only. This subclasses the same parent as P9 and overrides
`_vote` only, calling the REAL parent's helpers (`_combine_votes`,
`send_vote_to_lm`, `update_stats_after_vote`) -- the P9 bug was transcribing
`monty_base.py:302` when `graph_matching.py:389` is what runs.
"""

from __future__ import annotations

import logging

import numpy as np

from tbp.monty.frameworks.models.evidence_matching.model import (
    MontyForEvidenceGraphMatching,
)

logger = logging.getLogger(__name__)


class ParliamentaryMonty(MontyForEvidenceGraphMatching):
    """Monty with propose/oppose phases and sequential within-phase voting.

    Args:
        phases: list of lists of LM indices, one per phase, in voting order.
            Default ``[[0,1,2],[3],[4]]``.
        opposing_phases: indices into `phases` whose members argue their
            runner-up hypothesis instead of their best. Default ``[1, 2]``.
            Set to ``[]`` for the no-opposition structural control.
        sequential: if True (default) modules within a phase vote one at a time,
            each seeing prior updates. If False the phase is a single batch,
            which isolates the effect of sequencing.

    Attributes:
        phase_stats: ``(phase_ix, n_voting, n_silent, opposed)`` per phase per
            step. Silence is recorded rather than inferred: P6 established that
            an absent module and a dissenting one look identical in output
            statistics while being opposite at the mechanism.
    """

    def __init__(
        self,
        *args,
        phases: list[list[int]] | None = None,
        opposing_phases: list[int] | None = None,
        sequential: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.phases = [list(p) for p in (phases or [[0, 1, 2], [3], [4]])]
        self.opposing_phases = (
            list(opposing_phases) if opposing_phases is not None else [1, 2]
        )
        self.sequential = sequential
        self.phase_stats: list[tuple[int, int, int, bool]] = []

    # ------------------------------------------------------------------ #

    def _runner_up_vote(self, lm):
        """Ask `lm` for a vote arguing its SECOND-best object.

        Implemented by temporarily hiding the best-supported object's
        hypotheses, so the module's own `send_out_vote` runs unmodified and
        produces a structurally valid vote for its runner-up. Restoring
        afterwards leaves the module exactly as found -- this must not be a
        covert evidence edit.

        Returns None if the module has fewer than two objects to choose
        between, in which case it simply abstains this phase.
        """
        hyps = getattr(lm, "_hypotheses", None)
        if not isinstance(hyps, dict) or len(hyps) < 2:
            return lm.send_out_vote()

        totals = {}
        for gid, h in hyps.items():
            ev = getattr(h, "evidence", None)
            if ev is None or len(ev) == 0:
                continue
            totals[gid] = float(np.max(ev))
        if len(totals) < 2:
            return lm.send_out_vote()

        best = max(totals, key=totals.get)
        saved = hyps.pop(best)
        try:
            vote = lm.send_out_vote()
        finally:
            hyps[best] = saved
        return vote

    def _run_phase(self, phase_ix, lm_ids, oppose):
        """One phase: gather votes from `lm_ids`, combine, deliver.

        Sequential mode runs one voter at a time so later voters in the phase
        see the evidence the earlier ones caused.
        """
        groups = [[i] for i in lm_ids] if self.sequential else [list(lm_ids)]

        for group in groups:
            # IMPORTANT: `_combine_votes` (evidence_matching/model.py:38) builds
            # a delivery for LM i only if votes_per_lm[i] is not None -- the
            # RECEIVER's own pose is needed to transform incoming votes into its
            # frame. So every module must supply its pose every phase, even when
            # it is not one of this phase's speakers.
            #
            # A first version set non-speakers to None. `_combine_votes` then
            # produced an empty delivery for every module and NO evidence moved
            # in any phase -- the P9 failure in a new costume, caught by the
            # liveness probe before the sweep rather than after.
            #
            # `speaking` is therefore what this phase ARGUES; every module still
            # participates as a listener.
            # Speakers are polled FIRST and one at a time, so in sequential
            # mode a later speaker reads the evidence earlier speakers caused.
            # Polling everyone upfront would destroy exactly that property --
            # the gate catches it.
            votes_per_lm = [None] * len(self.learning_modules)
            silent = 0
            for i in group:
                lm = self.learning_modules[i]
                v = self._runner_up_vote(lm) if oppose else lm.send_out_vote()
                if v is None:
                    silent += 1
                votes_per_lm[i] = v

            # Then every non-speaker supplies its pose so it can RECEIVE.
            for i, lm in enumerate(self.learning_modules):
                if votes_per_lm[i] is None:
                    votes_per_lm[i] = lm.send_out_vote()

            # Non-speakers listen but do not argue. `_combine_votes` reads
            # votes_per_lm[j]["possible_states"] from senders and
            # votes_per_lm[i]["sensed_pose_rel_body"] from the receiver, so a
            # listener keeps its pose and empties its argued states.
            for i in range(len(self.learning_modules)):
                if i not in group and isinstance(votes_per_lm[i], dict):
                    v = dict(votes_per_lm[i])
                    v["possible_states"] = {}
                    votes_per_lm[i] = v

            self.phase_stats.append(
                (phase_ix, len(group) - silent, silent, oppose)
            )

            combined_votes = self._combine_votes(votes_per_lm)
            for i, lm in enumerate(self.learning_modules):
                self.send_vote_to_lm(lm, i, combined_votes)
                self.update_stats_after_vote(lm)

    def _vote(self) -> None:
        if self.lm_to_lm_vote_matrix is not None:
            for ix, lm_ids in enumerate(self.phases):
                ids = [i for i in lm_ids if i < len(self.learning_modules)]
                if ids:
                    self._run_phase(ix, ids, ix in self.opposing_phases)

        for lm in self.learning_modules:
            pm = (
                lm.get_possible_matches()
                if lm.buffer.get_num_observations_on_object()
                else []
            )
            logger.info(f"Possible matches for {lm.learning_module_id}: {pm}")

    def phase_summary(self) -> dict:
        """send_none% per phase -- mandatory alongside any accuracy number."""
        out = {}
        for ix in range(len(self.phases)):
            rows = [s for s in self.phase_stats if s[0] == ix]
            if not rows:
                continue
            total = sum(v + s for _, v, s, _ in rows)
            silent = sum(s for _, _, s, _ in rows)
            out[f"phase_{ix + 1}_send_none_pct"] = (
                100.0 * silent / total if total else 0.0
            )
            out[f"phase_{ix + 1}_opposing"] = rows[0][3]
        return out
